import json, os, subprocess, sys, tempfile
H = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")

def run(hook, payload):
    r = subprocess.run([sys.executable, f"{H}/{hook}"], input=json.dumps(payload), capture_output=True, text=True)
    return json.loads(r.stdout) if r.stdout.strip() else None

def transcript(final_text, tool_inputs=()):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for inp in tool_inputs:
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": inp}]}}) + "\n")
    f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": final_text}]}}) + "\n")
    f.close(); return f.name

def test_reminder_fires_on_jev_question():
    out = run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?"})
    assert "route.py" in out["hookSpecificOutput"]["additionalContext"]

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
    assert f"{root}/scripts/route.py" in out["hookSpecificOutput"]["additionalContext"]
    out = run("jev-dispatch-check.py", {"tool_input": {"prompt": "Review this Jev design."}})
    assert f"{root}/scripts" in out["hookSpecificOutput"]["permissionDecisionReason"]

def test_symlinked_hook_names_the_real_install(tmp_path):
    for f in ("jev-prompt-reminder.py", "jev_terms.py"):
        os.symlink(os.path.join(H, f), tmp_path / f)
    r = subprocess.run([sys.executable, str(tmp_path / "jev-prompt-reminder.py")], input=json.dumps({"prompt": "is a Noul right here?"}),
                       capture_output=True, text=True)
    root = os.path.dirname(os.path.realpath(H))
    assert f"{root}/scripts/route.py" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


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
