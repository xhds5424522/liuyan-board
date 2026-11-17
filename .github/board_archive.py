#!/usr/bin/env python3
"""把公开中继里最近 12 小时的留言并进 messages.json，按时间去重。"""
import json
import sys
import urllib.request

TOPIC = "jidu-lyb-7h4k9vq2xw"
NTFY = "https://ntfy.sh/%s/json?poll=1&since=all" % TOPIC
FILE = "messages.json"
KEEP = 500
MAX = 60


def pull():
    req = urllib.request.Request(NTFY, headers={"User-Agent": "board-archive"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def main():
    try:
        with open(FILE, encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        old = []
    if not isinstance(old, list):
        old = []

    try:
        raw = pull()
    except Exception as e:
        print("拉取中继失败：%s" % e)
        return 0

    incoming = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if not isinstance(ev, dict) or ev.get("event") != "message":
            continue
        try:
            m = json.loads(ev.get("message") or "")
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        text = str(m.get("t") or "").strip()[:300]
        if not text:
            continue
        name = str(m.get("n") or "匿名").strip()[:16] or "匿名"
        try:
            c = int(m.get("c") or 0)
        except Exception:
            c = 0
        if not c:
            try:
                c = int(ev.get("time") or 0) * 1000
            except Exception:
                c = 0
        if not c:
            continue
        incoming.append({"n": name, "t": text, "c": c})

    def key(x):
        return (x.get("n", ""), x.get("c", 0), x.get("t", ""))

    seen = {}
    for x in old:
        if isinstance(x, dict) and x.get("t"):
            seen[key(x)] = x

    added = 0
    for x in incoming[:MAX]:
        k = key(x)
        if k not in seen:
            seen[k] = x
            added += 1

    if not added:
        print("没有新留言")
        return 0

    out = sorted(seen.values(), key=lambda x: int(x.get("c") or 0), reverse=True)[:KEEP]
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("归档 %d 条，共 %d 条" % (added, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
