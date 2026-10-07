#!/usr/bin/env python3
"""PreToolUse (Agent): an agent brief about Jev must carry the JEV-SOURCES block, so the agent reads and cites sources.
A brief that mentions Jev but makes no claim about it (a copy edit, a question about other tooling) may instead carry
`NO-JEV-CLAIMS: <reason>`; each opt-out is logged so misuse shows up in the log (2026-10-06: three such briefs were refused)."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import JEV, MARKER, BRIEF, topic_text, log

OPTOUT = re.compile(r"^NO-JEV-CLAIMS:[ \t]*(\S.*)$", re.M)

def main():
    try:
        p = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = (p.get("tool_input") or {}).get("prompt") or ""
    if not JEV.search(topic_text(prompt)) or MARKER in prompt:
        return 0
    m = OPTOUT.search(prompt)
    if m:
        log("jev-dispatch-check", f"OPTOUT session={p.get('session_id')} reason={m.group(1).strip()[:100]!r}")
        return 0
    log("jev-dispatch-check", f"DENY session={p.get('session_id')} desc={(p.get('tool_input') or {}).get('description')!r}")
    reason = ("jev-dispatch-check: this agent brief is about Jev but has no source-reading block, so its findings "
              "would rest on memory. Add this line to the brief and dispatch again:\n" + BRIEF
              + "\nIf the agent makes no claim about Jev (a copy edit, a question about other tooling), add instead a line "
                "`NO-JEV-CLAIMS: <why>`.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
