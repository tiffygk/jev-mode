import json, os, shutil, subprocess, stat, sys
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

# conftest turns the library-tests step off for every test; a test of the step passes JEV_LIBRARY_TESTS="" to turn it back on
def run_refresh(tmp_path, bin_, *args, **env):
    e = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", JEV_SOURCES_DATA=str(tmp_path / "data"), **env)
    e.pop("JEV_VAULT", None)
    return subprocess.run(["bash", f"{CODE}/refresh.sh", *args], capture_output=True, text=True, env=e)

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


def fake_python_with_pytest(tmp_path, pytest_out="", pytest_exit=0, broken=False):
    """A python3 on PATH that logs its arguments and environment and skips the build scripts, but really runs
    library_tests.py. That script finds a pytest stand-in on PYTHONPATH, which logs its own call."""
    log, envlog, call = tmp_path / "calls.log", tmp_path / "env.log", tmp_path / "pytest-call.json"
    bin_ = tmp_path / "bin"; bin_.mkdir()
    py = bin_ / "python3"
    py.write_text(f"""#!/bin/bash
echo "$*" >> {log}
echo "$1 JEV_LIBRARY_TESTS=$JEV_LIBRARY_TESTS" >> {envlog}
case "$1" in *library_tests.py) exec {sys.executable} "$@";; esac
if [ "$1" = "-c" ]; then exit 1; fi
exit 0
""")
    py.chmod(py.stat().st_mode | stat.S_IEXEC)
    fake = tmp_path / "fake"; fake.mkdir()
    (fake / "pytest.py").write_text("raise ImportError('no pytest')\n" if broken else f"""
import json, os, sys
if __name__ == "__main__":
    json.dump({{"argv": sys.argv[1:], "cwd": os.getcwd(), "env": dict(os.environ)}}, open({str(call)!r}, "w"))
    sys.stdout.write({pytest_out!r})
    sys.exit({pytest_exit})
""")
    return bin_, log, envlog, call, str(fake)

def test_failing_library_tests_are_named_and_the_refresh_still_exits_0(tmp_path):
    bin_, log, _, _, fake = fake_python_with_pytest(tmp_path, pytest_exit=1, pytest_out=(
        "..F\n= short test summary info =\n"
        "FAILED tests/test_route.py::test_known_question_finds_its_sources[pin the model version] - AssertionError: x\n"
        "ERROR tests/test_index.py::test_rebuild - OSError: y\n"
        "1 failed, 1 error, 1 passed in 1.00s\n"))
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    assert "library tests: 2 failed" in r.stdout
    assert "tests/test_route.py::test_known_question_finds_its_sources[pin the model version]\n" in r.stdout
    assert "tests/test_index.py::test_rebuild\n" in r.stdout
    assert "AssertionError" not in r.stdout
    assert "check_new.py" in log.read_text()

def test_passing_library_tests_print_one_line(tmp_path):
    bin_, _, _, _, fake = fake_python_with_pytest(tmp_path, pytest_out="...\n3 passed in 1.00s\n")
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    assert [l for l in r.stdout.splitlines() if "library tests" in l] == ["running the library tests (about 2 minutes)",
                                                                         "library tests: all passed (3 passed in 1.00s)"]

def test_library_tests_are_skipped_without_pytest(tmp_path):
    bin_, log, _, call, fake = fake_python_with_pytest(tmp_path, broken=True)
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    assert "library tests skipped: pytest is not installed" in r.stdout
    assert not call.exists() and "check_new.py" in log.read_text()

def test_library_tests_are_skipped_without_the_tests_folder(tmp_path):
    bin_, log, _, call, fake = fake_python_with_pytest(tmp_path)
    skill = tmp_path / "skill"; (skill / "scripts").mkdir(parents=True)
    shutil.copy(f"{CODE}/refresh.sh", skill)
    for f in ("library_tests.py", "paths.py"):
        shutil.copy(f"{CODE}/scripts/{f}", skill / "scripts")
    e = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", JEV_SOURCES_DATA=str(tmp_path / "data"), JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    e.pop("JEV_VAULT", None)
    r = subprocess.run(["bash", str(skill / "refresh.sh")], capture_output=True, text=True, env=e)
    assert r.returncode == 0, r.stderr
    assert "library tests skipped: no tests folder" in r.stdout
    assert not call.exists() and "check_new.py" in log.read_text()

def test_a_pytest_that_cannot_finish_still_exits_0(tmp_path):
    bin_, log, _, _, fake = fake_python_with_pytest(tmp_path, pytest_out="ERROR: file or directory not found: tests/x.py\n", pytest_exit=4)
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    assert "library tests: could not finish (pytest exit 4): ERROR: file or directory not found: tests/x.py" in r.stdout
    assert "check_new.py" in log.read_text()

def test_a_library_written_by_the_tests_is_reported(tmp_path):
    bin_, _, _, _, fake = fake_python_with_pytest(tmp_path, pytest_exit=1, pytest_out=(
        "...\nLIBRARY WRITTEN BY THE SUITE: docs changed under /lib\n3 passed in 1.00s\n"))
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    assert "LIBRARY WRITTEN BY THE SUITE: docs changed under /lib" in r.stdout

@pytest.mark.parametrize("args, steps", [([], ["route_check.py", "check_new.py", "library_tests.py"]),
                                         (["--fetch"], ["fetch.py", "route_check.py", "check_new.py", "library_tests.py"])])
def test_library_tests_run_once_last_so_they_read_the_pages_just_downloaded(tmp_path, args, steps):
    bin_, log, envlog, call, fake = fake_python_with_pytest(tmp_path, pytest_out="1 passed in 1.00s\n")
    r = run_refresh(tmp_path, bin_, *args, JEV_SEMANTIC="off", JEV_LOG="on", JEV_CHECK="on", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    calls = log.read_text().splitlines()
    order = [next(i for i, c in enumerate(calls) if key in c) for key in steps]
    assert order == sorted(order) and order[-1] == len(calls) - 1
    assert sum("library_tests.py" in c for c in calls) == 1
    child = json.load(open(call))
    assert (child["env"]["JEV_LOG"], child["env"]["JEV_CHECK"]) == ("off", "off")
    assert child["env"]["JEV_SOURCES_DATA"] == str(tmp_path / "data")
    assert os.path.realpath(child["cwd"]) == os.path.realpath(CODE)

@pytest.mark.parametrize("args, script", [([], "check_new.py"), (["--fetch"], "fetch.py"), (["--fetch"], "check_new.py")])
def test_the_refresh_turns_the_step_off_inside_its_own_check_and_fetch(tmp_path, args, script):
    bin_, _, envlog, _, fake = fake_python_with_pytest(tmp_path, pytest_out="1 passed in 1.00s\n")
    r = run_refresh(tmp_path, bin_, *args, JEV_SEMANTIC="off", JEV_LIBRARY_TESTS="", PYTHONPATH=fake)
    assert r.returncode == 0, r.stderr
    lines = envlog.read_text().splitlines()
    assert next(l for l in lines if script in l).endswith("JEV_LIBRARY_TESTS=off")
    assert next(l for l in lines if "library_tests.py" in l).endswith("JEV_LIBRARY_TESTS=")  # and leaves it on for the step itself

def test_the_shell_no_longer_holds_the_test_logic():
    text = open(f"{CODE}/refresh.sh").read()
    assert "pytest" not in text and "library_tests()" not in text


def test_refresh_runs_its_python_checks_from_the_skill_folder_not_the_current_one(tmp_path):
    """python -c and python -m put the current folder first on the path, so a hostile project's model2vec.py or pip.py would run."""
    log = tmp_path / "cwd.log"
    bin_ = tmp_path / "bin"; bin_.mkdir()
    py = bin_ / "python3"
    py.write_text(f"""#!/bin/bash
case "$1" in
  -c) echo "$PWD" >> {log}; exec {sys.executable} "$@";;
  -m) echo "$PWD" >> {log}; exit 0;;
esac
exit 0
""")
    py.chmod(py.stat().st_mode | stat.S_IEXEC)
    hostile = tmp_path / "hostile"; hostile.mkdir()
    marker = tmp_path / "planted-ran"
    (hostile / "model2vec.py").write_text(f"open({str(marker)!r}, 'w').write('x')\n")
    e = dict(os.environ, PATH=f"{bin_}:{os.environ['PATH']}", JEV_SOURCES_DATA=str(tmp_path / "data"))
    e.pop("JEV_VAULT", None)
    r = subprocess.run(["bash", f"{CODE}/refresh.sh"], capture_output=True, text=True, env=e, cwd=hostile)
    assert r.returncode == 0, r.stderr
    assert not marker.exists()
    here = os.path.realpath(CODE)
    cwds = [os.path.realpath(l) for l in log.read_text().split()]
    assert cwds and all(c == here for c in cwds), cwds
