#!/usr/bin/env python3
"""UserPromptSubmit: when a message is about Jev, tell the model to read the sources first. Never blocks."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import ROOT, BUILD_LINE, log, log_event
import firing, reminder_state

def main():
    try:
        p = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(p, dict):
        return 0
    prompt = p.get("prompt") or ""
    if not isinstance(prompt, str):
        return 0
    try:  # a fault in the rule or the state must never error the prompt
        # firing.jev_words reads topic_text, which drops paths, file names and the repo's folder name.
        rule = os.environ.get("JEV_FIRE_RULE")
        rule = rule if rule in firing.RULES else firing.DEFAULT_RULE
        sid = p.get("session_id")
        before = reminder_state.load(sid)
        fire, reason, words, st = firing.step(before, prompt, rule)  # the same function score_rules.py walks
        # a build word beside a Jev word in reach adds BUILD_LINE, and fires the reminder when no Jev word is in the message
        build = firing.build_line(prompt, p.get("permission_mode"), firing.recent_words(before))
        if build and not fire:
            fire, reason = True, "build_line"
        reminder_state.save(sid, st)
        reminder_state.prune()
        log_event("reminder", session=sid, cwd=p.get("cwd"), fire=fire, reason=reason, rule=rule, words=words, build=build, chars=len(prompt), prompt=prompt[:120])
    except Exception:
        return 0
    if not fire:
        return 0
    log("jev-prompt-reminder", f"FIRE session={p.get('session_id')} prompt={prompt[:80]!r}")
    ctx = ("This message is about Jev/TypeSafe. Before any Jev claim or design call: load the jev-sources skill, "
           f"run `python3 {ROOT}/scripts/jev.py \"<the question>\" --docs-words \"<the same question in the docs' words>\"` "
           "and read what it prints, unless those sections were already read in full this session. Keep each source's "
           "label (reference rule, pattern, cookbook example, sdk reference, vendor claim) and say when a section is "
           "marked NEEDS or EXPERIMENTAL.")
    if build:
        ctx += BUILD_LINE
    import refresh_trigger  # background docs check every JEV_CHECK_DAYS, and its notice (shown once)
    refresh_trigger.maybe_start()
    notice = refresh_trigger.notice()
    if notice:
        ctx += " Tell the user: " + notice
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
