#!/usr/bin/env python3
"""UserPromptSubmit: when a message is about Jev, tell the model to read the sources first. Never blocks."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import JEV, ROOT, HANDBACK, log

def main():
    try:
        p = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = p.get("prompt") or ""
    if HANDBACK.search(prompt) or not JEV.search(prompt):
        return 0
    log("jev-prompt-reminder", f"FIRE session={p.get('session_id')} prompt={prompt[:80]!r}")
    ctx = ("This message is about Jev/TypeSafe. Before any Jev claim or design call: load the `jev-sources` skill, "
           f"run `python3 {ROOT}/scripts/route.py \"<the question>\"`, and read every READ FULL item "
           "with read.py, unless those sections were already read in full this session. Label each source as a "
           "reference rule or a cookbook example.")
    try:  # weekly check_new.py result; empty when the library matches TypeSafe's page list
        notice = open(os.path.join(os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data"), "NEW_PAGES.txt")).read().strip()
    except OSError:
        notice = ""
    if notice:
        ctx += " Tell the user: " + notice
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
