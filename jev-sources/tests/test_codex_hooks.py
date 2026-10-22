"""codex_hooks.py: Codex runs no hooks from a plugin, so jev-sources writes its five hooks into Codex's own hooks.json."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPT = os.path.join(SKILL, "scripts", "codex_hooks.py")
MARKET = os.path.join(os.path.dirname(SKILL), ".claude-plugin", "marketplace.json")


def run(*args, home=None):
    env = {**os.environ, **({"CODEX_HOME": str(home)} if home else {})}
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, env=env)


def commands(doc):
    return [h["command"] for groups in doc["hooks"].values() for g in groups for h in g["hooks"]]


def test_install_writes_the_five_hooks_with_paths_that_exist(tmp_path):
    r = run("install", home=tmp_path)
    assert r.returncode == 0, r.stderr
    doc = json.load(open(tmp_path / "hooks.json"))
    assert set(doc["hooks"]) == {"UserPromptSubmit", "PreToolUse", "PostToolUse", "SubagentStop", "Stop"}
    cmds = commands(doc)
    assert len(cmds) == 5
    for c in cmds:
        path = c.split('"')[1]
        assert os.path.isabs(path) and os.path.exists(path), c
    assert "installed 5 jev-sources hooks" in r.stdout


def test_the_hooks_match_the_plugin_manifest(tmp_path):
    run("install", home=tmp_path)
    mine = json.load(open(tmp_path / "hooks.json"))["hooks"]
    plugin = [p for p in json.load(open(MARKET))["plugins"] if p["name"] == "jev-sources"][0]["hooks"]
    want = json.loads(json.dumps(plugin).replace("${CLAUDE_PLUGIN_ROOT}/jev-sources", SKILL))
    assert mine == want


def test_other_hooks_are_kept_and_a_second_install_changes_nothing(tmp_path):
    other = {"description": "mine", "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}]}}
    (tmp_path / "hooks.json").write_text(json.dumps(other))
    run("install", home=tmp_path)
    once = (tmp_path / "hooks.json").read_text()
    run("install", home=tmp_path)
    assert (tmp_path / "hooks.json").read_text() == once
    doc = json.loads(once)
    assert doc["description"] == "mine" and "echo hi" in commands(doc) and len(commands(doc)) == 6


def test_remove_takes_out_only_jev_sources_hooks(tmp_path):
    other = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo bye"}]}]}}
    (tmp_path / "hooks.json").write_text(json.dumps(other))
    run("install", home=tmp_path)
    r = run("remove", home=tmp_path)
    assert r.returncode == 0 and "removed 5" in r.stdout
    assert json.load(open(tmp_path / "hooks.json")) == other


def test_project_install_writes_the_project_file(tmp_path):
    r = run("install", "--project", str(tmp_path / "proj"))
    assert r.returncode == 0, r.stderr
    assert len(commands(json.load(open(tmp_path / "proj" / ".codex" / "hooks.json")))) == 5


def test_a_hooks_file_that_is_not_json_is_left_alone(tmp_path):
    (tmp_path / "hooks.json").write_text("{not json")
    r = run("install", home=tmp_path)
    assert r.returncode == 1 and "not valid JSON" in r.stderr
    assert (tmp_path / "hooks.json").read_text() == "{not json"
