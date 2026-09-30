"""Run the comprehension quiz: invented scenarios, the eval grader's instructions, N reps.
Usage: run_quiz.py --system routing|vocab --reps N --out <.work dir> [--ids q01,q02]
routing = SKILL.md + rubric section 1 (what the eval grader gets); vocab = SKILL.md + only the allowed-value lines (the red control)."""
import argparse, json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).parent; EVALS = HERE.parent; SKILL = EVALS.parent / "jevaluate"
sys.path.insert(0, str(EVALS)); sys.path.insert(0, str(SKILL / "scripts"))
import rubric_text, run_eval

def system(kind):
    if kind == "routing": return run_eval.system_prompt()
    vals = rubric_text.allowed_values()
    return (SKILL / "SKILL.md").read_text() + "\n\n## Allowed values\n" + "\n".join(f"- `{k}` values: {', '.join(v)}" for k, v in vals.items())

def prompt(scen):
    task = (EVALS / "task.md").read_text()
    return task + "".join(f"\n\n# Project: {s['id']}\n{s['text']}\n" for s in scen)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--system", required=True, choices=["routing", "vocab"])
    ap.add_argument("--reps", type=int, default=3); ap.add_argument("--out", required=True); ap.add_argument("--ids", default="")
    a = ap.parse_args()
    probs = run_eval.preflight_out(a.out) + run_eval.preflight_repo(SKILL.parent)
    if probs: print("\n".join(probs), file=sys.stderr); sys.exit(2)
    key = json.loads((HERE / "expected.json").read_text())
    ids = [i for i in a.ids.split(",") if i] or sorted(key)
    scen = [s for s in json.loads((HERE / "scenarios.json").read_text()) if s["id"] in ids]
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    run_eval.write_stamp(out, "baseline", SKILL.parent)
    (out / "system.md").write_text(system(a.system)); groups = [scen[i:i + 4] for i in range(0, len(scen), 4)]
    for rep in range(1, a.reps + 1):
        for gi, g in enumerate(groups):
            res = subprocess.run(["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "",
                                  "--system-prompt-file", str(out / "system.md"), "--model", "claude-sonnet-5-5",
                                  "--effort", "medium", "--output-format", "json"], input=prompt(g), capture_output=True, text=True)
            (out / f"r{rep}_g{gi}.json").write_text(res.stdout or json.dumps({"result": "", "error": res.stderr}))
            print(f"rep {rep} group {gi}: {len(g)} scenarios, exit {res.returncode}")

if __name__ == "__main__":
    main()
