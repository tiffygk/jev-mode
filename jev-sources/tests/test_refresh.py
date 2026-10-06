import os, subprocess, stat
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fake_python(tmp_path, pip_exit=0):
    """A python3 on PATH that logs its arguments, lacks model2vec, and skips the real build scripts."""
    log = tmp_path / "calls.log"
    bin_ = tmp_path / "bin"; bin_.mkdir()
    py = bin_ / "python3"
    py.write_text(f"""#!/bin/bash
echo "$*" >> {log}
if [ "$1" = "-c" ]; then exit 1; fi
if [ "$1" = "-m" ]; then exit {pip_exit}; fi
exit 0
""")
    py.chmod(py.stat().st_mode | stat.S_IEXEC)
    return bin_, log

def run_refresh(tmp_path, bin_, **env):
    e = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", JEV_SOURCES_DATA=str(tmp_path / "data"), **env)
    e.pop("JEV_VAULT", None)
    return subprocess.run(["bash", f"{CODE}/refresh.sh"], capture_output=True, text=True, env=e)

def test_refresh_installs_model2vec_when_missing(tmp_path):
    bin_, log = fake_python(tmp_path)
    r = run_refresh(tmp_path, bin_)
    assert r.returncode == 0, r.stderr
    assert "-m pip install --user --quiet model2vec" in log.read_text()

def test_refresh_skips_install_when_semantic_off(tmp_path):
    bin_, log = fake_python(tmp_path)
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert "pip" not in log.read_text()

def test_failed_install_still_refreshes(tmp_path):
    bin_, log = fake_python(tmp_path, pip_exit=1)
    r = run_refresh(tmp_path, bin_)
    assert r.returncode == 0, r.stderr
    assert "keyword-only" in r.stdout and "build_index.py" in log.read_text()
