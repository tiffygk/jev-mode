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


LIBRARY_FILES = ["test_applicability.py", "test_route.py", "test_index.py", "test_jev.py", "test_usage_log.py"]

def fake_python_with_pytest(tmp_path, pytest_out="", pytest_exit=0):
    """Like fake_python, but pytest imports, and `-m pytest` prints pytest_out, exits pytest_exit and logs its environment."""
    log, envlog, out = tmp_path / "calls.log", tmp_path / "env.log", tmp_path / "pytest.out"
    out.write_text(pytest_out)
    bin_ = tmp_path / "bin"; bin_.mkdir()
    py = bin_ / "python3"
    py.write_text(f"""#!/bin/bash
echo "$*" >> {log}
if [ "$1" = "-c" ]; then case "$2" in *pytest*) exit 0;; esac; exit 1; fi
if [ "$1" = "-m" ] && [ "$2" = "pytest" ]; then
  echo "pwd=$PWD JEV_LOG=$JEV_LOG JEV_CHECK=$JEV_CHECK JEV_SOURCES_DATA=$JEV_SOURCES_DATA" >> {envlog}
  cat {out}
  exit {pytest_exit}
fi
exit 0
""")
    py.chmod(py.stat().st_mode | stat.S_IEXEC)
    return bin_, log, envlog

def test_failing_library_tests_are_named_and_the_refresh_still_exits_0(tmp_path):
    bin_, log, _ = fake_python_with_pytest(tmp_path, pytest_exit=1, pytest_out=(
        "..F\n= short test summary info =\n"
        "FAILED tests/test_route.py::test_known_question_finds_its_sources[pin the model version] - AssertionError: x\n"
        "ERROR tests/test_index.py::test_rebuild - OSError: y\n"
        "1 failed, 1 error, 1 passed in 1.00s\n"))
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert "library tests: 2 failed" in r.stdout
    assert "tests/test_route.py::test_known_question_finds_its_sources[pin the model version]\n" in r.stdout
    assert "tests/test_index.py::test_rebuild\n" in r.stdout
    assert "AssertionError" not in r.stdout
    assert "check_new.py" in log.read_text()  # the steps after it still run

def test_passing_library_tests_print_one_line(tmp_path):
    bin_, _, _ = fake_python_with_pytest(tmp_path, pytest_out="...\n3 passed in 1.00s\n")
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert [l for l in r.stdout.splitlines() if "library tests" in l] == ["library tests: all passed (3 passed in 1.00s)"]

def test_library_tests_are_skipped_without_pytest(tmp_path):
    bin_, log = fake_python(tmp_path)  # every -c import fails here
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert "library tests skipped: pytest is not installed" in r.stdout
    assert "-m pytest" not in log.read_text() and "check_new.py" in log.read_text()

def test_library_tests_are_skipped_without_the_tests_folder(tmp_path):
    bin_, log, _ = fake_python_with_pytest(tmp_path)
    skill = tmp_path / "skill"; skill.mkdir()
    (skill / "refresh.sh").write_text(open(f"{CODE}/refresh.sh").read())
    e = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", JEV_SOURCES_DATA=str(tmp_path / "data"), JEV_SEMANTIC="off")
    e.pop("JEV_VAULT", None)
    r = subprocess.run(["bash", str(skill / "refresh.sh")], capture_output=True, text=True, env=e)
    assert r.returncode == 0, r.stderr
    assert "library tests skipped: no tests folder" in r.stdout
    assert "-m pytest" not in log.read_text() and "check_new.py" in log.read_text()

def test_a_pytest_that_cannot_finish_still_exits_0(tmp_path):
    bin_, log, _ = fake_python_with_pytest(tmp_path, pytest_out="ERROR: file or directory not found: tests/x.py\n", pytest_exit=4)
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert "library tests: could not finish (pytest exit 4): ERROR: file or directory not found: tests/x.py" in r.stdout
    assert "check_new.py" in log.read_text()

def test_a_library_written_by_the_tests_is_reported(tmp_path):
    bin_, _, _ = fake_python_with_pytest(tmp_path, pytest_exit=1, pytest_out=(
        "...\nLIBRARY WRITTEN BY THE SUITE: docs changed under /lib\n3 passed in 1.00s\n"))
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0, r.stderr
    assert "LIBRARY WRITTEN BY THE SUITE: docs changed under /lib" in r.stdout

def test_library_tests_run_only_the_files_that_read_the_library_with_logging_and_checks_off(tmp_path):
    bin_, log, envlog = fake_python_with_pytest(tmp_path, pytest_out="1 passed in 1.00s\n")
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LOG="on", JEV_CHECK="on")
    assert r.returncode == 0, r.stderr
    calls = log.read_text().splitlines()
    call = next(c for c in calls if c.startswith("-m pytest"))
    assert sorted(a for a in call.split() if a.startswith("tests/")) == sorted(f"tests/{f}" for f in LIBRARY_FILES)
    assert all(os.path.exists(f"{CODE}/tests/{f}") for f in LIBRARY_FILES)
    assert envlog.read_text().strip() == f"pwd={CODE} JEV_LOG=off JEV_CHECK=off JEV_SOURCES_DATA={tmp_path / 'data'}"
    order = [next(i for i, c in enumerate(calls) if key in c) for key in ("route_check.py", "-m pytest", "check_new.py")]
    assert order == sorted(order)
