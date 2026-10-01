"""Score an eval run against gold.json. Pass bar: tuning cases 3/3 on kind, type, F0 and verdict-1 code; held-out 2/3;
top stakes 2/3 wherever gold gives one (never where gold is n.a.: code works those out), taken from the answer's decisions list as library.highest_stakes orders it, not from its stated top_stakes. A run with no case run, or any case skipped (tuning or held-out), is not a pass and lists the skips.
The planned rep count (run.json "reps", or --reps N for an older run) is the denominator: a rep file that is missing is a miss, and a run
with no planned count is refused. Held-out and stakes bars are ceil(2N/3) of N reps.
Exit 0 on pass, 1 on fail, 2 on a bad gold file, a run whose gold changed since it was made, or no planned rep count.
Usage: score.py <rundir> [--reps N]"""
import hashlib, json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "jevaluate" / "scripts"))
import rubric_text
from library import highest_stakes

NOT_MEASURED = "Not measured: facts F1-F23, verdicts 2 to 5, guide scoring."

def _level(s):
    s = str(s or "").lower().strip()
    return "n.a." if s in ("n.a.", "n.a", "na", "n/a") else "very high" if "very high" in s else "high" if "high" in s else "low" if "low" in s else None

_stakes = _level

def fingerprint(here=HERE):
    """First 12 hex chars of sha1 over gold.json and sources.json bytes: what the answers were scored against."""
    h = hashlib.sha1()
    for f in ("gold.json", "sources.json"): h.update((pathlib.Path(here) / f).read_bytes())
    return h.hexdigest()[:12]

def preflight(gold):
    """Problems in gold: any type, kind or code the rubric does not allow."""
    allowed = rubric_text.allowed_values()
    fields = (("type", "project_type"), ("kind", "kind"), ("code", "verdict_1_code"))
    probs = []
    for slug, g in gold.items():
        for field, name in fields:
            if g.get(field) not in allowed.get(name, []):
                probs.append(f"{slug}: {field} {g.get(field)!r} is not an allowed {name} value ({', '.join(allowed.get(name, []))})")
    return probs

def check_stamp(rundir, here=HERE):
    """Problems with the run's run.json: missing, or gold/sources changed since the run."""
    p = pathlib.Path(rundir) / "run.json"
    try: d = json.loads(p.read_text())
    except (OSError, ValueError): return [f"{p} is missing or unreadable; the run has no stamp"]
    if d.get("gold_fingerprint") != fingerprint(here):
        return [f"gold.json or sources.json changed since this run (run {d.get('gold_fingerprint')}, now {fingerprint(here)}); rerun"]
    return []

def _answers(path):
    tok = 0
    try:
        d = json.loads(path.read_text())
        u = d.get("usage") or {}; tok = sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"))
        m = re.search(r"\[.*\]", d.get("result") or "", re.S)
        ans = json.loads(m.group(0)) if m else []
        return (ans if isinstance(ans, list) else []), tok
    except (ValueError, AttributeError, TypeError, OSError):
        return [], tok

def _f0(a):
    v = str(a.get("calls_jev", a.get("calls_hosted_jev", ""))).lower().strip()
    return "n.a." if v in ("n.a.", "n.a", "na", "n/a") else v

def _top_stakes(a):
    """The answer's top stakes as a rating derives it: the highest level among its decisions (None with none); its stated top_stakes is not read."""
    ds = a.get("decisions"); ds = ds if isinstance(ds, list) else []
    return highest_stakes([l for l in (_level(d.get("stakes")) if isinstance(d, dict) else None for d in ds) if l in ("very high", "high", "low")])

def _stakes_gold(g): return g.get("top_stakes") not in (None, "n.a.")

def _f0_ok(a, g):
    """A guide's calls-Jev may be no or n.a.; every other case must match exactly."""
    got = _f0(a)
    return got in ("no", "n.a.") if g["f0"] == "n.a." and g["type"] == "guide" else got == g["f0"]

def score(rundir, gold, reps=None):
    if not reps: raise ValueError("the planned rep count is unknown: pass reps (score.py --reps N for a run whose run.json has none)")
    runs, tokens = {}, 0
    for f in sorted(pathlib.Path(rundir).glob("r*_g*.json")):
        rep = f.name.split("_")[0]; ans, t = _answers(f); tokens += t
        runs.setdefault(rep, []).extend(a for a in ans if isinstance(a, dict))
    reps = [f"r{i}" for i in range(1, reps + 1)]
    need_some = -(-2 * len(reps) // 3)  # ceil(2N/3): 2 of 3 reps
    sp = pathlib.Path(rundir) / "status.json"
    try: status = json.loads(sp.read_text()) if sp.exists() else {}
    except ValueError: status = {}
    rows, passed, ran = [], True, 0
    for slug, g in gold.items():
        base = {"slug": slug, "set": g["set"], "synthetic": bool(g.get("synthetic")), "reps": len(reps)}
        if status.get(slug, "ok") != "ok":
            rows.append(dict(base, answered=status[slug], kind_ok="-", type_ok="-", f0_ok="-", code_ok="-", stakes_ok="-", types_seen=[], **{"pass": "skipped"}))
            passed = False  # any skipped case, tuning or held-out, fails the run
            continue
        ran += 1
        hits = [next((x for x in runs.get(rep, []) if any(k.lower() in str(x.get("project", "")).lower() for k in g["match"])), None) for rep in reps]
        got = [a for a in hits if a]
        ok = lambda f: sum(1 for a in got if f(a))
        row = dict(base, answered=len(got),
                   kind_ok=ok(lambda a: rubric_text.KIND_OF.get(str(a.get("project_type", "")).lower()) == g["kind"]),  # kind is derived from the answer's type
                   type_ok=ok(lambda a: str(a.get("project_type", "")).lower() == g["type"]),
                   f0_ok=ok(lambda a: _f0_ok(a, g)),
                   code_ok=ok(lambda a: str(a.get("verdict_1_code", "")).lower() == g["code"]),
                   stakes_ok=ok(lambda a: not _stakes_gold(g) or _top_stakes(a) == g["top_stakes"]),
                   types_seen=sorted({str(a.get("project_type", "")).lower() for a in got}))
        need = len(reps) if g["set"] == "tuning" else need_some
        row["pass"] = all(row[k] >= need for k in ("kind_ok", "type_ok", "f0_ok", "code_ok")) and (not _stakes_gold(g) or row["stakes_ok"] >= need_some)
        passed &= row["pass"]; rows.append(row)
    return rows, bool(passed and ran), tokens

def _rows_table(rows, reps):
    out = ["| case | set | answered | kind | type | F0 | code | stakes | types seen | pass |", "|---|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {r['slug']} | {r['set']} | {r['answered'] if r['pass'] == 'skipped' else str(r['answered']) + '/' + str(reps or r.get('reps', 3))} | {r['kind_ok']} | {r['type_ok']} | {r['f0_ok']} | {r['code_ok']} | {r['stakes_ok']} | {', '.join(r['types_seen'])} | {r['pass'] if r['pass'] == 'skipped' else 'yes' if r['pass'] else 'NO'} |" for r in rows]
    return "\n".join(out)

def table(rows, tokens, reps=None):
    real = [r for r in rows if not r.get("synthetic")]; syn = [r for r in rows if r.get("synthetic")]
    ran = sum(1 for r in rows if r["pass"] != "skipped")
    out = [f"{ran} of {len(rows)} cases ran.", "", _rows_table(real, reps)]
    if syn: out += ["", "Synthetic cases (written for this eval; reported apart from real projects):", "", _rows_table(syn, reps)]
    skipped = [f"{r['slug']} ({r['answered']})" for r in rows if r["pass"] == "skipped"]
    if skipped: out += ["", "Skipped, so the run fails: " + ", ".join(skipped)]
    out += ["", NOT_MEASURED, "", f"Tokens: {tokens:,} (headless; add to the budget by hand)", ""]
    return "\n".join(out)

def planned_reps(run, argv_reps):
    """(reps, problem): the run.json rep count, or --reps for a run that has none; a problem when neither is given or they disagree."""
    try: stamped = json.loads((pathlib.Path(run) / "run.json").read_text()).get("reps")
    except (OSError, ValueError): stamped = None
    if stamped and argv_reps and stamped != argv_reps: return None, f"--reps {argv_reps} disagrees with the {stamped} reps planned in run.json; drop --reps"
    reps = stamped or argv_reps
    if not reps: return None, f"{run}/run.json has no rep count (a run made before run_eval.py wrote one); rerun score.py with --reps N, the number of reps that run planned"
    return int(reps), None

def stamp_line(run, passed):
    """First output line: what was run, on which rubric and commit, and whether it passed."""
    info = json.loads((pathlib.Path(run) / "run.json").read_text())
    return f"Run: phase={info.get('phase')} rubric={info.get('rubric', 'unknown')} commit={info.get('head')} passed={'yes' if passed else 'no'}"  # the rubric the run was made on

if __name__ == "__main__":
    args = sys.argv[1:]; argv_reps = None
    if "--reps" in args:
        i = args.index("--reps")
        try: argv_reps = int(args[i + 1]); del args[i:i + 2]
        except (IndexError, ValueError): print("--reps needs a whole number", file=sys.stderr); sys.exit(2)
    run = pathlib.Path(args[0])
    gold = json.loads((HERE / "gold.json").read_text())
    probs = preflight(gold) + check_stamp(run)
    if not probs:
        n, why = planned_reps(run, argv_reps)
        if why: probs.append(why)
    if probs: print("\n".join(probs), file=sys.stderr); sys.exit(2)
    rows, passed, tok = score(run, gold, n)
    print(stamp_line(run, passed))
    print((run / "run.json").read_text())
    print(table(rows, tok, n)); sys.exit(0 if passed else 1)
