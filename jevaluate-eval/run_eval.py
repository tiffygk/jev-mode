"""Run the judgment eval: SKILL.md + rubric section 1 (routing) as the system prompt, 4 packets per call, N reps.
Refuses (exit 2) on a bad gold file, a dirty or behind-main repo, an --out outside .work/, or an --out folder that already holds files."""
import argparse, json, pathlib, subprocess, sys
from build_packets import build
import score

HERE = pathlib.Path(__file__).parent; SKILL = HERE.parent / "jevaluate"
sys.path.insert(0, str(SKILL / "scripts"))
import rubric_text

def system_prompt():
    return "\n\n".join([(SKILL / "SKILL.md").read_text(), rubric_text.section(1)])

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)

def preflight_repo(repo):
    """Problems that make a paid run meaningless: uncommitted skill changes, or main ahead on the skill folders."""
    probs = []
    st = _git(repo, "status", "--porcelain", "--", "jevaluate/", "jevaluate-harness/")
    if st.returncode != 0: return [f"git status failed: {st.stderr.strip()}"]
    if st.stdout.strip(): probs.append("uncommitted changes in jevaluate/ or jevaluate-harness/; commit them first:\n" + st.stdout.rstrip())
    lg = _git(repo, "log", "--oneline", "HEAD..main", "--", "jevaluate/", "jevaluate-harness/")
    if lg.returncode != 0: probs.append(f"cannot compare with main: {lg.stderr.strip()}")
    elif lg.stdout.strip(): probs.append("main has commits touching jevaluate/ or jevaluate-harness/ that this branch lacks; merge main first:\n" + lg.stdout.rstrip())
    return probs

def preflight_out(out):
    p = pathlib.Path(out)
    if ".work" not in p.parts: return [f"--out {out} must be under .work/ (git-ignored), or the git-status check refuses the next run"]
    used = sorted(x.name for x in p.iterdir()) if p.is_dir() else []
    if used: return [f"--out {out} is not empty ({', '.join(used[:4])}{' ...' if len(used) > 4 else ''}): its old rep files would mix into this run's score; pass a new --out folder"]
    return []

def write_stamp(out, phase, repo, reps):
    head = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    (pathlib.Path(out) / "run.json").write_text(json.dumps({"phase": phase, "head": head, "gold_fingerprint": score.fingerprint(HERE), "reps": reps, "rubric": score.rubric_text.version()}, indent=1))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=3); ap.add_argument("--effort", default="medium")
    ap.add_argument("--phase", required=True, choices=["baseline", "after"]); ap.add_argument("--out", required=True); a = ap.parse_args()
    repo = SKILL.parent
    probs = score.preflight(json.loads((HERE / "gold.json").read_text())) + preflight_out(a.out) + preflight_repo(repo)
    if probs: print("\n".join(probs), file=sys.stderr); sys.exit(2)
    out = pathlib.Path(a.out); pk = out / "packets"; out.mkdir(parents=True, exist_ok=True)
    write_stamp(out, a.phase, repo, a.reps)
    status = build(json.loads((HERE / "sources.json").read_text()), pk)
    (out / "status.json").write_text(json.dumps(status, indent=1))
    (out / "system.md").write_text(system_prompt())
    ready = [s for s, st in status.items() if st == "ok"]
    groups = [ready[i:i + 4] for i in range(0, len(ready), 4)]
    for rep in range(1, a.reps + 1):
        for gi, g in enumerate(groups):
            prompt = (HERE / "task.md").read_text() + "".join("\n\n" + (pk / f"{s}.md").read_text() for s in g)
            res = subprocess.run(["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "",
                                  "--system-prompt-file", str(out / "system.md"), "--model", "claude-sonnet-5-5",
                                  "--effort", a.effort, "--output-format", "json"], input=prompt, capture_output=True, text=True)
            (out / f"r{rep}_g{gi}.json").write_text(res.stdout or json.dumps({"result": "", "error": res.stderr}))
            print(f"rep {rep} group {gi}: {len(g)} cases, exit {res.returncode}")
    print("skipped:", {s: st for s, st in status.items() if st != "ok"})

if __name__ == "__main__":
    main()
