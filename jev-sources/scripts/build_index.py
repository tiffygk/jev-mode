#!/usr/bin/env python3
"""Build sections.jsonl: one row per heading across docs/, cookbooks/ and patterns/.

Each row: id, path, heading, level, line_start, line_end (1-based, inclusive), kind,
tokens (chars/4), caveats (scope notes inside the section), file_caveats (scope notes
anywhere in the file; a cookbook's "for clarity" note often sits in a later section
than the one it scopes), captions (diagram captions, image alt text).
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA
ROOT = DATA
CAVEAT = re.compile(r"this walkthrough|for clarity|a real application|in a real (app|system)|in practice|"
                    r"for simplicity|to keep (it|this|the example) simple|note:|caveat|not (a|an) (rule|requirement)",
                    re.I)
CAPTION = re.compile(r"^\s*(!\[[^\]]*\]|<figcaption>|caption=|\*Figure|_Figure)", re.I)
SKIP = ("docs/cookbooks__", "docs/patterns__")  # MDX duplicates of cookbooks/ and patterns/


def kind_of(path):
    if path.startswith("cookbooks/"):
        return "example"
    if path.startswith("patterns/"):
        return "pattern"
    name = path[len("docs/"):]
    if name.startswith("sdk"):
        return "sdk"
    if name.startswith(("demos", "legal")):
        return "other"
    return "reference"


def paragraphs_matching(lines, rx):
    out, buf = [], []
    for ln in lines + [""]:
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            para = " ".join(buf)
            if rx.search(para):
                out.append(para[:600])
            buf = []
    return out


def sections(path):
    lines = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
    heads, fence = [], False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        m = re.match(r"^(#{1,4})\s+(.+?)\s*$", ln)
        if m and not fence and not ln.startswith(">"):
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    if not heads:
        heads = [(0, 1, os.path.basename(path))]
    file_cav = paragraphs_matching([l for l in lines if not l.startswith(">")], CAVEAT)
    rows = []
    for n, (i, lvl, h) in enumerate(heads):
        end = heads[n + 1][0] - 1 if n + 1 < len(heads) else len(lines) - 1
        body = lines[i:end + 1]
        text = "\n".join(body)
        rows.append({
            "id": f"{path[:-3]}#{n}", "path": path, "heading": h, "level": lvl,
            "line_start": i + 1, "line_end": end + 1, "kind": kind_of(path),
            "tokens": len(text) // 4,
            "caveats": paragraphs_matching(body, CAVEAT),
            "file_caveats": file_cav,
            "captions": [l.strip()[:200] for l in body if CAPTION.match(l)],
        })
    return rows


def main():
    out = []
    for sub in ("docs", "cookbooks", "patterns"):
        for f in sorted((os.listdir(os.path.join(ROOT, sub)) if os.path.isdir(os.path.join(ROOT, sub)) else [])):
            p = f"{sub}/{f}"
            if f.endswith(".md") and not p.startswith(SKIP):
                out += sections(p)
    if not out:
        sys.exit(f"no pages in {ROOT}; run bash ~/.claude/skills/jev-sources/refresh.sh --fetch")
    with open(os.path.join(ROOT, "sections.jsonl"), "w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(out)} sections from {len({r['path'] for r in out})} files")


if __name__ == "__main__":
    main()
