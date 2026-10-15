#!/usr/bin/env python3
"""Route a Jev question to the source sections to read, and how deeply.

  python3 scripts/route.py "can I put 30 passages in one call?"
  ... --json   machine-readable

Ranks sections with BM25 over the section index, after expanding the question with
synonyms.json. Reference and pattern pages rank above cookbook examples; SDK pages rank
last unless the question is about code. At most 2 sections per file, 6 in all. Each gets
a depth: READ FULL (the question limits a design, or the section is small) or EXTRACT.
Definitions of any primitive named in the question are added as READ FULL.
When the semantic index is on (semantic.py), the keyword list stays as it is and up to SEM_ADD
sections that match by meaning are appended; JEV_SEMANTIC=off, or a missing model or index,
leaves the keyword list alone.
"""
import json, math, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE as CODE_DIR, DATA, SCRIPTS, REFRESH
import usage_log
import applicability
try:
    import semantic
except ImportError:  # numpy missing: BM25 alone
    semantic = None
ROOT = DATA
CONSTRAINT = re.compile(r"\b(must|require[sd]?|only|can'?t|cannot|one call|per request|per call|limit|allowed|wrong|correct|need to|have to)\b", re.I)
CODE = re.compile(r"\b(sdk|python|javascript|typescript|client|method|install|import|async|http|api)\b", re.I)
FULL_UNDER = 2500
BOOST = {"reference": 1.35, "pattern": 1.3, "example": 1.0, "vendor": 0.9, "other": 0.6, "sdk": 0.35}
DEFS = {"noul": "docs/primitives__noul.md", "choice": "docs/primitives__choice.md",
        "score": "docs/primitives__score.md", "state": "docs/concepts__state.md",
        "confidence": "docs/confidence.md"}
SEM_ADD, SEM_FLOOR = 2, 0.35  # sections appended by meaning; least similarity to append one
STOP = set("a an the of to in on for is are be it i we you can do does how what should with and or this that my our".split())


def toks(s):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-/]*", s.lower()) if t not in STOP]


def load():
    try:
        rows = [json.loads(l) for l in open(os.path.join(ROOT, "sections.jsonl"))]
    except FileNotFoundError:
        sys.exit(f"no section found: the library index is missing; run {REFRESH}")
    texts = {}
    if not rows:
        sys.exit(f"no section found: the library index is empty; run {REFRESH}")
    keep, missing = [], set()
    for r in rows:
        try:
            lines = open(os.path.join(ROOT, r["path"]), encoding="utf-8").read().split("\n")
        except FileNotFoundError:
            missing.add(r["path"]); continue
        keep.append(r)
        body = "\n".join(lines[r["line_start"] - 1:r["line_end"]])
        texts[r["id"]] = toks(r["heading"] + " " + r["heading"] + " " + body)  # heading counts double
    for p in sorted(missing):
        print(f"missing source {p}; run {REFRESH}", file=sys.stderr)
    return keep, texts


def expand(q):
    syn = json.load(open(os.path.join(CODE_DIR, "synonyms.json")))
    base = toks(q)
    extra = []
    for t in base:
        for k in (t, t.rstrip("s")):
            for x in syn.get(k, []):
                extra += toks(x)
    return base, extra


def bm25(rows, texts, base, extra, k1=1.4, b=0.75):
    N = len(rows)
    df = Counter(t for r in rows for t in set(texts[r["id"]]))
    avg = sum(len(texts[r["id"]]) for r in rows) / N
    q = Counter(base) + Counter({t: 0.4 for t in extra})  # synonyms count less than the user's words
    out = {}
    for r in rows:
        tf = Counter(texts[r["id"]]); dl = len(texts[r["id"]]); s = 0.0
        for t, w in q.items():
            if tf[t]:
                idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                s += w * idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avg))
        out[r["id"]] = s
    return out


def route(q, model=None):
    model = model or applicability.find_model(q)
    rows, texts = load()
    base, extra = expand(q)
    scores = bm25(rows, texts, base, extra)
    if os.environ.get("JEV_SEMANTIC") == "off":
        sem, sem_why = None, "off: JEV_SEMANTIC=off"
    elif semantic is None:
        sem, sem_why = None, "off: numpy unavailable"
    else:
        sem, why = semantic.scores(q, rows)
        sem_why = "on" if sem else f"off: {why}"
    if sem and max(scores.values()) == 0:  # no word of the question is in the library: gibberish
        sem, sem_why = None, "off: no keyword match"
    code = bool(CODE.search(q))
    def final(r):
        boost = BOOST[r["kind"]] if not (code and r["kind"] == "sdk") else 1.0
        return scores[r["id"]] * boost
    ranked = sorted((r for r in rows if scores[r["id"]] > 0), key=final, reverse=True)
    picked, per_file = [], Counter()
    for r in ranked:
        if per_file[r["path"]] < 2:
            picked.append(r); per_file[r["path"]] += 1
        if len(picked) == 6:
            break
    # topic map first: the best-scoring section of each mapped page (fix-catalog seeds)
    try:
        topics = json.load(open(os.path.join(CODE_DIR, "topics.json")))["topics"]
    except (json.JSONDecodeError, KeyError) as e:
        sys.exit(f"topics.json is malformed ({e}); fix it before routing (refresh does not rebuild it)")
    by_name = {t["name"]: t for t in topics}
    for t in topics:  # a topic may share another topic's regex ("match_of": its name)
        src = by_name[t["match_of"]] if "match_of" in t else t
        t.setdefault("match", src["match"] if "match" in src else "(?!)")
        t.setdefault("density", src.get("density", t["match"]))
    hit = [t for t in topics if re.search(r"\b(?:" + t["match"] + ")", q, re.I)]
    mapped = []
    for t in hit:
        for p in t["paths"]:
            if "#" in p:  # a named section: path#heading
                path, head = p.split("#", 1)
                r = next((x for x in rows if x["path"] == path and x["heading"] == head), None)
                if r and r["id"] not in {m["id"] for m in mapped}:
                    mapped.append(r)
                continue
            if p in {r["path"] for r in mapped}:
                continue
            cands = sorted((r for r in rows if r["path"] == p), key=lambda r: (-scores[r["id"]], r["line_start"]))
            if t.get("top"):  # a long unheaded page (a blog capture): the sections densest in the topic's own words
                rx = re.compile(r"\b(?:" + t["density"] + ")", re.I)
                dens = {r["id"]: len(rx.findall(" ".join(texts[r["id"]]))) for r in cands}
                cands = sorted(cands, key=lambda r: (-dens[r["id"]], -scores[r["id"]], r["line_start"]))
                cands = [r for r in cands if dens[r["id"]] > 0]
            for r in cands[:t.get("top", 1)]:
                if r["id"] not in {m["id"] for m in mapped}:
                    mapped.append(r)
    picked = mapped + [r for r in picked if r["id"] not in {m["id"] for m in mapped}][:max(0, 8 - len(mapped))]
    picked = picked[:10]
    if sem:  # meaning complements the keyword list: append only, never reorder or drop
        have, per_file = {r["id"] for r in picked}, Counter(r["path"] for r in picked)
        added = []
        for r in sorted(rows, key=lambda r: (-sem[r["id"]], r["id"])):
            if len(added) == SEM_ADD or sem[r["id"]] < SEM_FLOOR:
                break
            if r["id"] not in have and per_file[r["path"]] < 2 and (r["kind"] != "sdk" or code):
                added.append(r); per_file[r["path"]] += 1
        picked += added
    n_keyword = len(picked) - (len(added) if sem else 0)
    constraint = bool(CONSTRAINT.search(q))
    secs = [dict(id=r["id"], path=r["path"], heading=r["heading"], kind=r["kind"], tokens=r["tokens"],
                 depth="READ FULL" if constraint or (k < n_keyword and r["tokens"] < FULL_UNDER) else "EXTRACT",
                 by="keyword" if k < n_keyword else "meaning")
            for k, r in enumerate(picked)]  # a section matched only by meaning is a pointer, not a mandatory read
    named = {p for w, p in DEFS.items() if re.search(rf"\b{w}s?\b", q, re.I)}
    defs = []
    for p in sorted(named):
        r = next((x for x in rows if x["path"] == p), None)
        if not r or r["id"] in {x["id"] for x in secs[:n_keyword]}:
            continue
        defs.append(dict(id=r["id"], path=p, heading=r["heading"], kind=r["kind"], tokens=r["tokens"], depth="READ FULL", by="keyword"))
    secs = [x for k, x in enumerate(secs) if k < n_keyword or x["id"] not in {d["id"] for d in defs}]
    for x in secs + defs:  # which model a section needs, and whether TypeSafe calls it not production-ready
        a = applicability.lookup(x["path"], x["heading"])
        base = model or applicability.ALIASES["jev-latest"]  # NEEDS marks a model newer than the one in use (jev-latest when none is named)
        x["needs"], x["status"], x["note"] = (a["needs"] if not applicability.allowed(a, base) else None), a["status"], a["note"]
    if model:  # a section the model can't run is still listed, after every section that applies
        secs = sorted(secs, key=lambda x: not applicability.allowed(x, model))
        defs = sorted(defs, key=lambda x: not applicability.allowed(x, model))
    return {"question": q, "model": model, "topics": [t["name"] for t in hit], "constraint": constraint, "sections": secs, "definitions": defs,
            "semantic": sem_why, "n_keyword": n_keyword}


def main():
    args, model = [a for a in sys.argv[1:] if a != "--json"], None
    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1] if i + 1 < len(args) and not args[i + 1].startswith("--") else None
        args = args[:i] + args[i + (2 if model else 1):]
        if model is None:
            print("warning: --model needs a value such as jev-1.13.0; routing with no model", file=sys.stderr)
        else:
            model = applicability.checked(model)
    if not args:
        sys.exit('usage: route.py [--json] [--model <jev-model>] "<question>"')
    res = route(" ".join(args), model=model)
    usage_log.write("route", question=res["question"], constraint=res["constraint"], topics=res["topics"], semantic=res["semantic"], cwd=os.getcwd(),
                    sections=[{"id": s["id"], "depth": s["depth"], "kind": s["kind"], "by": s["by"]}
                              for s in res["sections"]],
                    definitions=[{"id": d["id"], "depth": d["depth"], "kind": d["kind"]} for d in res["definitions"]])
    if "refresh.sh" in res["semantic"] or "unavailable" in res["semantic"]:  # something to fix
        print(f"semantic routing {res['semantic']}", file=sys.stderr)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1)); return
    if not res["sections"] and not res["definitions"]:
        print(f"no section found; refresh the library ({REFRESH}) or read the indexes")
        print(semantic_line(res)); return
    label = {"reference": "reference rule", "pattern": "pattern", "example": "cookbook example", "sdk": "sdk reference", "vendor": "vendor claim", "other": "other"}
    print(f"Question: {res['question']}" + ("  [limits a design: read in full]" if res["constraint"] else ""))
    if res["topics"]:
        print("Topics matched: " + "; ".join(res["topics"]))
    items = res["sections"] + res["definitions"]
    if res["model"]:  # sections the model can't run come last, after the definitions too
        items = sorted(items, key=lambda x: not applicability.allowed(x, res["model"]))
        print(f"Model: {res['model']}")
    for s in items:
        print(f"{s['depth']:9} | {label[s['kind']]:16} | {s['path']}#{s['heading']} | {s['tokens']} tok{marks(s)}\n"
              f"          python3 {SCRIPTS}/read.py '{s['id']}'")
    print("READ FULL items: read every one with read.py before any claim. EXTRACT items: claims from them are unverified until read in full.")
    print(semantic_line(res))


def marks(s):
    out = f" | NEEDS {s['needs']}" if s.get("needs") else ""
    if s.get("status") == "experimental":
        out += " | EXPERIMENTAL: " + (s.get("note") or "TypeSafe says not production-ready")
    elif s.get("status") == "part-experimental":
        out += " | PART EXPERIMENTAL: " + (s.get("note") or "TypeSafe says image support is not production-ready")
    return out


def semantic_line(res):
    return "semantic: on" if res["semantic"] == "on" else f"semantic: off ({res['semantic'][5:]})"


if __name__ == "__main__":
    main()
