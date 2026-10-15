import json, os, subprocess, sys
H = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")


def test_dispatch_refusal_asks_to_route_twice():
    """2026-10-14: a session routed a capability question once, in its own words, and missed the docs' term."""
    r = subprocess.run([sys.executable, os.path.join(H, "jev-dispatch-check.py")],
                       input=json.dumps({"tool_input": {"prompt": "Review this Jev re-ranking design for errors."}}),
                       capture_output=True, text=True)
    msg = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "twice" in msg and "in the docs' words" in msg


def test_skill_brief_line_matches_hook():
    sys.path.insert(0, H)
    import jev_terms
    skill = open(os.path.join(os.path.dirname(H), "SKILL.md"), encoding="utf-8").read()
    assert jev_terms.BRIEF.replace(jev_terms.ROOT, "<skill>") in skill


def test_brief_names_jev_py_and_every_label():
    sys.path.insert(0, H)
    import jev_terms
    b = jev_terms.BRIEF
    assert "scripts/jev.py" in b and "--docs-words" in b and "twice" in b
    assert all(l in b for l in ("reference rule", "pattern", "cookbook example", "sdk reference", "vendor claim"))


def test_reminder_text_names_jev_py_and_keeps_the_labels(tmp_path):
    root = os.path.dirname(os.path.realpath(H))
    env = dict(os.environ, JEV_SOURCES_DATA=str(tmp_path), JEV_LOG="off", JEV_CHECK="off")
    r = subprocess.run([sys.executable, os.path.join(H, "jev-prompt-reminder.py")], input=json.dumps({"prompt": "is a Noul right here?"}),
                       capture_output=True, text=True, env=env)
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert ctx == ("This message is about Jev/TypeSafe. Before any Jev claim or design call: load the jev-sources skill, run "
                   f"`python3 {root}/scripts/jev.py \"<the question>\" --docs-words \"<the same question in the docs' words>\"` "
                   "and read what it prints, unless those sections were already read in full this session. Keep each source's label "
                   "(reference rule, pattern, cookbook example, sdk reference, vendor claim) and say when a section is marked NEEDS or EXPERIMENTAL.")
