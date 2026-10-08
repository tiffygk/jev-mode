"""Run the judgment eval: SKILL.md + rubric section 1 (routing) as the system prompt, 4 packets per call, N reps.
Refuses (exit 2) on a bad gold file, a dirty or behind-main repo, an --out outside the runs folder, or an --out folder that
already holds files. The runs folder is $JEVALUATE_RUNS when set (a folder outside the repo, so run output never sits in a
checkout), else jevaluate-eval/.work/ (git-ignored)."""
import argparse, json, os, pathlib, subprocess, sys
import tempfile as _tf; sys.pycache_prefix = _tf.mkdtemp(prefix="jev-pyc-")  # never load a cached .pyc another process wrote (2026-10-05)
from build_packets import build, runs_folder
import score, runners

HERE = pathlib.Path(__file__).parent; SKILL = HERE.parent / "jevaluate"
sys.path.insert(0, str(SKILL / "scripts"))
import rubric_text

def system_prompt():
    return "\n\n".join([(SKILL / "SKILL.md").read_text(), rubric_text.section(1)])

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)

GOLDEN_DIRS = ("jevaluate/", "jevaluate-harness/", "jevaluate-eval/", "shared/")

def preflight_repo(repo):
    """Problems that make a paid run meaningless: uncommitted skill changes, or main ahead on the skill folders."""
    probs = []
    st = _git(repo, "status", "--porcelain", "--", *GOLDEN_DIRS)
    if st.returncode != 0: return [f"git status failed: {st.stderr.strip()}"]
    if st.stdout.strip(): probs.append("uncommitted changes in the golden folders; commit them first:\n" + st.stdout.rstrip())
    lg = _git(repo, "log", "--oneline", "HEAD..main", "--", *GOLDEN_DIRS)
    if lg.returncode != 0: probs.append(f"cannot compare with main: {lg.stderr.strip()}")
    elif lg.stdout.strip(): probs.append("main has commits touching jevaluate/ or jevaluate-harness/ that this branch lacks; merge main first:\n" + lg.stdout.rstrip())
    return probs

def runs_dir():
    """Where run output goes (build_packets.runs_folder); exits 2 with one sentence on a bad JEVALUATE_RUNS."""
    folder, problem = runs_folder()
    if problem: print(problem, file=sys.stderr); sys.exit(2)
    return folder

def preflight_out(out):
    folder, problem = runs_folder()
    if problem: return [problem]
    p = pathlib.Path(out).resolve()
    if "JEVALUATE_RUNS" in os.environ:
        if folder not in p.parents:
            return [f"--out {out} must be a folder inside $JEVALUATE_RUNS ({folder}): run output is kept outside the repo, so it outlives the checkout"]
    elif ".work" not in p.parts: return [f"--out {out} must be under .work/ (git-ignored), or the git-status check refuses the next run"]
    used = sorted(x.name for x in p.iterdir()) if p.is_dir() else []
    if used: return [f"--out {out} is not empty ({', '.join(used[:4])}{' ...' if len(used) > 4 else ''}): its old rep files would mix into this run's score; pass a new --out folder"]
    return []

MODELS = {"claude": "claude-sonnet-5-5", "codex": "gpt-6-sol"}

def write_stamp(out, phase, repo, reps, runner="claude", model=MODELS["claude"], effort="medium"):
    head = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    (pathlib.Path(out) / "run.json").write_text(json.dumps({"phase": phase, "head": head, "gold_fingerprint": score.fingerprint(HERE), "reps": reps, "rubric": score.rubric_text.version(), "rubric_status": score.rubric_text.frozen_status()[0], "rubric_detail": score.rubric_text.frozen_status()[1], "golden": score.rubric_text.golden_hash(), "runner": runner, "model": model, "effort": effort}, indent=1))

def add_runner_args(ap):
    ap.add_argument("--runner", choices=["claude", "codex"], default="claude"); ap.add_argument("--model")

def runner_setup(a):
    """(model, home, system suffix) for the chosen runner; exits 2 with one sentence, before any file is written, if Codex can't run."""
    model = a.model or MODELS[a.runner]
    if a.runner == "claude": return model, None, ""
    home = runners.codex_home(); problem = runners.codex_ready(home)
    if problem: runners.close_home(home); print(problem, file=sys.stderr); sys.exit(2)
    notes = (HERE / "codex-notes.md").read_text().strip()
    return model, home, ("\n\n" + notes if notes else "")

def run_call(a, model, home, system_file, prompt, out_file, label):
    d = runners.call(a.runner, system_file, prompt, model, a.effort, home=home)
    out_file.write_text(json.dumps(d))
    print(f"{label}: {'answered' if d.get('result') else 'no answer'}" + (f"; used tools: {d['commands']}" if d.get("commands") else "") + (f"; error: {d['error'][:200]}" if d.get("error") else ""))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=3); ap.add_argument("--effort", default="medium")
    ap.add_argument("--phase", required=True, choices=["baseline", "after"]); ap.add_argument("--out", required=True); ap.add_argument("--ids", default="", help="comma-separated case ids; default all")
    add_runner_args(ap); a = ap.parse_args()
    repo = SKILL.parent
    probs = score.preflight(json.loads((HERE / "gold.json").read_text())) + preflight_out(a.out) + preflight_repo(repo)
    if probs: print("\n".join(probs), file=sys.stderr); sys.exit(2)
    model, home, suffix = runner_setup(a)
    try:
        run_all(a, model, home, suffix, repo)
    finally:  # copies a refreshed Codex login back even after Ctrl-C or an error
        if home: runners.close_home(home)

def select(sources, ids):
    """Only the named cases (comma-separated); all when empty. An unknown id exits with one sentence."""
    want = [i for i in ids.split(",") if i]
    unknown = [i for i in want if i not in sources]
    if unknown: print(f"unknown case ids: {', '.join(unknown)}", file=sys.stderr); sys.exit(2)
    return {k: v for k, v in sources.items() if not want or k in want}

def run_all(a, model, home, suffix, repo):
    out = pathlib.Path(a.out); pk = out / "packets"; out.mkdir(parents=True, exist_ok=True)
    write_stamp(out, a.phase, repo, a.reps, a.runner, model, a.effort)
    status = build(select(json.loads((HERE / "sources.json").read_text()), a.ids), pk)
    (out / "status.json").write_text(json.dumps(status, indent=1))
    (out / "system.md").write_text(system_prompt() + suffix); (out / "task.md").write_text((HERE / "task.md").read_text())
    ready = [s for s, st in status.items() if st == "ok"]
    groups = [ready[i:i + 4] for i in range(0, len(ready), 4)]
    for rep in range(1, a.reps + 1):
        for gi, g in enumerate(groups):
            prompt = (HERE / "task.md").read_text() + "".join("\n\n" + (pk / f"{s}.md").read_text() for s in g)
            run_call(a, model, home, out / "system.md", prompt, out / f"r{rep}_g{gi}.json", f"rep {rep} group {gi}: {len(g)} cases")
    print("skipped:", {s: st for s, st in status.items() if st != "ok"})

if __name__ == "__main__":
    main()
