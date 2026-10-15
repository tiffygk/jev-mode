#!/usr/bin/env python3
"""One call for a Jev question: route it (in your words, and in the docs' words when given), read every READ FULL
section in reading order up to a token cap, and print one bundle with a citation line per section. Sections past the
cap are listed with their read.py commands, never dropped.
  jev.py "<question>" [--docs-words "<question in the docs' words>"] [--model jev-1.13.0] [--cap 12000] [--json]"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route as R
import read as RD
import usage_log
import applicability
from paths import CODE

ORDER = {"reference": 0, "pattern": 1, "sdk": 2, "example": 3, "vendor": 4, "other": 5}


def bundle(questions, model=None, cap=12000):
    seen, sem = {}, "off"
    model = model or applicability.find_model(" ".join(questions))  # found once, from every phrasing; the oldest wins
    used_model = model
    for q in questions:
        res = R.route(q, model=model)
        sem = res["semantic"]
        usage_log.write("route", question=q, model=model, via="jev.py", semantic=res["semantic"],
                        sections=[{"id": s["id"], "depth": s["depth"], "kind": s["kind"], "by": s.get("by")} for s in res["sections"]],
                        definitions=[{"id": d["id"], "depth": "READ FULL", "kind": d["kind"]} for d in res.get("definitions", [])])
        defs = [dict(s, depth="READ FULL") for s in res.get("definitions", [])]  # route.py prints these as READ FULL
        for d in res["sections"] + defs:
            if d["id"] not in seen or (d["depth"] == "READ FULL" and seen[d["id"]]["depth"] != "READ FULL"):
                seen[d["id"]] = d  # the deeper depth wins when two phrasings disagree
    full = [s for s in seen.values() if s["depth"] == "READ FULL"]
    extract = [s for s in seen.values() if s["depth"] != "READ FULL"]
    # a section the model in use is too old for goes after every applicable one, then by kind; with no model, none is demoted
    def too_new(s):
        return bool(s.get("needs_newer")) or (used_model is not None and not applicability.allowed(s, used_model))
    full.sort(key=lambda s: (too_new(s), ORDER.get(s["kind"], 9)))
    read, read_ids, not_read, used = [], [], [], 0
    for s in full:
        if read and used + s["tokens"] > cap:
            not_read.append(s)
            continue
        first, rest = RD.render(s["id"]).split("\n", 1)
        read.append(first + R.marks(s) + "\n" + rest)  # CITE AS line plus any NEEDS / EXPERIMENTAL label
        read_ids.append(s["id"])
        usage_log.write("read", id=s["id"], extract=False, tokens=s["tokens"], via="jev.py")
        used += s["tokens"]
    return {"read": read, "read_ids": read_ids, "not_read": not_read, "extract": extract, "semantic": sem}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--docs-words")
    ap.add_argument("--model")
    ap.add_argument("--cap", type=int, default=12000)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    qs = [a.question] + ([a.docs_words] if a.docs_words else [])
    model = applicability.checked(a.model)
    b = bundle(qs, model, a.cap)
    usage_log.write("jev", questions=qs, model=model, cap=a.cap, read=b["read_ids"],
                    not_read=[s["id"] for s in b["not_read"]], extract=[s["id"] for s in b["extract"]])
    if a.json:
        print(json.dumps({**b, "not_read": [s["id"] for s in b["not_read"]], "extract": [s["id"] for s in b["extract"]]}, indent=1))
        return 0
    print("\n\n".join(b["read"]) or "no section found; route in other words or refresh")
    rd = f"python3 {os.path.join(CODE, 'scripts', 'read.py')}"
    for s in b["not_read"]:
        print(f"NOT YET READ (over the cap): {rd} '{s['id']}'  # {s['path']}#{s['heading']}")
    for s in b["extract"]:
        print(f"EXTRACT (claims from it are unverified until read in full): {rd} '{s['id']}'")
    print(f"semantic: {b['semantic']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
