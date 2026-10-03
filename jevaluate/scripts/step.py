"""Serve rubric.md one section at a time. Usage: step.py next <rating.md> | step.py full <rating.md> <past rating> | step.py estimate <manifest.md>.
Each call checks the current phase is written in the rating file, then prints the next section and logs it."""
import datetime, hashlib, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rubric_text as rt
import library as lib

ORDER = ["routing", "facts", "scores", "compare", "verdict"]
ROUTED = lib.ROUTED_CODES
STAKES_FACTS = (11, 13, 20, 22)
ROW_LEVELS = {"low": {"low"}, "high": {"high"}, "very high": {"very high"}, "high or low": {"high", "low"}, "high or very high": {"high", "very high"}}

def fm(t, k): return lib.front_text(t).get(k, "").split("#")[0].strip()
def manifest_for(r):
    m = pathlib.Path(r).parent / "manifest.md"
    if not m.exists(): print(f"No manifest at {m}: run coverage_manifest.py first.", file=sys.stderr); sys.exit(3)
    return m
def estimate(manifest):
    m = re.search(r"~\s*([\d,]+)\s*tokens", manifest.read_text())
    return 45_000 + int(m.group(1).replace(",", "")) if m else 10**9
def approved(r):
    p = pathlib.Path(r).parent / "approved_cost.json"
    return json.loads(p.read_text()).get("approved", 0) if p.exists() else 0
def routing_print(t): return lib.routing_print(lib.front_text(t), t)
def log_path(r): return pathlib.Path(str(r) + ".steps.json")
def read_log(r): p = log_path(r); return json.loads(p.read_text()) if p.exists() else []
def now(): return datetime.datetime.now().isoformat(timespec="seconds")

def template():
    """The rating template in read.md: its text between the ```markdown fence after 'Template:'."""
    try: return (lib.SKILL / "read.md").read_text().split("Template:", 1)[1].split("```markdown\n", 1)[1].split("\n```", 1)[0]
    except (OSError, IndexError): return ""

def is_placeholder(line, key=None):
    """True when a rating line still holds the template's own text: a <placeholder> from the template, or (with a front-matter `key`) the template's value."""
    tmpl = template()
    if any(p in line for p in re.findall(r"<[^<>\n]+>", tmpl)): return True
    return bool(key) and line.split("#")[0].strip() == lib.front_text(tmpl).get(key, "").split("#")[0].strip()

def missing(step, t):
    vals = rt.allowed_values(); need = []
    if step == "routing":
        for k in ("project_type", "verdict_1_code"):
            if fm(t, k) not in vals.get(k, []): need.append(k)
        f0 = re.search(r"^\s*-\s*F0\b.*$", t, re.M)
        if not f0 or is_placeholder(f0.group(0)): need.append("the F0 calls-Jev line (still the template's text, or missing)")
        if rt.KIND_OF.get(fm(t, "project_type")) == "uses" and fm(t, "project_type") != "client" and fm(t, "verdict_1_code") not in ROUTED and not lib.decisions(t)[0]:
            need.append("## Decisions (one line per decision Jev makes: " + lib.DECISION_FORMAT + ")")
        if fm(t, "project_type") == "jev-mention-only":
            need += [k for k in ("citation", "type_best_match", "code_functionality", "replaces_jev", "intended_call") if not fm(t, k)]
    elif step == "facts":
        have = {n for n, (_, line) in lib.facts(t).items() if not is_placeholder(line)}; need += [f"F{n}" for n in range(1, 24) if n not in have]
    elif step == "scores":
        need += [k for k in ("scores", "closes_loop") if not fm(t, k) or is_placeholder(fm(t, k), k)]
    elif step == "compare":
        if not lib.section(t, "Compared with").strip(): need.append("## Compared with")
    return need

def stakes_rows(section, t):
    """Keep, for F11, F13, F20 and F22, only the table rows whose stakes level matches a decision the rating lists."""
    listed = {x["stakes"] for x in lib.decisions(t)[0]}; keep = []
    for line in section.splitlines():
        m = re.match(r"\| F(\d+) ([^|]*)\|", line)
        if m and int(m.group(1)) in STAKES_FACTS:
            label = m.group(2).strip().rsplit(", ", 1)[-1]
            if not (ROW_LEVELS.get(label, set()) & listed): continue
        keep.append(line)
    return "\n".join(keep)

def serve(step, t):
    if step == "routing": return rt.section(1)
    if step == "facts": return stakes_rows(rt.section(2), t) + "\n\n## Jev rules and sources\n" + (lib.SKILL.parent / "shared" / "jev-rules.md").read_text()
    if step == "scores": return rt.section(3) + "\n" + rt.section(4)
    if step == "compare":
        d = lib.front_text(t); cards = lib.cards(d, exclude=f"{d.get('owner', '')}/{d.get('project', '')}")
        prev = lib.latest_rating_for(d.get("url", ""))
        lines = [f"- {c['path']} | verdict {c['verdict']} {c['code']} | {c['why']} | failed: {', '.join(c['failed']) or 'none'}"
                 + ("  [old rubric: context only]" if c["old"] else "") + ("  [full rating: step.py full]" if i < 2 else "") for i, c in enumerate(cards)]
        return ("## Comparison cards, closest first\n" + ("\n".join(lines) or "no similar ratings yet")
                + (f"\n\nThis project's previous rating: {prev} (step.py full)" if prev else ""))
    failed = {lib.fid(n) for n, _, v, _ in lib.fact_rows(t) if v == "no"}
    rows = [l for l in (lib.SKILL / "fix-catalog.md").read_text().splitlines() if l.startswith("| ") and not l.startswith(("| Failed fact", "|---"))
            and (not re.match(r"\| [FG]\d+\b", l) or re.match(r"\| ([FG]\d+)\b", l).group(1) in failed)]
    return rt.section(5) + ("\n\n## Fix-catalog rows for the failed checks\n" + "\n".join(rows) if rows else "")

def next_step(rating):
    t = rating.read_text(); log = [e for e in read_log(rating) if not e["step"].startswith("full:")]
    if not log:
        est = estimate(manifest_for(rating)); print(f"Estimated cost: about {est // 1000}k tokens.")
        if est > 200_000 and approved(rating) < est:
            print(f'Over 200k: stop. The controller approves by writing approved_cost.json beside the rating: {{"approved": {est}}}', file=sys.stderr); sys.exit(3)
        step = "routing"
    else:
        cur = log[-1]["step"]; need = missing(cur, t)
        if need: print("Write these before the next section: " + ", ".join(need), file=sys.stderr); sys.exit(1)
        if cur == "verdict": print("All sections served. Log the rating with library.py add.", file=sys.stderr); sys.exit(1)
        step = "compare" if cur == "routing" and fm(t, "verdict_1_code") in ROUTED else ORDER[ORDER.index(cur) + 1]  # a routed code skips facts and scores, never the comparison (read.md phase 3)
    full_log = read_log(rating) + [{"step": step, "time": now(), "routing": routing_print(t)}]
    log_path(rating).write_text(json.dumps(full_log, indent=1)); print(serve(step, t))

def full(rating, past):
    t = rating.read_text(); d = lib.front_text(t)
    allowed = [str(c["path"]) for c in lib.cards(d, exclude=f"{d.get('owner', '')}/{d.get('project', '')}")[:2]]
    prev = lib.latest_rating_for(d.get("url", ""))
    served = [e["step"] for e in read_log(rating)]
    if not (prev and str(past) == str(prev)) and str(past) not in allowed:
        sys.exit("Only the two closest past ratings, or this project's previous rating, can be read in full.")
    if "compare" not in served: sys.exit("Full ratings are served after the compare step: run step.py next until it prints the comparison cards.")
    log = read_log(rating) + [{"step": f"full:{past}", "time": now(), "routing": routing_print(t)}]
    log_path(rating).write_text(json.dumps(log, indent=1)); print(pathlib.Path(past).read_text())

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("next", "full", "estimate"): print(__doc__, file=sys.stderr); sys.exit(2)
    if sys.argv[1] == "estimate": print(estimate(pathlib.Path(sys.argv[2]))); sys.exit(0)
    r = pathlib.Path(sys.argv[2])
    next_step(r) if sys.argv[1] == "next" else full(r, sys.argv[3] if len(sys.argv) > 3 else "")
