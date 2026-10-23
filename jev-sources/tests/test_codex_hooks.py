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


def test_a_users_hook_sharing_a_group_with_ours_survives_install_and_remove(tmp_path):
    run("install", home=tmp_path)
    doc = json.load(open(tmp_path / "hooks.json"))
    doc["hooks"]["Stop"][0]["hooks"].append({"type": "command", "command": "echo MINE"})
    (tmp_path / "hooks.json").write_text(json.dumps(doc))
    run("install", home=tmp_path)
    assert "echo MINE" in commands(json.load(open(tmp_path / "hooks.json")))
    run("remove", home=tmp_path)
    assert commands(json.load(open(tmp_path / "hooks.json"))) == ["echo MINE"]


def test_a_symlinked_hooks_file_is_written_through_and_keeps_its_mode(tmp_path):
    real = tmp_path / "dotfiles" / "hooks.json"
    real.parent.mkdir()
    real.write_text('{"hooks": {}}')
    os.chmod(real, 0o644)
    home = tmp_path / "home"
    home.mkdir()
    (home / "hooks.json").symlink_to(real)
    assert run("install", home=home).returncode == 0
    assert os.path.islink(home / "hooks.json") and len(commands(json.load(open(real)))) == 5
    assert oct(os.stat(real).st_mode & 0o777) == "0o644"


def test_bad_arguments_and_bad_shapes_exit_with_a_message_and_write_nothing(tmp_path):
    r = run("install", "--project")
    assert r.returncode == 2 and "Traceback" not in r.stderr
    for bad in ("[]", '{"hooks": []}', '{"hooks": {"Stop": ["x"]}}'):
        (tmp_path / "hooks.json").write_text(bad)
        r = run("install", home=tmp_path)
        assert r.returncode == 1 and "Traceback" not in r.stderr and (tmp_path / "hooks.json").read_text() == bad


def test_an_empty_project_a_remove_with_no_file_and_non_object_hooks_are_handled(tmp_path):
    assert run("install", "--project", "", home=tmp_path).returncode == 2 and not (tmp_path / "hooks.json").exists()
    r = run("remove", home=tmp_path)
    assert r.returncode == 0 and "removed 0" in r.stdout and not (tmp_path / "hooks.json").exists()
    bad = '{"hooks": {"Stop": [{"hooks": [1, "s", null]}]}}'
    (tmp_path / "hooks.json").write_text(bad)
    assert run("install", home=tmp_path).returncode == 1 and (tmp_path / "hooks.json").read_text() == bad


def test_a_hooks_path_that_is_a_folder_exits_with_a_message(tmp_path):
    (tmp_path / "hooks.json").mkdir()
    r = run("install", home=tmp_path)
    assert r.returncode == 1 and "Traceback" not in r.stderr
