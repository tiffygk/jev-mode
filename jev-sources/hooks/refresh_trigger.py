"""Called by jev-prompt-reminder: starts scripts/check_new.py in the background when the last attempt is
CHECK_DAYS old, and returns the notice to show once. Never blocks, never raises."""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SCRIPT = os.environ.get("JEV_CHECK_SCRIPT") or os.path.join(HERE, "scripts", "check_new.py")
REFRESH = f"bash {os.path.join(HERE, 'refresh.sh')} --fetch"
try:  # the reminder imports this module, so a bad setting must not crash it
    CHECK_DAYS = float(os.environ.get("JEV_CHECK_DAYS") or 2)
except ValueError:
    CHECK_DAYS = 2.0
RETRY_HOURS = 6  # after a failed or running attempt, wait this long before another
WARN_DAYS = 7


def _data():
    return os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")


def _state():
    try:
        return json.load(open(os.path.join(_data(), "last_check.json")))
    except (OSError, ValueError):
        return {}


def maybe_start(now=None, popen=subprocess.Popen):
    """Starts a check when the last success is CHECK_DAYS old (or there is none), at most once per RETRY_HOURS."""
    try:
        if os.environ.get("JEV_CHECK") == "off":
            return False
        now = now or time.time()
        d, s = _data(), _state()
        if now - s.get("last_success", 0) < CHECK_DAYS * 86400:
            return False
        if now - s.get("last_attempt", 0) < RETRY_HOURS * 3600:
            return False
        os.makedirs(d, exist_ok=True)
        lock = os.path.join(d, "check.lock")
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))  # no check-then-create race
        except FileExistsError:
            if time.time() - os.path.getmtime(lock) < 3600:
                return False
            os.utime(lock)  # stale lock from a crashed run: take it over
        s["last_attempt"] = now
        with open(os.path.join(d, "last_check.json"), "w") as f:
            json.dump(s, f)
        popen([sys.executable, SCRIPT, "--locked"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL, start_new_session=True, cwd=d)
        return True
    except Exception:
        return False


def notice(now=None):
    try:
        if os.environ.get("JEV_CHECK") == "off":
            return ""  # tests and opt-outs never read or move the real NEW_PAGES.txt
        now = now or time.time()
        d, parts = _data(), []
        path = os.path.join(d, "NEW_PAGES.txt")
        try:
            text = open(path).read().strip()
        except OSError:
            text = ""
        if text:
            parts.append(text)
            os.makedirs(os.path.join(d, "notices"), exist_ok=True)
            os.replace(path, os.path.join(d, "notices", time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now)) + ".txt"))
        s = _state()
        ok, tried = s.get("last_success"), s.get("last_attempt")
        if (ok and now - ok > WARN_DAYS * 86400) or (not ok and tried and now - tried > 86400):
            when = time.strftime("%Y-%m-%d", time.gmtime(ok)) if ok else "never"
            parts.append(f"Jev Sources hasn't completed a check of TypeSafe's docs since {when}; run `{REFRESH}` and say if it fails.")
        return " ".join(parts)
    except Exception:
        return ""
