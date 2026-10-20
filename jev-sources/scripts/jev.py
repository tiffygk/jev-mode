#!/usr/bin/env python3
"""One call for a Jev question: route it (in your words, and in the docs' words when given), read every READ FULL
section in reading order up to a token cap, and print one bundle with a citation line per section. Sections past the
cap are listed with their read.py commands, never dropped.
  jev.py "<question>" [--docs-words "<question in the docs' words>"] [--model jev-1.13.0] [--cap 12000] [--json]
  jev.py "<q1>" --also "<q2>" [--also ...]   several questions, one shared cap, a COVERAGE block (at most 8 questions)
  jev.py --map "<goal>"                        an outline of the pages and sections that may answer a broad goal; reads nothing"""
import argparse, datetime, hashlib, json, os, shlex, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import route as R
import read as RD
import usage_log
import applicability
import paths
from paths import CODE, REFRESH
import clean

CAP = 12000
ORDER = {"reference": 0, "pattern": 1, "sdk": 2, "example": 3, "vendor": 4, "other": 5}
MAX_QUESTIONS = 8   # sub-questions in one call
MAX_BATCHES = 6     # reading-plan batches; past that the goal is too broad
MAP_TOKENS = 1500   # outline size, counted as characters / 4
LABEL = {"reference": "reference rule", "pattern": "pattern", "example": "cookbook example", "sdk": "sdk reference",
         "vendor": "vendor claim", "other": "other"}
NEXT = 'Next: run jev.py with one question per topic you need: jev.py "<q1>" --also "<q2>" ...'


def reading_plan(not_read, cap):
    """Batches of unread sections in reading order; each fits the cap, and a section over the cap stands alone.
    A page whose unread sections fit under the cap together moves as one unit, placed where its first section is."""
    pages = {}
    for s in not_read:
        pages.setdefault(s.get("path", s["id"]), []).append(s)
    units, placed = [], set()
    for s in not_read:
        page = s.get("path", s["id"])
        group = pages[page]
        if len(group) > 1 and sum(g["tokens"] for g in group) <= cap:
            if page not in placed:
                placed.add(page)
                units.append(group)
        else:
            units.append([s])
    batches, cur, used = [], [], 0
    for unit in units:
        t = sum(s["tokens"] for s in unit)
        if cur and used + t > cap:
            batches.append(cur)
            cur, used = [], 0
        cur += unit
        used += t
    if cur:
        batches.append(cur)
    return batches


def save_plan(qs, batches):
    """Write <data>/plans/<plan_id>.json (folder owner-only, file written atomically) and return the plan id. The file is
    what check_findings.py reads, so JEV_LOG=off does not stop it."""
    created = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    plan_id = "p" + hashlib.sha256((json.dumps(qs) + created + str(os.getpid())).encode()).hexdigest()[:8]
    d = os.path.join(paths.DATA, "plans")
    os.makedirs(d, mode=0o700, exist_ok=True)
    os.chmod(d, 0o700)  # a folder made earlier with looser permissions is tightened
    plan = {"plan_id": plan_id, "created": created, "goal": list(qs),
            "batches": [{"n": n, "ids": [s["id"] for s in b], "tokens": sum(s["tokens"] for s in b)} for n, b in enumerate(batches, 1)]}
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")  # mkstemp makes the file 0600
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(plan, f, indent=1)
        os.replace(tmp, os.path.join(d, plan_id + ".json"))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return plan_id


READER_SOURCES = ("JEV-SOURCES: your reading for this goal is the read.py commands below, already routed; run them and "
                  "no other search (no jev.py or route.py), and quote only from those sections.")
# The reader brief carries the JEV-SOURCES marker the dispatch hook looks for, but not SKILL.md's routing line: a reader
# told to run jev.py routes its own goal again and reads far past its batch (a live test, 2026-10-19).


def reader_block(plan_id, n, batch, qs):
    rd = f"python3 {os.path.join(CODE, 'scripts', 'read.py')}"
    return "\n".join([
        f"----- READER BRIEF plan {plan_id} batch {n} -----",
        f"JEV-READER: plan {plan_id} batch {n}",
        READER_SOURCES,
        "GOAL: " + " | ".join(qs),
        "Read these sections in full, in order:",
        *[f"  {rd} {shlex.quote(s['id'])}   # {s['path']}#{s['heading']}" for s in batch],
        "Return only lines of this form, at most 12, with no page text:",
        'FINDING: <one sentence> | CITE AS: <path#heading (label)> | QUOTE: "<exact words>"',
        "Start your reply with the JEV-READER line above.",
        "----- END READER BRIEF -----"])


def bundle(questions, model=None, cap=CAP, log=True, coverage=True):
    """questions: strings, or a list of phrasings of one question (a question and its docs-words phrasing). One cap and one
    dedupe cover them all; coverage says, per question, which READ FULL sections it reached and where each one went."""
    groups = [[q] if isinstance(q, str) else list(q) for q in questions]
    flat = [p for g in groups for p in g]
    seen, sem, reached = {}, "off", [[] for _ in groups]
    model = model or applicability.find_model(" ".join(flat))  # found once, from every phrasing; the oldest wins
    used_model = model
    for gi, g in enumerate(groups):
        for q in g:
            res = R.route(q, model=model)
            sem = res["semantic"]
            if log:
                usage_log.write("route", question=q, model=model, via="jev.py", semantic=res["semantic"],
                                sections=[{"id": s["id"], "depth": s["depth"], "kind": s["kind"], "by": s.get("by")} for s in res["sections"]],
                                definitions=[{"id": d["id"], "depth": "READ FULL", "kind": d["kind"]} for d in res.get("definitions", [])])
            defs = [dict(s, depth="READ FULL") for s in res.get("definitions", [])]  # route.py prints these as READ FULL
            for d in res["sections"] + defs:
                if d["id"] not in reached[gi]:
                    reached[gi].append(d["id"])
                if d["id"] not in seen or (d["depth"] == "READ FULL" and seen[d["id"]]["depth"] != "READ FULL"):
                    seen[d["id"]] = d  # the deeper depth wins when two phrasings disagree
    full = [s for s in seen.values() if s["depth"] == "READ FULL"]
    extract = [s for s in seen.values() if s["depth"] != "READ FULL"]
    # a section the model in use is too old for goes after every applicable one, then by kind; with no model, none is demoted
    def too_new(s):
        return bool(s.get("needs_newer")) or (used_model is not None and not applicability.allowed(s, used_model))
    full.sort(key=lambda s: (too_new(s), ORDER.get(s["kind"], 9)))
    read, read_ids, read_refs, not_read, notices, used = [], [], [], [], [], 0
    for s in full:
        if read and used + s["tokens"] > cap:
            not_read.append(s)
            continue
        first, rest = RD.render(s["id"]).split("\n", 1)
        read.append(first + R.marks(s) + "\n" + rest)  # CITE AS line plus any NEEDS / EXPERIMENTAL label
        read_ids.append(s["id"])
        read_refs.append(f"{s['path']}#{s['heading']}")
        n = clean.code_shaped(rest.split("\n"))
        if n >= 10:
            notices.append(f"NOTICE: {s['path']}#{s['heading']} looks like site code ({n} code-shaped lines). "
                           f"Run {REFRESH} to re-clean; treat this section as unverified until then.")
        if log:
            usage_log.write("read", id=s["id"], extract=False, tokens=s["tokens"], via="jev.py")
        used += s["tokens"]
    plan, too_broad = [], None
    if sum(s["tokens"] for s in not_read) > cap:
        plan = reading_plan(not_read, cap)
        if len(plan) > MAX_BATCHES:  # no partial plan: the goal is narrowed or split instead
            too_broad = {"batches": len(plan), "tokens": sum(s["tokens"] for s in not_read)}
            plan = []
    out = {"read": read, "read_ids": read_ids, "read_refs": read_refs, "not_read": not_read, "extract": extract,
           "semantic": sem, "plan": [[s["id"] for s in b] for b in plan], "plan_batches": plan, "notices": notices,
           "too_broad": too_broad}
    if coverage:
        rd, nr = set(read_ids), {s["id"] for s in not_read}
        out["coverage"] = [{"q": g[0], "read": [i for i in ids if i in rd], "planned": [i for i in ids if i in nr],
                            "extract": [i for i in ids if seen[i]["depth"] != "READ FULL"]}
                           for g, ids in zip(groups, reached)]
    return out


def map_outline(goal, docs_words=None, budget=MAP_TOKENS, model=None):
    """The pages and sections that may answer a broad goal: path, label, headings and sizes, no section text, nothing logged.
    Pages come in rank order of each page's best section; pages that do not fit the budget (characters / 4) become a count."""
    phrasings = [goal] + ([docs_words] if docs_words else [])
    model = model or applicability.find_model(" ".join(phrasings))
    ranked = []
    for pi, q in enumerate(phrasings):
        res = R.route(q, model=model, limit=30, per_page=3)
        for rank, s in enumerate(res["sections"] + [dict(d, depth="READ FULL") for d in res.get("definitions", [])]):
            ranked.append((rank, pi, s))
    ranked.sort(key=lambda t: (t[0], t[1]))
    pages, ids = {}, set()
    for _, _, s in ranked:
        if s["id"] not in ids:
            ids.add(s["id"])
            pages.setdefault(s["path"], []).append(s)
    if not pages:
        return f"MAP: {goal[:200]}\nno section found; route in other words or refresh\n"
    blocks = []
    for path, secs in pages.items():  # a page's token figure counts only its listed sections, not the whole page
        n = len(secs)
        head = f"{path} ({LABEL.get(secs[0]['kind'], 'other')}, {n} section{'s' if n != 1 else ''}, ~{sum(x['tokens'] for x in secs):,} tokens)"
        blocks.append([head] + [f"  - {x['heading']} (~{x['tokens']:,})" for x in secs])

    def text(kept):
        lines = [f"MAP: {goal[:200]}"] + [l for b in blocks[:kept] for l in b]
        more = len(blocks) - kept
        if more:
            lines.append(f"... and {more} more page{'s' if more != 1 else ''}")
        return "\n".join(lines + [NEXT]) + "\n"
    kept = 1  # at least one page, whatever the budget
    while kept < len(blocks) and len(text(kept + 1)) / 4 <= budget:
        kept += 1
    return text(kept)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="the question, or with --map the goal")
    ap.add_argument("--docs-words")
    ap.add_argument("--also", action="append", default=[], help="another question; repeat up to %d in all" % (MAX_QUESTIONS - 1))
    ap.add_argument("--map", action="store_true", help="print an outline of the pages that may answer the goal; read nothing")
    ap.add_argument("--model")
    ap.add_argument("--cap", type=int, default=CAP)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    model = applicability.checked(a.model)
    if a.map and a.also:
        print("--map takes one goal; run --also without --map", file=sys.stderr)
        return 2
    if a.map:
        print(map_outline(a.question, a.docs_words, MAP_TOKENS, model), end="")
        return 0
    if 1 + len(a.also) > MAX_QUESTIONS:
        print(f"too many sub-questions ({1 + len(a.also)}); split the goal into two runs of at most {MAX_QUESTIONS}", file=sys.stderr)
        return 2
    groups = [[a.question] + ([a.docs_words] if a.docs_words else [])] + [[q] for q in a.also]  # docs-words go with the first only
    qs = [p for g in groups for p in g]
    b = bundle(groups, model, a.cap)
    usage_log.write("jev", questions=qs, model=model, cap=a.cap, read=b["read_ids"],
                    not_read=[s["id"] for s in b["not_read"]], extract=[s["id"] for s in b["extract"]])
    plan_id = save_plan(qs, b["plan_batches"]) if b["plan_batches"] else None
    if a.json:
        print(json.dumps({**{k: v for k, v in b.items() if k != "plan_batches"}, **({"plan_id": plan_id} if plan_id else {}), "not_read": [s["id"] for s in b["not_read"]],
                          "extract": [s["id"] for s in b["extract"]]}, indent=1))
        return 0
    print("\n\n".join(b["read"]) or "no section found; route in other words or refresh")
    rd = f"python3 {os.path.join(CODE, 'scripts', 'read.py')}"
    for line in b["notices"]:
        print(line)
    if b["too_broad"]:
        print(f"goal too broad: {b['too_broad']['batches']} batches ({b['too_broad']['tokens']:,} tokens); "
              f"narrow the goal or split it into runs")
    elif b["plan_batches"]:
        total = sum(s["tokens"] for s in b["not_read"])
        print(f"READING PLAN: {len(b['not_read'])} sections, {total:,} tokens not yet read, more than the cap ({a.cap:,}). "
              f"Start one reader per batch (SKILL.md, \"Over the cap\").")
        print("GOAL: " + " | ".join(qs))
        for n, batch in enumerate(b["plan_batches"], 1):
            print(f"BATCH {n} (~{sum(s['tokens'] for s in batch):,} tokens)")
        for n, batch in enumerate(b["plan_batches"], 1):
            print(reader_block(plan_id, n, batch, qs))
    else:
        for s in b["not_read"]:
            print(f"NOT YET READ (over the cap): {rd} {shlex.quote(s['id'])}  # {s['path']}#{s['heading']}")
    for s in b["extract"]:
        print(f"EXTRACT (claims from it are unverified until read in full): {rd} '{s['id']}'")
    if len(groups) > 1:
        for c in b["coverage"]:
            if not c["read"] and not c["planned"]:
                print(f"NO SOURCE FOUND: {c['q']}")
        print("COVERAGE:")
        for n, c in enumerate(b["coverage"], 1):
            if not c["read"] and not c["planned"]:
                print(f"  {n}. {c['q']}: NO SOURCE FOUND (nothing to read in full; EXTRACT only: {len(c['extract'])})")
            else:
                word = "unread" if b["too_broad"] else "in plan"  # a too-broad goal has no plan to be in
                print(f"  {n}. {c['q']}: read {len(c['read'])}, {word} {len(c['planned'])}")
    print(f"semantic: {b['semantic']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
