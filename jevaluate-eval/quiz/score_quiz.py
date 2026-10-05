"""Score a quiz run against the owner's key, per scenario and per rule tag. Usage: score_quiz.py <run dir> [--reps N] (--reps only for a run whose run.json has none)"""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent; sys.path.insert(0, str(HERE.parent))
import score

def gold():
    key = json.loads((HERE / "expected.json").read_text())
    sets = {s["id"]: s["set"] for s in json.loads((HERE / "scenarios.json").read_text())}
    return {q: dict(k, set=sets[q], match=[q]) for q, k in key.items()}

def by_tag(rows):
    tags = {s["id"]: s["tags"] for s in json.loads((HERE / "scenarios.json").read_text())}
    out = {}
    for r in rows:
        for t in tags.get(r["slug"], []):
            d = out.setdefault(t, {"scenarios": 0, "passed": 0}); d["scenarios"] += 1; d["passed"] += bool(r["pass"] is True)
    return out

if __name__ == "__main__":
    if sys.argv[1:2] in (["-h"], ["--help"]): print(__doc__); sys.exit(0)
    argv_reps = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else None
    reps, problem = score.planned_reps(sys.argv[1], argv_reps)
    if problem: print(problem, file=sys.stderr); sys.exit(2)
    rows, passed, tok = score.score(sys.argv[1], gold(), reps)
    print(score.table(rows, tok)); print("\n| Rule tag | Scenarios | Passed |\n|---|---|---|")
    for t, d in sorted(by_tag(rows).items()): print(f"| {t} | {d['scenarios']} | {d['passed']} |")
    print(f"\nOverall: {'PASS' if passed else 'FAIL'}" + score.rubric_note(sys.argv[1]))
