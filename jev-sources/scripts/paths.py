"""Where the code and the downloaded pages live. Code sits beside this file; pages live in
$JEV_SOURCES_DATA (default ~/.claude/jev-sources-data), never inside the repo."""
import os, shlex

CODE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DATA = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
SCRIPTS = os.path.join(CODE, "scripts")
REFRESH = f"bash {shlex.quote(os.path.join(CODE, 'refresh.sh'))} --fetch"


def private_dirs(path):
    """Make path and every missing folder above it owner-only (os.makedirs gives its mode to the last folder only)."""
    missing = []
    p = os.path.abspath(path)
    while not os.path.isdir(p):
        missing.append(p)
        p = os.path.dirname(p)
    for d in reversed(missing):
        try:
            os.mkdir(d, 0o700)
        except FileExistsError:
            pass
    os.chmod(path, 0o700)
