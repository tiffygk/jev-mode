"""The step that runs the tests reading the live library, on both paths that bring in docs changes. pytest is a
stand-in on PYTHONPATH that logs how it was called, so nothing here runs the real suite."""
import importlib, json, os, sys, time
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
T = "tests/test_route.py::test_"
LONG = "x" * 600


@pytest.fixture
def env(tmp_path, monkeypatch):
    """check_new on an empty temp library, with the routing, applicability and citation checks stood in for by one line."""
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.delenv("JEV_LIBRARY_TESTS", raising=False)
    import paths, pages, blog, check_new
    for m in (paths, pages, blog, check_new):
        importlib.reload(m)
    monkeypatch.setattr(check_new, "after_change", lambda res: ["routing line"])
    yield check_new
    monkeypatch.undo()
    for m in (paths, pages, blog, check_new):
        importlib.reload(m)


def fake_pytest(tmp_path, monkeypatch, out="", code=0, broken=False, body=""):
    """A pytest module on PYTHONPATH. Returns the path it logs to, which exists only once it has run."""
    d = tmp_path / "fake"
    d.mkdir()
    log = tmp_path / "pytest-call.json"
    text = "raise ImportError('no pytest')\n" if broken else f"""
import json, os, subprocess, sys, time
if __name__ == "__main__":
    json.dump({{"argv": sys.argv[1:], "cwd": os.getcwd(), "env": dict(os.environ)}}, open({str(log)!r}, "w"))
    {body or "pass"}
    sys.stdout.write({out!r})
    sys.stdout.flush()
    sys.exit({code})
"""
    (d / "pytest.py").write_text(text)
    monkeypatch.setenv("PYTHONPATH", str(d))
    return log


def failing(n):
    return "..F\n" + "".join(f"FAILED {T}{i} - AssertionError: x\n" for i in range(n)) + f"{n} failed in 1.00s\n"


def changes(cn):
    return cn.record_changes({"changed": ["models"], "added": [], "removed": [], "moved": {}, "removed_sections": [], "added_sections": []},
                             cn.pages.datetime.datetime(2026, 11, 4, tzinfo=cn.pages.UTC), False, None)


def test_failures_reach_the_notice_after_the_other_checks(env, tmp_path, monkeypatch):
    fake_pytest(tmp_path, monkeypatch, failing(2), 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    lines = changes(env)
    assert lines[0] == "routing line" and len(lines) == 2
    assert lines[1].startswith("Library tests: 2 failed")
    assert f"{T}0" in lines[1] and f"{T}1" in lines[1] and "more" not in lines[1] and "AssertionError" not in lines[1]


def test_the_notice_names_five_failures_and_counts_the_rest(env, tmp_path, monkeypatch):
    fake_pytest(tmp_path, monkeypatch, failing(7), 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    line = changes(env)[-1]
    assert line.startswith("Library tests: 7 failed") and "and 2 more" in line
    assert f"{T}4" in line and f"{T}5" not in line


def test_all_passing_adds_nothing_to_the_notice(env, tmp_path, monkeypatch):
    log = fake_pytest(tmp_path, monkeypatch, "...\n3 passed in 1.00s\n")
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    assert changes(env) == ["routing line"]
    assert log.exists()  # it did run


def test_a_missing_pytest_adds_nothing_to_the_notice(env, tmp_path, monkeypatch):
    fake_pytest(tmp_path, monkeypatch, broken=True)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    assert changes(env) == ["routing line"]


def test_a_missing_tests_folder_adds_nothing_to_the_notice(env, tmp_path, monkeypatch):
    import library_tests
    log = fake_pytest(tmp_path, monkeypatch, failing(1), 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    monkeypatch.setattr(library_tests, "TESTS", str(tmp_path / "nowhere"))
    assert changes(env) == ["routing line"]
    assert not log.exists()


def test_a_run_that_cannot_finish_reaches_the_notice(env, tmp_path, monkeypatch):
    fake_pytest(tmp_path, monkeypatch, "ERROR: file or directory not found: tests/x.py\n", 4)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    assert "could not finish (pytest exit 4)" in changes(env)[-1]


def test_a_library_written_by_the_tests_reaches_the_notice(env, tmp_path, monkeypatch):
    fake_pytest(tmp_path, monkeypatch, "LIBRARY WRITTEN BY THE SUITE: docs changed under /lib\n3 passed in 1.00s\n", 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    assert "LIBRARY WRITTEN BY THE SUITE: docs changed under /lib" in changes(env)[-1]


def test_the_off_switch_skips_the_run(env, tmp_path, monkeypatch):
    log = fake_pytest(tmp_path, monkeypatch, failing(1), 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "off")
    monkeypatch.delenv("PYTEST_CURRENT_TEST")  # as in the background check, so the pytest guard can't be what skips it
    assert changes(env) == ["routing line"]
    assert not log.exists()


def test_under_pytest_it_does_not_run_unless_asked(env, tmp_path, monkeypatch):
    log = fake_pytest(tmp_path, monkeypatch, failing(1), 1)
    assert os.environ.get("PYTEST_CURRENT_TEST")
    assert changes(env) == ["routing line"]
    assert not log.exists()


def test_the_child_run_cannot_start_another_refresh_or_log_questions(env, tmp_path, monkeypatch):
    log = fake_pytest(tmp_path, monkeypatch, "1 passed in 1.00s\n")
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    monkeypatch.setenv("JEV_CHECK", "on")  # conftest turns these off for every test; the step must turn them off itself
    monkeypatch.setenv("JEV_LOG", "on")
    changes(env)
    child = json.load(open(log))["env"]
    assert child["JEV_CHECK"] == "off"
    assert child["JEV_LOG"] == "off"


def test_the_child_run_reads_the_library_and_cannot_recurse(env, tmp_path, monkeypatch):
    log = fake_pytest(tmp_path, monkeypatch, "1 passed in 1.00s\n")
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    changes(env)
    call = json.load(open(log))
    assert call["env"]["JEV_SOURCES_DATA"] == str(tmp_path / "data")
    assert call["env"]["JEV_LIBRARY_TESTS"] == "off"
    assert "PYTEST_CURRENT_TEST" not in call["env"]
    assert os.path.realpath(call["cwd"]) == os.path.realpath(CODE)


def test_the_helper_runs_only_the_files_that_read_the_library(env, tmp_path, monkeypatch):
    import library_tests
    log = fake_pytest(tmp_path, monkeypatch, "1 passed in 1.00s\n")
    library_tests.run()
    named = [a for a in json.load(open(log))["argv"] if a.startswith("tests/")]
    assert sorted(named) == sorted(f"tests/test_{n}.py" for n in ("applicability", "route", "index", "jev", "usage_log"))
    assert all(os.path.exists(os.path.join(CODE, f)) for f in named)


def test_a_timeout_is_reported_and_leaves_nothing_running(env, tmp_path, monkeypatch):
    import library_tests
    marker = tmp_path / "grandchild-alive"
    # a grandchild keeps the output open: a helper that reads pytest through a pipe would wait for it
    child = f"import time; time.sleep(4); open({str(marker)!r}, 'w').close()"
    fake_pytest(tmp_path, monkeypatch, body=f"subprocess.Popen([sys.executable, '-c', {child!r}]); time.sleep(60)")
    start = time.time()
    r = library_tests.run(timeout=1)
    assert time.time() - start < 3.5
    assert r["state"] == "unfinished" and "timed out after 1s" in library_tests.report(r)[0]
    assert library_tests.report(r)[0].startswith("library tests: could not finish")
    time.sleep(4)
    assert not marker.exists()


def test_a_timeout_reaches_the_notice(env, tmp_path, monkeypatch):
    import library_tests
    fake_pytest(tmp_path, monkeypatch, body="time.sleep(60)")
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    monkeypatch.setattr(library_tests, "TIMEOUT", 1)
    assert "could not finish (timed out after 1s)" in changes(env)[-1]


def test_the_helper_never_raises_when_it_cannot_start(env, monkeypatch, capsys):
    import library_tests
    def boom(*a, **k):
        raise OSError("no such python")
    monkeypatch.setattr(library_tests.subprocess, "run", boom)
    monkeypatch.setattr(library_tests.subprocess, "Popen", boom)
    assert library_tests.run()["state"] == "unfinished"
    assert library_tests.main() == 0
    assert "could not finish" in capsys.readouterr().out


def test_the_helper_main_prints_the_skip_reasons_and_exits_0(env, tmp_path, monkeypatch, capsys):
    import library_tests
    fake_pytest(tmp_path, monkeypatch, broken=True)
    assert library_tests.main() == 0
    assert capsys.readouterr().out == "library tests skipped: pytest is not installed\n"
    monkeypatch.setattr(library_tests, "TESTS", str(tmp_path / "nowhere"))
    assert library_tests.main() == 0
    assert capsys.readouterr().out == "library tests skipped: no tests folder in this install\n"
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "off")
    assert library_tests.main() == 0
    assert capsys.readouterr().out == "library tests skipped: JEV_LIBRARY_TESTS=off\n"


def test_the_longest_line_fits_the_notice_cap(env, tmp_path, monkeypatch):
    out = "".join(f"FAILED {T}{i}{LONG} - x\n" for i in range(9)) + f"LIBRARY WRITTEN BY THE SUITE: {LONG}\n"
    fake_pytest(tmp_path, monkeypatch, out, 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    line = changes(env)[-1]
    assert len(line) < env.NOTICE_CAP
    assert line.startswith("Library tests: 9 failed") and "and 4 more" in line and "LIBRARY WRITTEN" in line


def test_the_count_survives_a_notice_full_of_page_names(env):
    import library_tests
    parts = [f"TypeSafe changed 12 page(s): {LONG}.", f"TypeSafe added 12 page(s): {LONG}.", f"TypeSafe removed 12 page(s): {LONG}."]
    text = env.notice_text(parts, ["routing line", f"{library_tests.NOTICE_PREFIX} 3 failed"])
    assert text.startswith(f"{library_tests.NOTICE_PREFIX} 3 failed")
    assert len(text) == env.NOTICE_CAP


def test_the_message_names_this_installs_folder(env, tmp_path, monkeypatch):
    import library_tests
    fake_pytest(tmp_path, monkeypatch, failing(1), 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    assert f"python3 -m pytest {CODE}" in changes(env)[-1]
    r = library_tests.run()
    assert f"python3 -m pytest {CODE}" in library_tests.report(r)[0]


def test_every_test_passing_but_the_library_written_leads_with_the_library(env, tmp_path, monkeypatch):
    import library_tests
    fake_pytest(tmp_path, monkeypatch, "...\nLIBRARY WRITTEN BY THE SUITE: docs changed under /lib\n3 passed in 1.00s\n", 1)
    monkeypatch.setenv("JEV_LIBRARY_TESTS", "on")
    r = library_tests.run()
    assert r["state"] == "written"
    assert library_tests.report(r)[0].startswith("library tests: the suite wrote into the library")
    assert "could not finish" not in " ".join(library_tests.report(r))
    line = changes(env)[-1]
    assert line.startswith("Library tests: the suite wrote into the library") and "could not finish" not in line
    assert "LIBRARY WRITTEN BY THE SUITE: docs changed under /lib" in line and len(line) < env.NOTICE_CAP


def test_a_failing_name_with_a_written_library_is_still_a_failure(env, tmp_path, monkeypatch):
    import library_tests
    fake_pytest(tmp_path, monkeypatch, failing(1) + "LIBRARY WRITTEN BY THE SUITE: x\n", 1)
    assert library_tests.run()["state"] == "failed"


def test_the_pytest_probe_has_a_short_timeout_and_a_timeout_counts_as_skipped(env, monkeypatch):
    import library_tests
    seen = {}
    def slow(*a, **k):
        seen.update(k)
        raise library_tests.subprocess.TimeoutExpired("python3", k.get("timeout"))
    monkeypatch.setattr(library_tests.subprocess, "run", slow)
    r = library_tests.run()
    assert seen.get("timeout") == 10
    assert r["state"] == "skipped" and "pytest" in r["why"]


def test_pytest_is_called_without_color_so_failing_names_stay_plain(env, tmp_path, monkeypatch):
    import library_tests
    log = fake_pytest(tmp_path, monkeypatch, "1 passed in 1.00s\n")
    monkeypatch.setenv("FORCE_COLOR", "1")
    library_tests.run()
    assert "--color=no" in json.load(open(log))["argv"]


def test_the_child_run_is_offline_and_reads_models_under_the_data_folder(monkeypatch):
    import library_tests, paths
    monkeypatch.delenv("HF_HOME", raising=False)
    env = library_tests.child_env()
    assert env["HF_HUB_OFFLINE"] == "1"
    assert env["HF_HOME"] == os.path.join(paths.DATA, "models")


def test_the_child_run_keeps_a_preset_hf_home_and_still_goes_offline(monkeypatch):
    import library_tests
    monkeypatch.setenv("HF_HOME", "/somewhere/else")
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    env = library_tests.child_env()
    assert env["HF_HOME"] == "/somewhere/else" and env["HF_HUB_OFFLINE"] == "1"
