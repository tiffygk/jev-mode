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
