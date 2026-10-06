"""Compare a Codex eval run with the saved Sonnet run on equal terms.
Usage: compare_runs.py report <sonnet run> <codex run> [--reps N]
Checks the two runs saw the same system prompt and packets (byte for byte; Codex notes appended at the end are
reported apart), then scores both with today's score.py and prints one side-by-side table."""
import json, pathlib, subprocess, sys
import tempfile as _tf; sys.pycache_prefix = _tf.mkdtemp(prefix="jev-pyc-")  # never load a cached .pyc another process wrote (2026-10-05)
HERE = pathlib.Path(__file__).parent; sys.path.insert(0, str(HERE))
import score

FIELDS = ("kind_ok", "type_ok", "f0_ok", "code_ok", "stakes_ok")


def task_text(run):
    """The task.md a run used: saved in the run folder, else read from git at the run's stamped commit."""
    p = pathlib.Path(run) / "task.md"
    if p.exists(): return p.read_bytes()
    head = stamp(run).get("head")
    for path in ("jevaluate-eval/task.md", "jevaluate/evals/task.md"):
        r = subprocess.run(["git", "-C", str(HERE), "show", f"{head}:{path}"], capture_output=True)
        if head and r.returncode == 0: return r.stdout
    return None


def same_inputs(a, b):
    """([problems], appended text): what differs between run a's inputs and run b's."""
    a, b = pathlib.Path(a), pathlib.Path(b); probs = []
    sa, sb = (a / "system.md").read_bytes(), (b / "system.md").read_bytes()
    extra = ""
    if sb.startswith(sa): extra = sb[len(sa):].decode()
    else: probs.append("system.md differs")
    ta, tb = task_text(a), task_text(b)
    if ta is None or tb is None: probs.append("task.md for one run can't be found")
    elif ta != tb: probs.append("task.md differs")
    pa = {p.name: p.read_bytes() for p in (a / "packets").glob("*.md")}
    pb = {p.name: p.read_bytes() for p in (b / "packets").glob("*.md")}
    for n in sorted(set(pa) | set(pb)):
        if n not in pb: probs.append(f"packet {n} missing from {b.name}")
        elif n not in pa: probs.append(f"packet {n} not in {a.name}")
        elif pa[n] != pb[n]: probs.append(f"packet {n} differs")
    return probs, extra


def stamp(run):
    try: return json.loads((pathlib.Path(run) / "run.json").read_text())
    except (OSError, ValueError): return {}


def side_by_side(rs, rc):
    c = {r["slug"]: r for r in rc}
    head = "| case | set | Sonnet answered | Sol answered | " + " | ".join(f.replace("_ok", "") + " S/Sol" for f in FIELDS) + " | Sonnet pass | Sol pass |"
    out = [head, "|" + "---|" * (6 + len(FIELDS))]
    for r in rs:
        k = c.get(r["slug"], {})
        cells = [f"{r.get(f, '-')}/{k.get(f, '-')}" for f in FIELDS]
        out.append(f"| {r['slug']} | {r['set']} | {r['answered']}/{r['reps']} | {k.get('answered', '-')}/{k.get('reps', '-')} | " + " | ".join(cells) + f" | {r['pass']} | {k.get('pass', '-')} |")
    return "\n".join(out)


def tool_calls(run):
    n = []
    for f in sorted(pathlib.Path(run).glob("r*_g*.json")):
        try: d = json.loads(f.read_text())
        except ValueError: n.append(f"{f.name}: unreadable"); continue
        if d.get("commands"): n.append(f"{f.name}: {d['commands']}")
        if not d.get("result"): n.append(f"{f.name}: no answer ({str(d.get('error', ''))[:120]})")
    return n


def report(sonnet, codex, reps=None):
    gold = json.loads((HERE / "gold.json").read_text())
    ss, sc = stamp(sonnet), stamp(codex)
    stale = score.check_stamp(sonnet) + score.check_stamp(codex)
    if stale: sys.exit("not comparable with today's answer key:\n" + "\n".join(stale))
    if ss.get("gold_fingerprint") != sc.get("gold_fingerprint"):
        sys.exit(f"answer keys differ: Sonnet run {ss.get('gold_fingerprint')}, Codex run {sc.get('gold_fingerprint')}; not comparable")
    probs, extra = same_inputs(sonnet, codex)
    if probs: sys.exit("inputs differ, not comparable:\n" + "\n".join(probs))
    rep = {}
    for name, run in (("Sonnet", sonnet), ("Codex", codex)):
        n, problem = score.planned_reps(run, reps)  # --reps fills in only for a run whose stamp has none; a disagreement is refused
        if problem: sys.exit(f"{name} run: {problem}")
        rep[name] = n
    rs, ps, ts = score.score(sonnet, gold, rep["Sonnet"])
    rc, pc, tc = score.score(codex, gold, rep["Codex"])
    used = [x for x in tool_calls(codex) if "no answer" not in x]
    notes = (HERE / "codex-notes.md").read_text().strip()
    if extra.strip() and extra.strip() != notes: sys.exit("the Codex notes in this run differ from today's codex-notes.md")
    lines = [f"Sonnet: {ss.get('model', 'claude-sonnet-5-5')} commit {ss.get('head')} | Codex: {sc.get('model')} effort {sc.get('effort')} commit {sc.get('head')} | key {ss.get('gold_fingerprint')}",
             "Inputs: identical (system prompt, packets, task.md)" + (f"; Codex notes appended:\n{extra.strip()}" if extra.strip() else ""), "",
             *(["INVALID: Sol used tools in some calls, so it may have read files; see the list below.", ""] if used else []),
             side_by_side(rs, rc), "",
             f"Overall: Sonnet {score.overall_line(ps, sonnet)[9:]}, Sol {score.overall_line(pc, codex)[9:]} (today's score.py for both)",
             f"Tokens: Sonnet {ts:,}; Sol {tc:,} (Codex carries built-in tool overhead; not a quality measure)", "",
             "Sol calls with tool use or no answer:", *(tool_calls(codex) or ["none"])]
    return "\n".join(lines)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or a[0] != "report": print(__doc__); sys.exit(2)
    reps = int(a[a.index("--reps") + 1]) if "--reps" in a else None  # only for a run whose stamp has none
    print(report(a[1], a[2], reps))
