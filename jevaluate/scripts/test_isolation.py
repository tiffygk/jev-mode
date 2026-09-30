import pathlib, subprocess, sys
SCRIPTS = pathlib.Path(__file__).parent

def test_rating_scripts_import_without_eval(tmp_path):
    for name in ("library", "step", "coverage_manifest", "rubric_text"):
        code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import {name}"
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
    assert not (SCRIPTS.parent / "evals").exists()
