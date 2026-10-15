#!/usr/bin/env python3
"""After a refresh: do the stored test questions still route to their sections? Runs each question on keywords
alone and with meaning-matching, and prints the misses. Always exits 0; check_new.py relays the summary."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE
import route as R

BAR = 0.80  # for paraphrases.json; every release_questions.json question must hit as READ FULL, and carry the label its "expect" names
SETS = {"paraphrases.json": False, "release_questions.json": True}  # name -> strict
QDIR = os.environ.get("JEV_ROUTE_QUESTIONS") or os.path.join(CODE, "tests")  # tests point this at a temp set


def questions():
    out = []
    for name, strict in SETS.items():
        p = os.path.join(QDIR, name)
        if os.path.exists(p):
            out += [dict(q, strict=strict) for q in json.load(open(p))]
    return out


def expected(s, q):
    """A question may carry "expect": "needs-newer" (the section must come back labeled NEEDS, because the question's
    model is too old for it) or "experimental" (labeled experimental and not NEEDS)."""
    want = q.get("expect")
    if want == "needs-newer":
        return bool(s.get("needs"))
    if want == "experimental":
        return s.get("status") == "experimental" and not s.get("needs")
    return True


def hit(res, q):
    return any(s["heading"] == q["heading"] and (not q.get("path") or s["path"] == q["path"])
               and (not q.get("strict") or s["depth"] == "READ FULL") and expected(s, q) for s in res["sections"])


def run():
    qs, sem, rep = questions(), R.semantic, {}
    try:
        for mode in ("keywords", "meaning"):
            R.semantic = None if mode == "keywords" else sem
            miss = [q for q in qs if not hit(R.route(q["q"], model=q.get("model")), q)]
            loose = [q for q in qs if not q["strict"]]
            rep[mode] = {"hits": len(loose) - sum(not m["strict"] for m in miss), "total": len(loose),
                         "strict_misses": [f"{m['heading']} <- {m['q'][:70]}" for m in miss if m["strict"]],
                         "misses": [f"{m['heading']} <- {m['q'][:70]}" for m in miss if not m["strict"]]}
    finally:
        R.semantic = sem
    return rep


def summary(rep):
    m, k = rep["meaning"], rep["keywords"]
    line = f"Routing check after the refresh: {m['hits']}/{m['total']} paraphrase questions find their section ({k['hits']} on keywords alone)"
    if m["total"] and m["hits"] < BAR * m["total"]:
        line += f", below the {int(BAR * 100)}% bar"
    if m["strict_misses"]:
        line += f"; {len(m['strict_misses'])} release questions missed: " + "; ".join(m["strict_misses"][:5])
    if m["misses"]:
        line += ". Paraphrase misses: " + "; ".join(m["misses"][:5])
    return line + "."


if __name__ == "__main__":
    print(summary(run()))
