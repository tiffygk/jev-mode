#!/usr/bin/env python3
"""Compare TypeSafe's llms.txt page list with the library. Writes NEW_PAGES.txt (empty when nothing changed),
which the prompt-reminder hook shows on the next Jev message. Run weekly (launchd) or by hand; network: one fetch."""
import json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA
ROOT = DATA
OUT = os.path.join(ROOT, "NEW_PAGES.txt")


def have():
    s = set()
    for sub in ("docs", "cookbooks", "patterns"):
        for f in (os.listdir(os.path.join(ROOT, sub)) if os.path.isdir(os.path.join(ROOT, sub)) else []):
            if f.endswith(".md"):
                s.add(f[:-3].replace("__", "/") if sub == "docs" else f"{sub}/{f[:-3]}")
    return s


def main():
    try:
        txt = urllib.request.urlopen("https://docs.typesafe.ai/llms.txt", timeout=20).read().decode()
    except Exception as e:
        print(f"check_new: could not fetch llms.txt ({e}); nothing written"); return 0
    live = set(re.findall(r"https://docs\.typesafe\.ai/([^)\s]+?)\.md", txt))
    lib = have()
    new = sorted(live - lib)
    gone = sorted(lib - live)
    lines = []
    if new:
        lines.append(f"TypeSafe added {len(new)} page(s) since the last refresh: {', '.join(new)}. "
                     "Run `bash ~/.claude/skills/jev-sources/refresh.sh --fetch`, then propose topics.json entries for them.")
    if gone:
        lines.append(f"{len(gone)} library page(s) are no longer listed by TypeSafe: {', '.join(gone[:10])}.")
    os.makedirs(ROOT, exist_ok=True)
    open(OUT, "w").write("\n".join(lines))
    print("\n".join(lines) or "check_new: library matches llms.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
