"""Release check: run before publishing. Exits 0 only when every check passes."""
import argparse, pathlib, re, shutil, subprocess, sys, tempfile

def run(cmd, cwd=None): r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True); return r.returncode, r.stdout + r.stderr

def tests(repo):
    code, out = run([sys.executable, "-m", "pytest", "-q", "jevaluate/scripts", "jevaluate-eval", "jevaluate-harness"], cwd=repo)
    return code == 0, out.strip().splitlines()[-1] if out.strip() else "no output"

def clone_smoke(repo):
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        code, out = run(["git", "clone", "-q", "--depth", "1", f"file://{pathlib.Path(repo).resolve()}", str(tmp / "r")])
        if code: return False, "clone failed: " + out[-600:]
        r = tmp / "r"; lib = r / "jevaluate/scripts/library.py"; fx = r / "jevaluate-harness/fixtures"
        if run([sys.executable, str(lib), "check", str(fx / "good-rating.md")])[0] != 0: return False, "good fixture refused in the clone"
        if run([sys.executable, str(lib), "check", str(fx / "bad-rating.md")])[0] == 0: return False, "bad fixture accepted in the clone"
        new = tmp / "new.md"; new.write_text("---\nproject: T\nurl: https://github.com/o/t\nowner: o\nrated: 2026-09-29\ncommit: abc1234\n---\n")
        (tmp / "manifest.md").write_text("# Coverage manifest\n\nAbout ~10,000 tokens.\n\n| file | chars | jev | decision | eval |\n|---|---|---|---|---|\n| a.py | 10 | 1 | 0 | 0 |\n")
        code, out = run([sys.executable, str(r / "jevaluate/scripts/step.py"), "next", str(new)])
        if code or "## 1. Routing" not in out or "## 2. Facts" in out: return False, "step.py didn't serve routing only"
        if run([sys.executable, str(r / "jevaluate-eval/lint_materials.py")])[0] != 0: return False, "materials lint failed in the clone"
        return True, "clone installs, check accepts good and refuses bad, step.py and lint run"
    finally: shutil.rmtree(tmp, ignore_errors=True)

def eval_stamp(results_dir, version):
    stamps = sorted(pathlib.Path(results_dir).glob("*-baseline.md")) + sorted(pathlib.Path(results_dir).glob("*-after.md"))
    if not stamps: return False, "no eval result found"
    last = max(stamps, key=lambda p: (p.name[:10], p.name.endswith("-after.md")))  # newest date; on one day the after run is the later one
    m = re.match(r"Run: phase=(\w+) rubric=(\S+) commit=(\S+) passed=(\w+)", last.read_text().splitlines()[0] if last.read_text() else "")
    if not m: return False, f"{last.name} has no stamp line"
    if m.group(2) != version: return False, f"last eval ran on rubric {m.group(2)}, publishing {version}"
    if m.group(4) != "yes": return False, f"last eval ({last.name}) did not pass"
    return True, f"{last.name}: rubric {version}, passed"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", default=str(pathlib.Path(__file__).resolve().parents[2])); a = ap.parse_args()
    sys.path.insert(0, str(pathlib.Path(a.repo) / "jevaluate/scripts")); import rubric_text
    checks = [("tests", tests(a.repo)), ("clone-smoke", clone_smoke(a.repo)),
              ("eval-stamp", eval_stamp(pathlib.Path(a.repo) / "jevaluate-eval/results", rubric_text.version()))]
    for name, (ok, detail) in checks: print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    sys.exit(0 if all(ok for _, (ok, _) in checks) else 1)
