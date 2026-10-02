#!/usr/bin/env python3
"""PreToolUse (Agent): an agent brief about Jev must carry the JEV-SOURCES block, so the agent reads and cites sources."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import JEV, MARKER, BRIEF, log

def main():
    try:
        p = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = (p.get("tool_input") or {}).get("prompt") or ""
    if not JEV.search(prompt) or MARKER in prompt:
        return 0
    log("jev-dispatch-check", f"DENY session={p.get('session_id')} desc={(p.get('tool_input') or {}).get('description')!r}")
    reason = ("jev-dispatch-check: this agent brief is about Jev but has no source-reading block, so its findings "
              "would rest on memory. Add this line to the brief and dispatch again:\n" + BRIEF)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
