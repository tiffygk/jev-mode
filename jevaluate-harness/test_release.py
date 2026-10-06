import re
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

def test_fixtures_behave(tmp_path):
    lib = HERE.parent / "jevaluate" / "scripts" / "library.py"
    sys.path.insert(0, str(lib.parent)); import rubric_text, shutil
    fx = tmp_path / "fixtures"; shutil.copytree(HERE / "fixtures", fx)
    for name in ("good-rating.md", "bad-rating.md"):  # rated under this checkout's rubric version
        f = fx / name; f.write_text(re.sub(r"^rubric: .*$", f"rubric: {rubric_text.version()}", f.read_text(), count=1, flags=re.M))
    env = {**__import__("os").environ, "JEVALUATE_LIBRARY": str(tmp_path / "lib")}  # never the owner's real library
    good = subprocess.run([sys.executable, str(lib), "check", str(fx / "good-rating.md")], capture_output=True, text=True, env=env)
    bad = subprocess.run([sys.executable, str(lib), "check", str(fx / "bad-rating.md")], capture_output=True, text=True, env=env)
    assert good.returncode == 0, good.stdout
    assert bad.returncode != 0, bad.stdout


def test_same_day_after_run_beats_the_baseline(tmp_path):
    (tmp_path / "2026-10-01-baseline.md").write_text("Run: phase=baseline rubric=2026-09-29 commit=abc passed=yes\n")
    (tmp_path / "2026-10-01-after.md").write_text("Run: phase=after rubric=2026-09-29 commit=def passed=no\n")
    ok, detail = cr.eval_stamp(tmp_path, "2026-09-29")
    assert ok is False and "after" in detail
