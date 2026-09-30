"""Where is this workflow? Usage: harness_status.py <ledger.md> --workflow rubric|round
The ledger has one line per finished step: `done: <step> <YYYY-MM-DD> <evidence>`. A step that has a scripted
gate is rerun here, and counts as done only when the check itself runs and passes; the ledger line is not trusted."""
import argparse, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
WORKFLOWS = {
    "rubric": [("rules-written", "rubric-change.md"), ("materials-checked", "jevaluate-eval"), ("quiz-passed", "jevaluate-eval"),
               ("eval-passed", "jevaluate-eval"), ("owner-approved", "rubric-change.md"), ("frozen", "rubric-change.md")],
    "round": [("picked", "rating-round.md"), ("sized", "rating-round.md"), ("costs-approved", "rating-round.md"), ("rated", "rating-round.md"),
              ("scanned", "rating-round.md"), ("adjudicated", "rating-round.md"), ("final-gate", "rating-round.md"),
              ("release-check", "publish.md"), ("published", "publish.md")]}

def _run(script):
    """(passed, last 200 chars of output); a script that is not there is a failure, never a pass."""
    script = pathlib.Path(script)
    if not script.exists(): return False, f"{script.name} not found, so the check did not run"
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-200:]

def make_gates():
    return {"materials-checked": lambda: _run(REPO / "jevaluate-eval/lint_materials.py"),
            "release-check": lambda: _run(HERE / "check_release.py")}

GATES = make_gates()

def status(ledger, workflow, run_gates=True):
    """One row per step: state done | next | waiting, the file to open, whether a scripted gate was rerun and passed, and why not."""
    p = pathlib.Path(ledger)
    done = set(re.findall(r"^done: (\S+)", p.read_text(), re.M)) if p.exists() else set()
    rows, found_next = [], False
    for step, where in WORKFLOWS[workflow]:
        ok, checked, detail = step in done, None, ""
        if step in GATES:
            checked = False
            if ok and run_gates:
                ok, detail = GATES[step]()
                checked = ok
        state = "done" if ok and not found_next else ("next" if not found_next else "waiting")
        if state == "next": found_next = True
        rows.append({"step": step, "state": state, "open": where, "checked": checked, "detail": detail})
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("ledger"); ap.add_argument("--workflow", choices=WORKFLOWS, required=True); a = ap.parse_args()
    for r in status(a.ledger, a.workflow):
        note = ("-> open " + r["open"]) if r["state"] == "next" else ""
        if r["state"] == "done" and r["checked"]: note = "(check rerun, passed)"
        if r["state"] == "next" and r["detail"]: note += f"  check failed: {r['detail']}"
        print(f"{r['state']:8s} {r['step']:18s} {note}".rstrip())
