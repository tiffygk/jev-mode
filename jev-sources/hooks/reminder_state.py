"""Per-session state for the prompt reminder: how many prompts the session has sent and which Jev words fired when.
Lives in <data>/logs/reminder_state/<sha1(session)[:16]>.json. Nothing here raises: a failure means no state."""
import hashlib, json, os, time
from jev_terms import data_dir


def _dir():
    return os.path.join(data_dir(), "logs", "reminder_state")


def _path(sid):
    return os.path.join(_dir(), hashlib.sha1(str(sid).encode("utf-8")).hexdigest()[:16] + ".json")


def load(sid):
    default = {"n": 0, "fires": []}
    if sid is None:
        return default
    try:
        with open(_path(sid), encoding="utf-8") as f:
            st = json.load(f)
        fires = [[int(n), [str(w) for w in ws]] for n, ws in st["fires"]]
        return {"n": int(st["n"]), "fires": fires}
    except Exception:
        return default


def save(sid, st):
    if sid is None:
        return
    try:
        os.makedirs(data_dir(), mode=0o700, exist_ok=True)  # makedirs gives the mode to the last folder only
        os.makedirs(os.path.dirname(_dir()), mode=0o700, exist_ok=True)
        os.makedirs(_dir(), mode=0o700, exist_ok=True)
        st = {"n": st["n"], "fires": st["fires"][-50:]}
        path = _path(sid)
        tmp = path + ".%d.tmp" % os.getpid()
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
            json.dump(st, f)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass


def prune(days=7):
    cutoff = time.time() - days * 86400
    try:
        names = os.listdir(_dir())
    except Exception:
        return
    for name in names:  # one entry that can't be removed doesn't stop the rest
        try:
            p = os.path.join(_dir(), name)
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
        except Exception:
            pass
