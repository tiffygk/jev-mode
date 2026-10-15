import json, os, shutil, subprocess, sys, tempfile
H = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")

def run(hook, payload, **env):
    """Every hook test gets its own data and log folders, so none touches the real library, starts a background
    check or carries state across tests. Tests that check logging pass JEV_LOG="on" and their own JEV_SOURCES_DATA."""
    tmp = tempfile.mkdtemp()
    e = {**os.environ, "JEV_SOURCES_DATA": tmp, "JEV_HOOK_LOG_DIR": tmp, "JEV_LOG": "off", "JEV_CHECK": "off", **env}
    r = subprocess.run([sys.executable, f"{H}/{hook}"], input=json.dumps(payload), capture_output=True, text=True, env=e)
    return json.loads(r.stdout) if r.stdout.strip() else None

def transcript(final_text, tool_inputs=()):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for inp in tool_inputs:
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": inp}]}}) + "\n")
    f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": final_text}]}}) + "\n")
    f.close(); return f.name

def test_reminder_fires_on_jev_question():
    out = run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?"})
    assert any(s in out["hookSpecificOutput"]["additionalContext"] for s in ("route.py", "jev.py"))

def test_reminder_quiet_on_folder_names_and_pasted_commands():
    """2026-10-08: the reminder fired on the repo's name and on a pasted settings command, never on a Jev question."""
    for p in ["Can you give me more information about the jev-mode-eval folder? We have a version of it on the repo.",
              "This folder is public; plans should go to the GitHub Jev mode Obsidian vault instead.",
              "cp ~/.claude/settings.json ~/.claude/settings.json.bak && jq -f ~/.claude/hooks/backups/jevaluate-runs.jq ~/.claude/settings.json > x",
              "]cp\n  ~/.claude/settings.json\n  -f ~/.claude/hooks/backups/jevaluate-runs.jq\n"]:
        assert run("jev-prompt-reminder.py", {"prompt": p}) is None, p
    assert run("jev-prompt-reminder.py", {"prompt": "Should Jev score these with a Choice question?"})
    assert run("jev-prompt-reminder.py", {"prompt": "rate this repo with jevaluate"})

def test_reminder_quiet_on_common_words():
    for p in ["make a choice of font", "what score did the deck get", "save the state of the app", "a cooking cookbook"]:
        assert run("jev-prompt-reminder.py", {"prompt": p}) is None, p

def test_dispatch_denied_without_block():
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review this Jev re-ranking design for errors."}})
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "JEV-SOURCES:" in out["hookSpecificOutput"]["permissionDecisionReason"]

def test_dispatch_allowed_with_block_or_not_jev():
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review this Jev design. JEV-SOURCES: read with route.py"}}) is None
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review the recipe cookbook layout."}}) is None

def test_dispatch_denies_jevaluate_brief():
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": "Run the jevaluate rubric on this repo."}})
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

def test_dispatch_allows_other_senses_of_typesafe_and_system_one():
    for p in ["Make the TypeScript API client typesafe and add zod validation.",
              "Summarize Kahneman: system one is fast and intuitive."]:
        assert run("jev-dispatch-check.py", {"tool_input": {"prompt": p}}) is None, p

def test_brief_and_reminder_name_this_install():
    root = os.path.dirname(H)
    out = run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?"})
    assert any(f"{root}/scripts/{s}" in out["hookSpecificOutput"]["additionalContext"] for s in ("route.py", "jev.py"))
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review this Jev design."}})
    assert f"{root}/scripts" in out["hookSpecificOutput"]["permissionDecisionReason"]

def test_symlinked_hook_names_the_real_install(tmp_path):
    for f in ("jev-prompt-reminder.py", "jev_terms.py"):
        os.symlink(os.path.join(H, f), tmp_path / f)
    iso = tempfile.mkdtemp()  # same isolated env as run(): the state prune must not touch the real data folder
    e = {**os.environ, "JEV_SOURCES_DATA": iso, "JEV_HOOK_LOG_DIR": iso, "JEV_LOG": "off", "JEV_CHECK": "off"}
    r = subprocess.run([sys.executable, str(tmp_path / "jev-prompt-reminder.py")], input=json.dumps({"prompt": "is a Noul right here?"}),
                       capture_output=True, text=True, env=e)
    root = os.path.dirname(os.path.realpath(H))
    ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
    assert any(f"{root}/scripts/{s}" in ctx for s in ("route.py", "jev.py"))


def test_dispatch_optout_with_reason_allowed():
    # 2026-10-06 replay: a copy edit of a CLAUDE.md that names Jev was refused.
    brief = "Stage 2 editor for one file. It is a copy edit: add no claims about Jev.\nNO-JEV-CLAIMS: copy edit only"
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": brief}}) is None

def test_dispatch_optout_needs_reason_and_own_line():
    for brief in ("Review this Jev design.\nNO-JEV-CLAIMS:", "Review this Jev design, NO-JEV-CLAIMS: x"):
        out = run("jev-dispatch-check.py", {"tool_input": {"prompt": brief}})
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny", brief

def test_dispatch_denial_names_optout():
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review this Jev design."}})
    assert "NO-JEV-CLAIMS" in out["hookSpecificOutput"]["permissionDecisionReason"]
# 2026-10-06 retro: the prompt reminder fired on 129 of 223 subagent hand-backs; the dispatch check refused briefs over path and plan names.
def test_prompt_reminder_skips_subagent_handback():
    p = '<agent-message from="ae71843ded3b0f02d">\n[Subagent hand-back] ... the Jev project ...'
    assert run("jev-prompt-reminder.py", {"prompt": p}) is None

def test_prompt_reminder_skips_task_notification():
    p = '<task-notification>\n<task-id>x</task-id> jevaluate-example-plan finished'
    assert run("jev-prompt-reminder.py", {"prompt": p}) is None

def test_prompt_reminder_still_fires_on_user_jev_message():
    out = run("jev-prompt-reminder.py", {"prompt": "Should this Jev integration batch the questions?"})
    assert out and "jev-sources" in out["hookSpecificOutput"]["additionalContext"]

def test_dispatch_allows_jev_word_only_in_a_path():
    b = "Count plans. Plan docs live under `~/notes/Jev Project/plans` and ~/work/Jev-mode/x.md."
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": b}}) is None

def test_dispatch_allows_jev_word_only_in_a_quoted_plan_name():
    b = 'Check the inflation on the plan "jevaluate-example-plan" by about 505k.'
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": b}}) is None

def test_dispatch_still_denies_jev_in_the_task():
    b = "Review whether this Jev integration sends each Noul in its own request."
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": b}})
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

def test_prompt_reminder_skips_handback_with_session_prefix():
    # Replay of a real 2026-10-06 transcript: hand-backs can arrive prefixed by this line.
    p = 'Another Claude session sent a message:\n<agent-message from="a011c59200f9062b3">\n[Subagent hand-back] the Jev rubric...'
    assert run("jev-prompt-reminder.py", {"prompt": p}) is None

def test_topic_text_is_fast_on_a_long_unclosed_quote():
    # Audit 2026-10-06: the quoted-identifier pattern backtracked quadratically (200k chars took 38 s), and this
    # check runs before every agent dispatch.
    import time
    sys.path.insert(0, H)
    from jev_terms import topic_text
    t = time.time(); topic_text('"' + "a-" * 100000); assert time.time() - t < 1

def test_dispatch_still_denies_jev_written_with_a_slash():
    # "Jev/TypeSafe" and "Jev/System One" name Jev, not a folder; dropping every slashed word let these through.
    for b in ["Rate how well this repo uses Jev/TypeSafe.", "Review the Jev/System One integration in app.py"]:
        out = run("jev-dispatch-check.py", {"tool_input": {"prompt": b}})
        assert out and out["hookSpecificOutput"]["permissionDecision"] == "deny", b

def test_dispatch_allows_jev_word_only_in_relative_paths():
    for b in ["Fix the typo in ~/Jev Study/notes.md", "Run the tests under jev-sources/hooks and report.",
              "Count the files in jevaluate/ and ratings/2026-10-06.md"]:
        assert run("jev-dispatch-check.py", {"tool_input": {"prompt": b}}) is None, b

def test_dispatch_allows_jev_in_the_middle_of_a_path_with_spaces():
    # Replay of real briefs: a path with spaces splits into pieces, and the middle piece "Notes/Jev" looks like a name pair.
    b = "Read ~/Documents/Study Notes/Jev Project/plan.md and count its headings."
    assert run("jev-dispatch-check.py", {"tool_input": {"prompt": b}}) is None


# 2026-10-08 security review of the folder-name rule.
def test_jev_model_and_modes_still_count():
    for p in ["What is the Jev model?", "Jev modes: which one fits?", "uses Jev,state.json for the cache"]:
        assert run("jev-prompt-reminder.py", {"prompt": p}), p
    out = run("jev-dispatch-check.py", {"tool_name": "Agent", "tool_input": {"prompt": "Review the Jev model and say whether it needs one call per passage."}})
    assert out and out["hookSpecificOutput"]["permissionDecision"] == "deny"

def test_folder_names_still_dropped():
    from jev_terms import topic_text, JEV
    for p in ["the jev-mode-eval folder", "jev-mode's README", "the GitHub Jev mode vault"]:
        assert not JEV.search(topic_text(p)), p

def test_reminder_ignores_a_non_text_prompt():
    assert run("jev-prompt-reminder.py", {"prompt": ["a"]}) is None


# Session state and decision logging.
def _lines(data, name):
    f = os.path.join(str(data), "logs", name + ".jsonl")
    return [json.loads(x) for x in open(f)] if os.path.exists(f) else []

def test_reminder_logs_fire_and_skip(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1", "cwd": "/w"}, **kw)
    assert run("jev-prompt-reminder.py", {"prompt": "fix the README table", "session_id": "s1", "cwd": "/w"}, **kw) is None
    a, b = _lines(tmp_path, "reminder")
    assert a["fire"] is True and a["reason"] == "jev_design" and a["session"] == "s1" and a["cwd"] == "/w"
    assert a["rule"] == "skip_continuations" and a["words"] == ["noul"] and a["chars"] == len("is a Noul right here?") and a["prompt"] == "is a Noul right here?"
    assert a["ts"].endswith("Z")
    assert b["fire"] is False and b["reason"] == "no_jev_word"

def test_reminder_without_session_logs_nothing(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?"}, **kw)
    assert not os.path.exists(tmp_path / "logs")

def test_non_text_prompt_logs_nothing(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-prompt-reminder.py", {"prompt": ["a"], "session_id": "s1"}, **kw) is None
    assert not os.path.exists(tmp_path / "logs")

def test_combined_rule_fires_once_then_repeat(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path), JEV_FIRE_RULE="combined")
    q = {"prompt": "does Jev batch questions?", "session_id": "s1"}
    assert run("jev-prompt-reminder.py", q, **kw)
    assert run("jev-prompt-reminder.py", q, **kw) is None
    assert [x["reason"] for x in _lines(tmp_path, "reminder")] == ["jev_design", "repeat"]

def test_corrupt_state_file_still_fires(tmp_path):
    import hashlib
    d = tmp_path / "logs" / "reminder_state"; d.mkdir(parents=True)
    (d / (hashlib.sha1(b"s1").hexdigest()[:16] + ".json")).write_text("{not json")
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1"}, **kw)

def test_dispatch_logs_not_jev_for_non_jev_brief(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-dispatch-check.py", {"session_id": "s1", "tool_input": {"prompt": "Review the recipe layout.", "description": "recipe review"}}, **kw) is None
    (x,) = _lines(tmp_path, "dispatch")
    assert x["decision"] == "not_jev" and x["session"] == "s1" and x["desc"] == "recipe review"

def test_dispatch_logs_deny_and_optout(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    run("jev-dispatch-check.py", {"session_id": "s1", "tool_input": {"prompt": "Review this Jev design."}}, **kw)
    run("jev-dispatch-check.py", {"session_id": "s1", "tool_input": {"prompt": "Review this Jev design.\nNO-JEV-CLAIMS: copy edit"}}, **kw)
    run("jev-dispatch-check.py", {"session_id": "s1", "tool_input": {"prompt": "Review this Jev design. JEV-SOURCES: x"}}, **kw)
    assert [x["decision"] for x in _lines(tmp_path, "dispatch")] == ["deny", "optout", "allow"]

def test_hostile_session_id_stays_inside_state_folder(tmp_path):
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path / "data"))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "../../x"}, **kw)
    files = [os.path.relpath(os.path.join(r, f), str(tmp_path)) for r, _, fs in os.walk(str(tmp_path)) for f in fs]
    state = [f for f in files if "reminder_state" in f]
    assert len(state) == 1 and state[0].startswith(os.path.join("data", "logs", "reminder_state") + os.sep)
    assert all(f.startswith("data" + os.sep) for f in files)

def test_unknown_rule_uses_default(tmp_path):
    out = run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1"}, JEV_FIRE_RULE="nonsense", JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert out
    assert _lines(tmp_path, "reminder")[0]["rule"] == "skip_continuations"

def test_unwritable_state_folder_still_prints(tmp_path):
    d = tmp_path / "logs" / "reminder_state"; d.mkdir(parents=True)
    d.chmod(0o500)
    try:
        out = run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1"}, JEV_SOURCES_DATA=str(tmp_path), JEV_LOG="on")
        assert out and any(s in out["hookSpecificOutput"]["additionalContext"] for s in ("route.py", "jev.py"))
    finally:
        d.chmod(0o700)

def test_default_rule_skips_a_continuation_summary():
    c = "This session is being continued from a previous conversation that ran out of context. Jev plans ..."
    assert run("jev-prompt-reminder.py", {"prompt": c, "session_id": "s1"}) is None

def test_hook_matches_step_over_a_session(tmp_path):
    """The six-prompt walk from test_firing.py::test_step_walks_a_session, through the real hook."""
    sys.path.insert(0, H)
    from firing import step
    prompts = ["does Jev batch questions?", "<task-notification> done", "fix the README table",
               "and does Jev cap tokens?", "is a Noul right here?", "is a Noul still right?"]
    kw = dict(JEV_FIRE_RULE="once_per_topic", JEV_SOURCES_DATA=str(tmp_path))
    state = {}
    for pr in prompts:
        fire, _, _, state = step(state, pr, "once_per_topic")
        assert bool(run("jev-prompt-reminder.py", {"prompt": pr, "session_id": "walk"}, **kw)) == fire, pr

def test_non_dict_json_payload_is_ignored():
    tmp = tempfile.mkdtemp()
    e = {**os.environ, "JEV_SOURCES_DATA": tmp, "JEV_HOOK_LOG_DIR": tmp, "JEV_LOG": "off", "JEV_CHECK": "off"}
    for hook in ("jev-prompt-reminder.py", "jev-dispatch-check.py"):
        r = subprocess.run([sys.executable, f"{H}/{hook}"], input="[]", capture_output=True, text=True, env=e)
        assert r.returncode == 0 and r.stdout == "" and "Traceback" not in r.stderr, hook

def test_fault_in_the_rule_never_errors_the_prompt(tmp_path):
    """A fault while picking the rule or reading state must exit 0 with no output, not a traceback."""
    e = {**os.environ, "JEV_SOURCES_DATA": str(tmp_path), "JEV_HOOK_LOG_DIR": str(tmp_path), "JEV_LOG": "off", "JEV_CHECK": "off"}
    d = tmp_path / "hooks"; d.mkdir()
    for f in ("jev-prompt-reminder.py", "jev_terms.py", "reminder_state.py"):
        shutil.copy(os.path.join(H, f), d / f)
    (d / "firing.py").write_text("RULES = ()\nDEFAULT_RULE = 'x'\ndef step(*a):\n    raise RuntimeError('boom')\n")
    r = subprocess.run([sys.executable, str(d / "jev-prompt-reminder.py")], input=json.dumps({"prompt": "is a Noul right here?"}),
                       capture_output=True, text=True, env=e)
    assert r.returncode == 0 and r.stdout == "" and "Traceback" not in r.stderr
