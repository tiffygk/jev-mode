import json, os, stat, sys, pathlib
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); import runners

def fake_codex(tmp, events, status_ok=True):
    b = tmp / "bin"; b.mkdir(); f = b / "codex"
    lines = " ".join("'" + json.dumps(e) + "'" for e in events)
    f.write_text("#!/bin/sh\nif [ \"$1\" = login ]; then exit %d; fi\ncat > /dev/null\nprintf '%%s\\n' %s\n" % (0 if status_ok else 1, lines))
    f.chmod(f.stat().st_mode | stat.S_IEXEC); return str(b)

def test_codex_result_and_usage(tmp_path, monkeypatch):
    ev = [{"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}},
          {"type": "item.completed", "item": {"type": "agent_message", "text": "[{\"case\":\"x\"}]"}},
          {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 4, "output_tokens": 2}}]
    monkeypatch.setenv("PATH", fake_codex(tmp_path, ev) + os.pathsep + os.environ["PATH"])
    (tmp_path / "s.md").write_text("sys")
    d = runners.call("codex", tmp_path / "s.md", "prompt", "gpt-6-sol", "medium", home=tmp_path)
    assert d["result"] == '[{"case":"x"}]' and d["commands"] == ["command_execution: ls"]
    assert d["usage"]["input_tokens"] == 6 and d["usage"]["cache_read_input_tokens"] == 4 and d["usage"]["output_tokens"] == 2
    assert "error" not in d

def test_codex_no_message_is_unanswered(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", fake_codex(tmp_path, [{"type": "turn.failed", "error": {"message": "rate limit"}}]) + os.pathsep + os.environ["PATH"])
    (tmp_path / "s.md").write_text("sys")
    d = runners.call("codex", tmp_path / "s.md", "p", "gpt-6-sol", "medium", home=tmp_path)
    assert d["result"] == "" and "rate limit" in d["error"]

def test_codex_missing_says_install(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    assert "codex login" in runners.codex_ready(tmp_path)

def test_codex_logged_out(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", fake_codex(tmp_path, [], status_ok=False) + os.pathsep + os.environ["PATH"])
    assert "not logged in" in runners.codex_ready(tmp_path)

def test_home_symlinks_auth_not_copies(tmp_path, monkeypatch):
    fake = tmp_path / "auth.json"; fake.write_text("{}")
    monkeypatch.setenv("JEV_CODEX_AUTH", str(fake))
    h = runners.codex_home()
    assert (h / "auth.json").is_symlink() and not (h / "AGENTS.md").exists() and not (h / "config.toml").exists()

def test_claude_runner_unchanged_command():
    assert runners.claude_cmd("s.md", "claude-sonnet-5-5", "medium") == ["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "", "--system-prompt-file", "s.md", "--model", "claude-sonnet-5-5", "--effort", "medium", "--output-format", "json"]

def test_score_quiz_runs_on_a_saved_quiz(tmp_path):
    import subprocess, shutil
    run = tmp_path / "q"; run.mkdir()
    (run / "run.json").write_text(json.dumps({"phase": "baseline", "head": "x", "reps": 1}))
    (run / "r1_g0.json").write_text(json.dumps({"result": "[]", "usage": {}}))
    r = subprocess.run([sys.executable, str(HERE / "quiz" / "score_quiz.py"), str(run)], capture_output=True, text=True)
    assert "Traceback" not in r.stderr and "Overall:" in r.stdout

def test_codex_cmd_turns_off_extras_and_env_hides_home(tmp_path):
    cmd = runners.codex_cmd("s.md", "gpt-6-sol", "medium", tmp_path)
    for f in runners.OFF + ("shell_tool", "unified_exec"):
        assert cmd[cmd.index(f) - 1] == "--disable"
    e = runners.env(tmp_path)
    assert e["HOME"] == str(tmp_path) and e["CODEX_HOME"] == str(tmp_path)

def test_warning_with_answer_is_not_an_error(tmp_path, monkeypatch):
    ev = [{"type": "error", "message": "reconnecting"}, {"type": "item.completed", "item": {"type": "agent_message", "text": "[]"}}]
    monkeypatch.setenv("PATH", fake_codex(tmp_path, ev) + os.pathsep + os.environ["PATH"])
    (tmp_path / "s.md").write_text("sys")
    d = runners.call("codex", tmp_path / "s.md", "p", "gpt-6-sol", "medium", home=tmp_path)
    assert d["result"] == "[]" and "error" not in d and d["commands"] == []

def test_todo_list_item_is_not_tool_use(tmp_path, monkeypatch):
    ev = [{"type": "item.completed", "item": {"type": "todo_list", "items": []}},
          {"type": "item.completed", "item": {"type": "agent_message", "text": "ok"}}]
    monkeypatch.setenv("PATH", fake_codex(tmp_path, ev) + os.pathsep + os.environ["PATH"])
    (tmp_path / "s.md").write_text("sys")
    assert runners.call("codex", tmp_path / "s.md", "p", "gpt-6-sol", "medium", home=tmp_path)["commands"] == []

def test_timeout_keeps_spent_usage(tmp_path, monkeypatch):
    b = tmp_path / "bin"; b.mkdir(); f = b / "codex"
    f.write_text("#!/bin/sh\ncat > /dev/null\necho '%s'\nsleep 5\n" % json.dumps({"type": "turn.completed", "usage": {"input_tokens": 9, "output_tokens": 1}}))
    f.chmod(f.stat().st_mode | stat.S_IEXEC); monkeypatch.setenv("PATH", str(b) + os.pathsep + os.environ["PATH"])
    (tmp_path / "s.md").write_text("sys")
    d = runners.call("codex", tmp_path / "s.md", "p", "gpt-6-sol", "medium", home=tmp_path, timeout=1)
    assert "timed out" in d["error"] and d["usage"]["output_tokens"] == 1

def test_close_home_without_real_auth_still_cleans_up(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_CODEX_AUTH", str(tmp_path / "missing.json"))
    h = runners.codex_home(); (h / "auth.json").write_text("new")
    runners.close_home(h)
    assert not h.exists() and (tmp_path / "missing.json").read_text() == "new"
