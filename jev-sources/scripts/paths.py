"""Where the code and the downloaded pages live. Code sits beside this file; pages live in
$JEV_SOURCES_DATA (default ~/.claude/jev-sources-data), never inside the repo."""
import os, shlex

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
SCRIPTS = os.path.join(CODE, "scripts")
REFRESH = f"bash {shlex.quote(os.path.join(CODE, 'refresh.sh'))} --fetch"
