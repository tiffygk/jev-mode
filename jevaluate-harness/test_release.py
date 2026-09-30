import pathlib, subprocess, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "scripts"))
import check_release as cr

def test_eval_stamp_must_match_rubric(tmp_path):
    (tmp_path / "2026-10-01-baseline.md").write_text("Run: phase=baseline rubric=2026-09-28b commit=abc passed=yes\n")
    ok, detail = cr.eval_stamp(tmp_path, "2026-09-29")
    assert not ok and "2026-09-28b" in detail

def test_eval_stamp_must_pass(tmp_path):
    (tmp_path / "2026-10-01-baseline.md").write_text("Run: phase=baseline rubric=2026-09-29 commit=abc passed=no\n")
    assert cr.eval_stamp(tmp_path, "2026-09-29")[0] is False

def test_eval_stamp_ok(tmp_path):
    (tmp_path / "2026-10-01-after.md").write_text("Run: phase=after rubric=2026-09-29 commit=abc passed=yes\n")
    assert cr.eval_stamp(tmp_path, "2026-09-29")[0] is True

def test_fixtures_behave():
    lib = HERE.parent / "jevaluate" / "scripts" / "library.py"
    good = subprocess.run([sys.executable, str(lib), "check", str(HERE / "fixtures" / "good-rating.md")], capture_output=True, text=True)
    bad = subprocess.run([sys.executable, str(lib), "check", str(HERE / "fixtures" / "bad-rating.md")], capture_output=True, text=True)
    assert good.returncode == 0, good.stdout
    assert bad.returncode != 0, bad.stdout
