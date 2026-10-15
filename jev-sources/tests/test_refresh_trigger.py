import importlib, json, os, subprocess, sys, time
import pytest
HOOKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
sys.path.insert(0, HOOKS)
DAY, HOUR = 86400, 3600


@pytest.fixture
def trig(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.delenv("JEV_CHECK", raising=False)
    monkeypatch.delenv("JEV_CHECK_SCRIPT", raising=False)
    import refresh_trigger
    mod = importlib.reload(refresh_trigger)
    yield mod
    monkeypatch.undo()  # put the env back, then reload so no other test sees this tmp_path
    importlib.reload(mod)


class Popen:
    def __init__(self):
        self.calls = []

    def __call__(self, args, **kw):
        self.calls.append(args)


def state(tmp_path, **kv):
    (tmp_path / "last_check.json").write_text(json.dumps(kv))


def test_success_three_days_old_starts_locked_check(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_success=now - 3 * DAY)
    p = Popen()
    assert trig.maybe_start(now=now, popen=p) is True
    assert "--locked" in p.calls[0] and p.calls[0][1] == trig.SCRIPT


def test_success_one_day_old_does_not_start(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_success=now - 1 * DAY)
    p = Popen()
    assert trig.maybe_start(now=now, popen=p) is False
    assert p.calls == []


def test_no_success_starts_a_check(trig, tmp_path):
    p = Popen()
    assert trig.maybe_start(now=time.time(), popen=p) is True
    assert len(p.calls) == 1


def test_failed_attempt_two_hours_ago_blocks_retry(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_attempt=now - 2 * HOUR)
    p = Popen()
    assert trig.maybe_start(now=now, popen=p) is False
    assert p.calls == []


def test_failed_attempt_seven_hours_ago_allows_retry(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_attempt=now - 7 * HOUR)
    p = Popen()
    assert trig.maybe_start(now=now, popen=p) is True
    assert len(p.calls) == 1


def test_fresh_lock_blocks_start(trig, tmp_path):
    (tmp_path / "check.lock").write_text("")
    p = Popen()
    assert trig.maybe_start(now=time.time(), popen=p) is False
    assert p.calls == []


def test_two_hour_old_lock_is_taken_over(trig, tmp_path):
    lock = tmp_path / "check.lock"
    lock.write_text("")
    old = time.time() - 2 * HOUR
    os.utime(lock, (old, old))
    p = Popen()
    assert trig.maybe_start(now=time.time(), popen=p) is True
    assert len(p.calls) == 1


def test_jev_check_off_never_starts(trig, tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_CHECK", "off")
    p = Popen()
    assert trig.maybe_start(now=time.time(), popen=p) is False
    assert p.calls == []


def test_notice_returns_new_pages_once_and_archives_it(trig, tmp_path):
    (tmp_path / "NEW_PAGES.txt").write_text("TypeSafe added 1 page(s): models.\n")
    assert trig.notice() == "TypeSafe added 1 page(s): models."
    assert not (tmp_path / "NEW_PAGES.txt").exists()
    assert len(list((tmp_path / "notices").glob("*.txt"))) == 1
    assert trig.notice() == ""


def test_success_eight_days_old_warns(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_success=now - 8 * DAY)
    text = trig.notice(now=now)
    assert "hasn't completed a check" in text


def test_success_three_days_old_does_not_warn(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_success=now - 3 * DAY)
    assert trig.notice(now=now) == ""


def test_no_success_with_attempt_two_days_old_warns(trig, tmp_path):
    now = time.time()
    state(tmp_path, last_attempt=now - 2 * DAY)
    assert "hasn't completed a check" in trig.notice(now=now)


def test_exception_inside_returns_false_and_empty(trig, tmp_path, monkeypatch):
    blocker = tmp_path / "blocked"
    blocker.write_text("a file, so the data folder can't be created")
    monkeypatch.setenv("JEV_SOURCES_DATA", str(blocker / "data"))
    assert trig.maybe_start(now=time.time(), popen=Popen()) is False
    assert trig.notice() == ""


def run_hook(tmp_path, env_extra, prompt="is a Noul right for one request?"):
    noop = tmp_path / "noop_check.py"  # the hook may start a check; this stands in for it and does nothing
    noop.write_text("")
    env = dict(os.environ, JEV_SOURCES_DATA=str(tmp_path), JEV_LOG="off", JEV_CHECK_SCRIPT=str(noop))
    env.pop("JEV_CHECK", None)
    env.update(env_extra)
    import json as j
    start = time.time()
    r = subprocess.run([sys.executable, os.path.join(HOOKS, "jev-prompt-reminder.py")], input=j.dumps({"prompt": prompt}),
                       capture_output=True, text=True, env=env, timeout=30)
    return time.time() - start, j.loads(r.stdout) if r.stdout.strip() else None


def test_hook_returns_fast_with_slow_check_and_still_reminds(tmp_path):
    slow = tmp_path / "slow_check.py"
    slow.write_text("import time\ntime.sleep(5)\n")
    elapsed, out = run_hook(tmp_path, {"JEV_CHECK_SCRIPT": str(slow)})
    assert elapsed < 2
    assert "jev.py" in out["hookSpecificOutput"]["additionalContext"]


def test_hook_shows_waiting_notice_once(tmp_path):
    (tmp_path / "NEW_PAGES.txt").write_text("TypeSafe added 1 page(s): models.\n")
    env = {}
    _, first = run_hook(tmp_path, env)
    assert "TypeSafe added 1 page(s): models." in first["hookSpecificOutput"]["additionalContext"]
    _, second = run_hook(tmp_path, env)
    assert "TypeSafe added" not in second["hookSpecificOutput"]["additionalContext"]


def test_notice_is_empty_and_leaves_pages_file_when_checks_are_off(trig, tmp_path, monkeypatch):
    (tmp_path / "NEW_PAGES.txt").write_text("TypeSafe added 1 page(s): models.\n")
    monkeypatch.setenv("JEV_CHECK", "off")
    assert trig.notice() == ""
    assert (tmp_path / "NEW_PAGES.txt").exists()
    assert not (tmp_path / "notices").exists()


def test_a_bad_check_days_setting_falls_back_to_two(trig, monkeypatch):
    monkeypatch.setenv("JEV_CHECK_DAYS", "abc")
    mod = importlib.reload(trig)  # the reminder imports this module; a crash here would lose the reminder
    assert mod.CHECK_DAYS == 2
