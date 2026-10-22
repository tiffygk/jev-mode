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

def test_logs_and_state_are_owner_only_and_fields_capped(tmp_path):
    import stat
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(tmp_path))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s" * 5000, "cwd": "/w" * 5000}, **kw)
    logs = tmp_path / "logs"
    for p in (logs, logs / "reminder.jsonl", logs / "reminder_state", next((logs / "reminder_state").iterdir())):
        assert stat.S_IMODE(os.stat(p).st_mode) & 0o077 == 0, p
    (x,) = _lines(tmp_path, "reminder")
    assert len(x["session"]) == 300 and len(x["cwd"]) == 300

def test_logs_made_by_an_older_version_are_locked_on_the_next_write(tmp_path):
    import stat
    data = tmp_path / "data"  # not there yet: the hook makes it owner-only
    logs = data / "logs"
    kw = dict(JEV_LOG="on", JEV_SOURCES_DATA=str(data))
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1", "cwd": "/w"}, **kw)
    assert stat.S_IMODE(os.stat(data).st_mode) & 0o077 == 0
    os.chmod(logs, 0o755); os.chmod(logs / "reminder.jsonl", 0o644)  # as an older version left them
    assert run("jev-prompt-reminder.py", {"prompt": "is a Noul right here?", "session_id": "s1", "cwd": "/w"}, **kw)
    for p in (logs, logs / "reminder.jsonl"):
        assert stat.S_IMODE(os.stat(p).st_mode) & 0o077 == 0, p

def test_state_prune_skips_an_entry_it_cannot_remove(tmp_path, monkeypatch):
    sys.path.insert(0, H)
    import reminder_state
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    d = tmp_path / "logs" / "reminder_state"; d.mkdir(parents=True)
    (d / "a-stuck").mkdir()  # os.remove fails on a folder
    old = d / "b-old.json"; old.write_text("{}")
    for p in (d / "a-stuck", old):
        os.utime(p, (0, 0))
    monkeypatch.setattr(reminder_state.os, "listdir", lambda _: ["a-stuck", "b-old.json"])  # the stuck one first
    reminder_state.prune()
    assert not old.exists() and (d / "a-stuck").exists()

def test_state_save_leaves_no_temp_file_when_replace_fails(tmp_path, monkeypatch):
    sys.path.insert(0, H)
    import reminder_state
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    os.makedirs(reminder_state._path("s1"))  # a folder where the state file goes: os.replace fails
    reminder_state.save("s1", {"n": 1, "fires": []})
    assert sorted(os.listdir(reminder_state._dir())) == [os.path.basename(reminder_state._path("s1"))]


# --- jev-reader-check.py (SubagentStop) ---------------------------------------------------------------------------
READER_PID = "p1a2b3c4d"
R_ALPHA = "Alpha holds the first secret rule: every box answers within five seconds."
R_BETA = "Beta holds the other rule: a state carries at most nine fields."
R_PAGES = {"docs/one.md": f"# One\n\nIntro.\n\n## Alpha\n\n{R_ALPHA}\n\n## Beta\n\n{R_BETA}\n"}
GOOD = 'FINDING: A rule. | CITE AS: docs/one.md#Alpha (reference rule) | QUOTE: "every box answers within five seconds"'
BAD = 'FINDING: A rule. | CITE AS: docs/one.md#Alpha (reference rule) | QUOTE: "every box answers within five minutes"'


def reader_lib(tmp_path, monkeypatch, with_plan=True):
    """An invented library and a saved reading plan with one batch holding both sections."""
    data = tmp_path / "data"
    for p, text in R_PAGES.items():
        (data / p).parent.mkdir(parents=True, exist_ok=True)
        (data / p).write_text(text)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.syspath_prepend(os.path.join(os.path.dirname(H), "scripts"))
    for n in ("paths", "build_index", "route", "read", "check_findings", "usage_log", "applicability"):
        sys.modules.pop(n, None)
    import build_index
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    build_index.main()
    ids = [r["id"] for r in map(json.loads, open(data / "sections.jsonl"))]
    if with_plan:
        (data / "plans").mkdir(exist_ok=True)
        (data / "plans" / (READER_PID + ".json")).write_text(json.dumps(
            {"plan_id": READER_PID, "created": "2026-10-20T10:00:00Z", "goal": ["g"],
             "batches": [{"n": 1, "ids": ids, "tokens": 100}]}))
    return data


def reader_run(data, message, agent_id="a1", session="s1", raw=None, **env):
    """(exit code, parsed stdout or None) for one SubagentStop call; the hook's log and state land in `data`."""
    e = {**os.environ, "JEV_SOURCES_DATA": str(data), "JEV_HOOK_LOG_DIR": str(data), "JEV_LOG": "on", "JEV_SEMANTIC": "off", **env}
    payload = raw if raw is not None else json.dumps({"session_id": session, "agent_id": agent_id, "last_assistant_message": message})
    r = subprocess.run([sys.executable, f"{H}/jev-reader-check.py"], input=payload, capture_output=True, text=True, env=e)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None)


def head(n=1, pid=READER_PID):
    return f"JEV-READER: plan {pid} batch {n}\n"


def test_reader_bad_quote_blocks_with_that_line(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, head() + BAD + "\n")
    assert code == 0 and set(out) == {"decision", "reason"} and out["decision"] == "block"
    assert "QUOTE NOT FOUND | b1 | docs/one.md#Alpha (reference rule)" in out["reason"]
    assert out["reason"].rstrip().endswith("fix these lines and reply again, starting with the JEV-READER line")

def test_reader_clean_reply_passes_with_no_output(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, head() + GOOD + "\n") == (0, None)

def test_reader_second_stop_of_same_agent_is_let_through_and_logged(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, head() + BAD + "\n")[1]["decision"] == "block"
    assert reader_run(data, head() + BAD + "\n") == (0, None)
    assert [x["decision"] for x in _lines(data, "reader_check")] == ["block", "loop_guard"]
    assert reader_run(data, head() + BAD + "\n", agent_id="a2")[1]["decision"] == "block"  # another agent is checked afresh

def test_reader_ignores_a_reply_without_the_reader_line(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, "Here are my notes.\nThe docs cover limits.\n") == (0, None)
    assert reader_run(data, "") == (0, None)
    assert not (data / "logs" / "reader_check.jsonl").exists()

def test_reader_finding_lines_with_no_header_block_once(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, GOOD + "\n")
    assert code == 0 and out["decision"] == "block" and out["reason"].startswith("NO HEADER")
    assert reader_run(data, GOOD + "\n") == (0, None)  # loop guard

def test_reader_header_after_a_short_preamble_is_checked(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, "Here are my findings.\n" + head() + BAD + "\n")[1]["decision"] == "block"
    assert reader_run(data, "Here are my findings.\n" + head() + GOOD + "\n", agent_id="a9") == (0, None)

def test_reader_line_may_follow_blank_lines(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, "\n\n" + head() + BAD + "\n")[1]["decision"] == "block"

def test_reader_malformed_input_exits_0_and_logs(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    for raw in ("not json", "[1, 2]", json.dumps({"last_assistant_message": 5, "agent_id": "a1"})):
        assert reader_run(data, "", raw=raw) == (0, None), raw
    assert reader_run(data, head() + BAD, raw=json.dumps({"last_assistant_message": head() + BAD})) == (0, None)  # no agent_id
    decisions = [x["decision"] for x in _lines(data, "reader_check")]
    assert decisions and set(decisions) == {"error"}

def test_reader_missing_plan_exits_0_and_logs(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch, with_plan=False)
    assert reader_run(data, head() + BAD + "\n") == (0, None)
    (x,) = _lines(data, "reader_check")
    assert x["decision"] == "no_plan" and x["plan"] == READER_PID

def test_reader_fault_in_the_check_exits_0_and_logs(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    (data / "plans" / (READER_PID + ".json")).write_text('{"batches": [{"x": 1}]}')  # a plan the checker cannot read
    assert reader_run(data, head() + BAD + "\n") == (0, None)
    assert _lines(data, "reader_check")[-1]["decision"] in ("error", "no_plan")

def test_reader_reason_is_at_most_4000_characters(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    many = "\n".join(f'FINDING: r | CITE AS: {"x" * 190}{i} | QUOTE: "q"' for i in range(60))
    page = "\n" + "P" * 150 + "\n" + "\n".join("Q" * 400 for _ in range(40))
    code, out = reader_run(data, head() + many + page + "\n")
    assert out["decision"] == "block" and 3000 < len(out["reason"]) <= 4000 and "more failing lines" in out["reason"]
    assert out["reason"].rstrip().endswith("starting with the JEV-READER line")  # the instruction survives the trim

def test_reader_reason_never_holds_a_section_body(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    paste = f"FINDING: x | CITE AS: docs/one.md#Alpha | QUOTE: \"{R_ALPHA}\" " + R_ALPHA + " " + R_BETA
    for msg in (head() + BAD + "\n" + R_ALPHA + " " + R_BETA + "\n", head() + paste + "\n"):
        _, out = reader_run(data, msg, agent_id=str(hash(msg)))
        assert out and R_ALPHA not in out["reason"] and R_BETA not in out["reason"]

def test_reader_empty_page_text_and_too_many_each_block(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    _, out = reader_run(data, head(), agent_id="e")
    assert "EMPTY | b1" in out["reason"]
    _, out = reader_run(data, head() + GOOD + "\n" + R_ALPHA * 3 + "\n", agent_id="p")
    assert "PAGE TEXT | b1" in out["reason"]
    _, out = reader_run(data, head() + "\n".join([GOOD] * 13) + "\n", agent_id="m")
    assert "TOO MANY | b1 | 13" in out["reason"]

def test_reader_checks_only_the_batch_named_on_the_first_line(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    msg = head() + GOOD + "\n" + head(2) + BAD + "\n"  # a second block for a batch the plan lacks is not this hook's business
    assert reader_run(data, msg) == (0, None)

def test_reader_log_holds_counts_never_the_reply(tmp_path, monkeypatch):
    import stat
    data = reader_lib(tmp_path, monkeypatch)
    reader_run(data, head() + GOOD + "\n" + BAD + "\n")
    (x,) = _lines(data, "reader_check")
    assert {"ts", "session", "agent_id", "plan", "batch", "decision", "findings", "failed"} <= set(x)
    assert x["plan"] == READER_PID and x["batch"] == 1 and x["decision"] == "block" and x["findings"] == 2 and x["failed"] == 1
    assert "every box" not in json.dumps(x)
    for p in (data / "logs", data / "logs" / "reader_check.jsonl", data / "logs" / "reader_check_state.json"):
        assert stat.S_IMODE(os.stat(p).st_mode) & 0o077 == 0, p

def test_reader_log_off_writes_no_log(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, head() + BAD + "\n", JEV_LOG="off")
    assert out["decision"] == "block"  # the check still runs
    assert not (data / "logs" / "reader_check.jsonl").exists()

def test_reader_state_keeps_at_most_500_agent_ids(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    for i in range(3):
        reader_run(data, head() + BAD + "\n", agent_id=f"seed{i}")
    st = data / "logs" / "reader_check_state.json"
    seeded = json.loads(st.read_text())
    key = next(iter(seeded))
    seeded[key] = [f"old{i}" for i in range(700)]
    st.write_text(json.dumps(seeded))
    _, out = reader_run(data, head() + BAD + "\n", agent_id="newest")
    assert out["decision"] == "block"
    ids = json.loads(st.read_text())[key]
    assert len(ids) == 500 and ids[-1] == "newest" and "old0" not in ids
    assert reader_run(data, head() + BAD + "\n", agent_id="newest") == (0, None)

def test_reader_hooks_stopping_together_each_block_exactly_once(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    e = {**os.environ, "JEV_SOURCES_DATA": str(data), "JEV_HOOK_LOG_DIR": str(data), "JEV_LOG": "on", "JEV_SEMANTIC": "off"}
    def start(i):
        payload = json.dumps({"session_id": "s1", "agent_id": f"c{i}", "last_assistant_message": head() + BAD + "\n"})
        p = subprocess.Popen([sys.executable, f"{H}/jev-reader-check.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=e)
        p.stdin.write(payload); p.stdin.close()
        return p
    procs = [start(i) for i in range(20)]
    outs = [p.stdout.read() for p in procs]
    for p in procs:
        p.wait()
    assert all('"block"' in o for o in outs)
    state = json.load(open(data / "logs" / "reader_check_state.json"))["agents"]
    assert sorted(state) == sorted(f"c{i}" for i in range(20))
    assert all(reader_run(data, head() + BAD + "\n", agent_id=f"c{i}") == (0, None) for i in range(20))
    assert not [f for f in os.listdir(data / "logs") if f.endswith(".tmp")]

def test_reader_header_in_bold_or_with_trailing_words_is_recognized(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert reader_run(data, f"**JEV-READER: plan {READER_PID} batch 1**\n" + GOOD + "\n") == (0, None)
    assert reader_run(data, f"JEV-READER: plan {READER_PID} batch 1 (done)\n" + GOOD + "\n", agent_id="a2") == (0, None)
    assert reader_run(data, f"`JEV-READER: plan {READER_PID} batch 1`\n" + BAD + "\n", agent_id="a3")[1]["decision"] == "block"

def test_reader_batch_not_in_the_plan_blocks_once(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, head(7) + GOOD + "\n")
    assert out["decision"] == "block" and out["reason"].startswith("BAD BATCH | b7 |")

def test_reader_hook_and_checker_share_one_header_rule():
    import importlib.util
    spec = importlib.util.spec_from_file_location("jrc", f"{H}/jev-reader-check.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    sys.path.insert(0, os.path.join(os.path.dirname(H), "scripts"))
    import check_findings
    assert m.HEADER.pattern == check_findings.HEADER.pattern and m.MARKS.pattern == check_findings.MARKS.pattern

def test_reader_header_keeps_underscores_in_the_plan_id_and_rejects_batch_ranges():
    import importlib.util
    spec = importlib.util.spec_from_file_location("jrc2", f"{H}/jev-reader-check.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    hit = m.HEADER.match(m.MARKS.sub("", "_JEV-READER: plan my_plan batch 2_"))
    assert hit and hit.group(1) == "my_plan" and hit.group(2) == "2"
    assert not m.HEADER.match("JEV-READER: plan p1 batch 1,2") and not m.HEADER.match("JEV-READER: plan p1 batch 1-3")
    assert m.HEADER.match("JEV-READER: plan p1 batch 1 (done)") and m.HEADER.match("JEV-READER: plan p1 batch 1.")

def test_reader_a_lock_held_too_long_passes_and_logs(tmp_path, monkeypatch):
    import fcntl
    data = reader_lib(tmp_path, monkeypatch)
    (data / "logs").mkdir(exist_ok=True)
    fd = os.open(str(data / "logs" / "reader_check_state.lock"), os.O_WRONLY | os.O_CREAT, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        assert reader_run(data, head() + BAD + "\n") == (0, None)
    finally:
        os.close(fd)
    assert _lines(data, "reader_check")[-1]["decision"] == "error"

def test_reader_hook_flags_page_text_in_the_preamble(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, R_ALPHA + "\n" + head() + GOOD + "\n")
    assert out["decision"] == "block" and "PAGE TEXT | b1" in out["reason"]

def test_reader_hook_blocks_page_text_behind_a_label(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out = reader_run(data, head() + GOOD + "\n- **Rule:** " + R_ALPHA + "\n")
    assert out["decision"] == "block" and "PAGE TEXT | b1" in out["reason"]

def test_a_printed_reader_brief_passes_the_dispatch_check(tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(H), "scripts"))
    import jev
    brief = "\n".join(["----- READER BRIEF plan p1 batch 1 -----", "JEV-READER: plan p1 batch 1", jev.READER_SOURCES,
                       "GOAL: how do Jev Noul questions work"])
    payload = json.dumps({"session_id": "s1", "tool_name": "Agent", "tool_input": {"prompt": brief, "description": "Jev reader"}})
    r = subprocess.run([sys.executable, f"{H}/jev-dispatch-check.py"], input=payload, capture_output=True, text=True,
                       env={**os.environ, "JEV_HOOK_LOG_DIR": str(tmp_path), "JEV_LOG": "off"})
    assert r.returncode == 0 and "deny" not in r.stdout


# --- jev-answer-check.py (Stop) ------------------------------------------------------------------------------------
A_GOOD = '- **Speed:** "every box answers within five seconds" (`docs/one.md#Alpha`, reference rule)\n'
A_BAD = '- **Speed:** "every box answers within five minutes" (`docs/one.md#Alpha`, reference rule)\n'


def answer_run(data, message, raw=None, **extra):
    """(exit code, parsed stdout or None, seconds) for one Stop call; the hook's log lands in `data`."""
    import time
    e = {**os.environ, "JEV_SOURCES_DATA": str(data), "JEV_HOOK_LOG_DIR": str(data), "JEV_LOG": "on", "JEV_SEMANTIC": "off"}
    payload = raw if raw is not None else json.dumps({"session_id": "s1", "stop_hook_active": False,
                                                      "last_assistant_message": message, **extra})
    t = time.monotonic()
    r = subprocess.run([sys.executable, f"{H}/jev-answer-check.py"], input=payload, capture_output=True, text=True, env=e)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None), time.monotonic() - t


def test_answer_hook_passes_a_checked_answer_and_logs_counts(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert answer_run(data, A_GOOD)[:2] == (0, None)
    assert _lines(data, "answer_check")[-1]["decision"] == "clean"


def test_answer_hook_blocks_a_wrong_quote_with_its_row_and_no_page_text(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out, _ = answer_run(data, A_BAD + f'- "{R_BETA}" (`docs/one.md#Alpha`)\n')
    assert code == 0 and out["decision"] == "block" and "NOT FOUND" in out["reason"]
    assert R_ALPHA not in out["reason"] and R_BETA not in out["reason"] and len(out["reason"]) <= 4000
    assert "label it unverified" in out["reason"]


def test_answer_hook_never_blocks_twice_in_a_row(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert answer_run(data, A_BAD, stop_hook_active=True)[:2] == (0, None)
    assert _lines(data, "answer_check")[-1]["decision"] == "loop_guard"


def test_answer_hook_is_silent_and_quick_on_an_answer_that_cites_no_library(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    code, out, secs = answer_run(data, 'Fixed the CSS. She said "this is a long quoted sentence here".')
    assert (code, out) == (0, None) and not (data / "logs" / "answer_check.jsonl").exists()


def test_answer_hook_reads_the_transcript_when_the_message_field_is_missing(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    path = transcript(A_BAD)
    raw = json.dumps({"session_id": "s1", "stop_hook_active": False, "transcript_path": path})
    assert answer_run(data, None, raw=raw)[1]["decision"] == "block"


def test_answer_hook_fails_open_on_bad_input_and_logs_it(tmp_path, monkeypatch):
    data = reader_lib(tmp_path, monkeypatch)
    assert answer_run(data, None, raw="not json")[:2] == (0, None)
    assert answer_run(data, None, raw=json.dumps({"session_id": "s1", "last_assistant_message": 5}))[:2] == (0, None)
    assert _lines(data, "answer_check")[-1]["decision"] == "error"


def test_answer_hook_passes_when_the_library_is_missing(tmp_path):
    assert answer_run(tmp_path / "nowhere", A_BAD)[:2] == (0, None)
