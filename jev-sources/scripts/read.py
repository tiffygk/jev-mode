#!/usr/bin/env python3
"""Print one source section in full, with the file's scope caveats and captions.

  python3 ~/.claude/skills/jev-sources/scripts/read.py 'cookbooks/rerank_typesafe#7'
  ... --extract "<terms>"   12 lines around each hit, capped at 1,500 tokens (marked as an extract)

The first line is the citation to quote: SOURCE: <path>#<heading> | KIND | READ.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA
ROOT = DATA
LABEL = {"reference": "reference rule", "pattern": "pattern", "example": "cookbook example", "sdk": "sdk reference", "other": "other"}


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: read.py <section id> [--extract terms]")
    sid = sys.argv[1]
    try:
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "sections.jsonl"))]
    except FileNotFoundError:
        sys.exit("library index missing; run bash ~/.claude/skills/jev-sources/refresh.sh --fetch")
    r = next((x for x in rows if x["id"] == sid), None)
    if not r:
        sys.exit(f"no section {sid!r}; run route.py to get ids")
    if not os.path.exists(os.path.join(ROOT, r["path"])):
        sys.exit(f"missing source {r['path']}; run bash ~/.claude/skills/jev-sources/refresh.sh --fetch")
    lines = open(os.path.join(ROOT, r["path"]), encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]]
    extract = "--extract" in sys.argv
    if extract:
        terms = [t.lower() for t in sys.argv[sys.argv.index("--extract") + 1:]]
        keep = set()
        for i, ln in enumerate(lines):
            if any(t in ln.lower() for t in terms):
                keep.update(range(max(0, i - 6), min(len(lines), i + 6)))
        body = "\n".join(lines[i] for i in sorted(keep))[:6000]
    else:
        body = "\n".join(lines)
    print(f"SOURCE: {r['path']}#{r['heading']} | KIND: {LABEL[r['kind']]} | READ: {'extract, not a full read' if extract else 'full'}")
    print(f"(lines {r['line_start']}-{r['line_end']}, ~{r['tokens']} tokens)\n")
    print(body)
    cav = [c for c in r["file_caveats"] if c not in "\n".join(lines)]
    if cav:
        print("\n--- Scope notes elsewhere in this file (they may limit what this section shows) ---")
        for c in cav:
            print("- " + c)
    if r["captions"]:
        print("\n--- Captions (diagram labels, not rules) ---")
        for c in r["captions"]:
            print("- " + c)


if __name__ == "__main__":
    main()
