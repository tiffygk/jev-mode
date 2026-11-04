#!/usr/bin/env python3
"""Run the tests that read the live library, so a docs change that breaks them gets seen. Both ways docs changes
arrive use this: check_new.record_changes (the background check, and fetch.py) puts the result in the notice, and
refresh.sh prints it. It only reports, and never raises.
JEV_LIBRARY_TESTS=off skips it. Under pytest, record_changes skips it unless JEV_LIBRARY_TESTS=on."""
import os, signal, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CODE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TESTS = os.path.join(CODE, "tests")
FILES = ("test_applicability.py", "test_route.py", "test_index.py", "test_jev.py", "test_usage_log.py")
TIMEOUT = 300  # seconds; the run takes about 95
PROBE_TIMEOUT = 10  # seconds for the "is pytest installed" check; a hang counts as skipped
RERUN = f"python3 -m pytest {CODE}"  # names the skill's folder, so it runs the right tests from any project
NOTICE_PREFIX = "Library tests:"  # check_new keeps a line with this start ahead of its notice cap
NAMES_SHOWN, NAME_CAP, TEXT_CAP = 5, 150, 200  # together they keep the longest notice line under check_new.NOTICE_CAP


def _result(state, why="", names=(), summary="", written=()):
    return {"state": state, "why": why, "names": list(names), "summary": summary, "written": list(written)}


def _pytest_run(env, timeout):
    """Returns (exit code or None on a timeout, output). Output goes to a file and the run gets its own process group,
    so a test's leftover child can't hold this up and a timeout stops them all."""
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as out:
        p = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "--color=no", "--tb=no", "-rfE", "-p", "no:cacheprovider"] + [f"tests/{f}" for f in FILES],
                             cwd=CODE, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = p.wait(timeout)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            code = None
        out.seek(0)
        return code, out.read()


def run(timeout=None):
    """Runs the tests. Returns a dict whose state is passed, failed, written, skipped or unfinished."""
    timeout = TIMEOUT if timeout is None else timeout
    try:
        if os.environ.get("JEV_LIBRARY_TESTS") == "off":
            return _result("skipped", "JEV_LIBRARY_TESTS=off")
        if not os.path.isdir(TESTS):
            return _result("skipped", "no tests folder in this install")
        try:
            probe = subprocess.run([sys.executable, "-c", "import pytest"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, check=False, timeout=PROBE_TIMEOUT).returncode
        except subprocess.TimeoutExpired:
            return _result("skipped", "pytest did not answer in time")
        if probe != 0:
            return _result("skipped", "pytest is not installed")
        import paths
        env = dict(os.environ, JEV_CHECK="off", JEV_LOG="off", JEV_SOURCES_DATA=paths.DATA, JEV_LIBRARY_TESTS="off")
        env.pop("PYTEST_CURRENT_TEST", None)
        code, out = _pytest_run(env, timeout)
        lines = out.splitlines()
        last = lines[-1] if lines else ""
        written = [l for l in lines if l.startswith("LIBRARY WRITTEN")]
        if code is None:
            return _result("unfinished", f"timed out after {timeout}s", written=written)
        names = [l.split(" ", 1)[1].split(" - ", 1)[0] for l in lines if l.startswith(("FAILED ", "ERROR "))]
        if names:
            return _result("failed", names=names, summary=last, written=written)
        if code == 0:
            return _result("passed", summary=last, written=written)
        if code == 1 and written:  # every test passed; the suite's write guard is what failed the run
            return _result("written", summary=last, written=written)
        return _result("unfinished", f"pytest exit {code}", summary=last, written=written)
    except Exception as e:
        return _result("unfinished", type(e).__name__)


def report(r):
    """The lines a refresh prints."""
    if r["state"] == "skipped":
        return [f"library tests skipped: {r['why']}"]
    if r["state"] == "failed":
        lines = [f"library tests: {len(r['names'])} failed (a docs change may have broken them; run them with {RERUN}):"] + r["names"]
    elif r["state"] == "written":
        lines = [f"library tests: the suite wrote into the library (every test passed: {r['summary']})"]
    elif r["state"] == "passed":
        lines = [f"library tests: all passed ({r['summary']})"]
    else:
        lines = [f"library tests: could not finish ({r['why']})" + (f": {r['summary']}" if r["summary"] else "")]
    return lines + r["written"]


def notice(r):
    """The notice lines for a result: none when all passed or the run was skipped, so a stranger's install gets no noise."""
    if r["state"] == "failed":
        names = [n[:NAME_CAP] for n in r["names"][:NAMES_SHOWN]]
        more = len(r["names"]) - len(names)
        text = (f"{NOTICE_PREFIX} {len(r['names'])} failed (a docs change may have broken them; run them with {RERUN}): "
                f"{', '.join(names)}{f' and {more} more' if more else ''}.")
    elif r["state"] == "written":
        text = f"{NOTICE_PREFIX} the suite wrote into the library, though every test passed."
    elif r["state"] == "unfinished":
        text = f"{NOTICE_PREFIX} could not finish ({r['why']})" + (f": {r['summary'][:TEXT_CAP]}" if r["summary"] else "") + "."
    else:
        return []
    return [" ".join([text] + [w[:TEXT_CAP] for w in r["written"][:1]])]


def notice_lines():
    """Runs the tests for record_changes and returns its notice lines; a run under pytest needs JEV_LIBRARY_TESTS=on."""
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("JEV_LIBRARY_TESTS") != "on":
        return []
    return notice(run())


def main():
    for line in report(run()):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
