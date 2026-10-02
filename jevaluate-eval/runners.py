"""Run one grader call through Claude or Codex and return {result, usage, commands[, error]}, the shape score.py reads."""
import json, os, pathlib, shutil, subprocess, tempfile

KEEP = ("agent_message", "reasoning")
# Turned off so the grader sees only Codex's built-in tools. HOME is also pointed at the temp home (see env()),
# because Codex finds the user's skills in ~/.agents/skills whatever CODEX_HOME says (found 2026-10-02).
# Shell, image and other tools are off too: with a shell, the grader searched the disk for rubric.md and read it,
# even in a read-only sandbox (2026-10-02 vocab control). What remains is a JavaScript sandbox with no file access.
OFF = ("apps", "multi_agent", "plugins", "remote_plugin", "skill_search", "goals",
       "shell_tool", "unified_exec", "view_image", "image_generation", "sleep_tool", "tool_suggest")


def env(home):
    return {**os.environ, "CODEX_HOME": str(home), "HOME": str(home)}  # Codex items that are the answer itself; anything else counts as tool use


def claude_cmd(system_file, model, effort):
    return ["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "", "--system-prompt-file",
            str(system_file), "--model", model, "--effort", effort, "--output-format", "json"]


def codex_home():
    """One CODEX_HOME per run holding only a symlink to the login: no AGENTS.md, config, MCP servers or plugins
    reach the grader, and a token refresh writes through to the real auth.json. JEV_CODEX_AUTH overrides the path."""
    home = pathlib.Path(tempfile.mkdtemp(prefix="codex-eval-"))
    auth = pathlib.Path(os.environ.get("JEV_CODEX_AUTH") or pathlib.Path.home() / ".codex" / "auth.json")
    if auth.exists():
        (home / "auth.json").symlink_to(auth)
    return home


def close_home(home):
    """Remove a run's temp home. If Codex replaced the auth symlink with a refreshed file, copy it back first."""
    a = pathlib.Path(home) / "auth.json"
    real = pathlib.Path(os.environ.get("JEV_CODEX_AUTH") or pathlib.Path.home() / ".codex" / "auth.json")
    if a.exists() and not a.is_symlink() and a.stat().st_mtime > real.stat().st_mtime:
        shutil.copy2(a, real)
    shutil.rmtree(home, ignore_errors=True)


def codex_ready(home):
    """None when codex can run, else one sentence. Check before writing any run file."""
    if not shutil.which("codex"):
        return "codex not found: install it (npm install -g @openai/codex) and run codex login"
    r = subprocess.run(["codex", "login", "status"], capture_output=True, text=True, timeout=60,
                       env=env(home))
    return None if r.returncode == 0 else "codex is not logged in: run codex login"


def codex_cmd(system_file, model, effort, cwd):
    return ["codex", "exec", "--ephemeral", "--skip-git-repo-check", "-s", "read-only", "-C", str(cwd), "-m", model,
            "-c", f"model_reasoning_effort={effort}", "-c", 'web_search="disabled"',
            *[x for f in OFF for x in ("--disable", f)], "-c", f"model_instructions_file={pathlib.Path(system_file).resolve()}", "--json"]


def parse_codex(stdout):
    out = {"result": "", "usage": {}, "commands": []}
    for line in stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        it = e.get("item") or {}
        if e.get("type") == "item.completed":
            if it.get("type") == "agent_message":
                out["result"] = it.get("text", "")
            elif it.get("type") not in KEEP + ("error",):
                out["commands"].append(f'{it.get("type")}: {it.get("command") or it.get("path") or it.get("query") or ""}')
        if e.get("type") == "turn.completed":
            u = e.get("usage") or {}
            out["usage"] = {"input_tokens": u.get("input_tokens", 0) - u.get("cached_input_tokens", 0),
                            "cache_read_input_tokens": u.get("cached_input_tokens", 0),
                            "cache_creation_input_tokens": u.get("cache_write_input_tokens", 0), "output_tokens": u.get("output_tokens", 0)}
        if e.get("type") in ("turn.failed", "error") or it.get("type") == "error":
            out["warning"] = json.dumps(e.get("error") or it or e)
    if not out["result"] and "warning" in out:
        out["error"] = out.pop("warning")
    return out


def call(runner, system_file, prompt, model, effort, home=None, timeout=900):
    if runner == "claude":
        r = subprocess.run(claude_cmd(system_file, model, effort), input=prompt, capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = None
        if not isinstance(d, dict):
            d = {"result": "", "error": r.stderr or "no JSON object from claude"}
        d.setdefault("commands", [])
        return d
    cwd = tempfile.mkdtemp(prefix="codex-cwd-")
    try:
        r = subprocess.run(codex_cmd(system_file, model, effort, cwd), input=prompt, capture_output=True, text=True,
                           timeout=timeout, env=env(home))
    except subprocess.TimeoutExpired:
        return {"result": "", "usage": {}, "commands": [], "error": f"timed out after {timeout}s"}
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    out = parse_codex(r.stdout)
    if r.returncode != 0 and "error" not in out:
        out["error"] = f"exit {r.returncode}: " + (r.stderr or "")[-500:]
    if not out["result"] and "error" not in out:
        out["error"] = (r.stderr or "no final message")[-500:]
    return out
