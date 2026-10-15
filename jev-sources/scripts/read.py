#!/usr/bin/env python3
"""Print one source section in full, with the file's scope caveats and captions.

  python3 scripts/read.py 'cookbooks/rerank_typesafe#7'
  ... --extract "<terms>"   12 lines around each hit, capped at 1,500 tokens (marked as an extract)

The first line is the citation to quote: SOURCE: <path>#<heading> | KIND | READ.
A section with a model or readiness limit gets a second line: APPLIES: needs <model> | experimental (<source>).
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA, REFRESH
import usage_log
import applicability
ROOT = DATA
LABEL = {"reference": "reference rule", "pattern": "pattern", "example": "cookbook example", "sdk": "sdk reference",
         "vendor": "vendor claim", "other": "other"}
EXAMPLE_NOTE = ("EXAMPLE: one build TypeSafe published. Its layout, call counts and diagrams are not API limits; "
                "check the scope notes below and the reference rules.")


def _row(sid):
    try:
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "sections.jsonl"))]
    except FileNotFoundError:
        sys.exit(f"library index missing; run {REFRESH}")
    r = next((x for x in rows if x["id"] == sid), None)
    if not r:
        sys.exit(f"no section {sid!r}; run route.py to get ids")
    if not os.path.exists(os.path.join(ROOT, r["path"])):
        sys.exit(f"missing source {r['path']}; run {REFRESH}")
    return r


def render(sid, extract_terms=None):
    """The section as text. The first line is CITE AS: <path>#<heading> (<label>); from the second line on it is
    what read.py prints. extract_terms (a list) gives an extract instead of the full section. Does not log."""
    r = _row(sid)
    lines = open(os.path.join(ROOT, r["path"]), encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]]
    extract = extract_terms is not None
    if extract:
        terms = [t.lower() for t in extract_terms]
        keep = set()
        for i, ln in enumerate(lines):
            if any(t in ln.lower() for t in terms):
                keep.update(range(max(0, i - 6), min(len(lines), i + 6)))
        body = "\n".join(lines[i] for i in sorted(keep))[:6000]
    else:
        body = "\n".join(lines)
    label = LABEL[r["kind"]]
    out = [f"CITE AS: {r['path']}#{r['heading']} ({label})",
           f"SOURCE: {r['path']}#{r['heading']} | KIND: {label} | READ: {'extract, not a full read' if extract else 'full'}"]
    if r["kind"] == "example":
        out.append(EXAMPLE_NOTE)
    ap = applicability.lookup(r["path"], r["heading"])
    if ap["needs"] or ap["status"]:
        out.append("APPLIES: " + " | ".join(([f"needs {ap['needs']}"] if ap["needs"] else []) + ([ap["status"].replace("-", " ")] if ap["status"] else [])) + f" ({ap['source']})")
    out.append(f"(lines {r['line_start']}-{r['line_end']}, ~{r['tokens']} tokens)\n")
    out.append(body)
    cav = [c for c in r["file_caveats"] if c not in "\n".join(lines)]
    if cav:
        out.append("\n--- Scope notes elsewhere in this file (they may limit what this section shows) ---")
        out += ["- " + c for c in cav]
    if r["captions"]:
        out.append("\n--- Captions (diagram labels, not rules) ---")
        out += ["- " + c for c in r["captions"]]
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: read.py <section id> [--extract terms]")
    sid = sys.argv[1]
    terms = sys.argv[sys.argv.index("--extract") + 1:] if "--extract" in sys.argv else None
    text = render(sid, terms)
    print(text.split("\n", 1)[1])  # the CITE AS line is for jev.py's bundle; this command's output starts at SOURCE
    usage_log.write("read", id=sid, extract=terms is not None, tokens=_row(sid)["tokens"])


if __name__ == "__main__":
    main()
