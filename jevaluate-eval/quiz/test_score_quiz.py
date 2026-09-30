import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import score_quiz as sq

def test_gold_has_every_key_scenario_with_set_and_match():
    g = sq.gold(); key = json.loads((sq.HERE / "expected.json").read_text())
    assert set(g) == set(key) and all(v["match"] == [q] and v["set"] in ("tuning", "heldout") for q, v in g.items())

def test_by_tag_counts_passes():
    rows = [{"slug": "q01", "pass": True}, {"slug": "q02", "pass": False}]
    t = sq.by_tag(rows)
    assert t["calls-jev"] == {"scenarios": 2, "passed": 1}


def test_help_prints_usage_and_exits_zero():
    import subprocess, sys, pathlib
    script = str(pathlib.Path(__file__).parent / "score_quiz.py")
    for flag in ("--help", "-h"):
        r = subprocess.run([sys.executable, script, flag], capture_output=True, text=True)
        assert r.returncode == 0 and "Usage: score_quiz.py" in r.stdout, (flag, r.returncode, r.stderr)
