#!/usr/bin/env python3
"""Codex runs no hooks from an installed plugin, so this writes jev-sources' five hooks into Codex's own hooks.json:
the reminder, the brief check, the read ledger, the reader quote check and the answer quote check, each pointing at
this skill folder by absolute path. Other hooks in the file are kept; running it again changes nothing.
  codex_hooks.py install [--project <dir>]   into $CODEX_HOME/hooks.json (default ~/.codex), or <dir>/.codex/hooks.json
  codex_hooks.py remove  [--project <dir>]   takes out only jev-sources' hooks
Run it again after moving or updating the skill folder."""
import json, os, sys, tempfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# event, matcher, hook file, timeout: the same set as .claude-plugin/marketplace.json (tests/test_codex_hooks.py checks)
HOOKS = [("UserPromptSubmit", None, "jev-prompt-reminder.py", None),
         ("PreToolUse", "Agent", "jev-dispatch-check.py", None),
         ("PostToolUse", "Bash", "jev-ledger.py", None),
         ("SubagentStop", None, "jev-reader-check.py", 15),
         ("Stop", None, "jev-answer-check.py", 15)]
NAMES = {name for _, _, name, _ in HOOKS}


def target(project):
    if project:
        return os.path.join(os.path.abspath(project), ".codex", "hooks.json")
    return os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "hooks.json")


def ours(hook):
    """A jev-sources hook: a command running one of HOOKS' files from a jev-sources/hooks folder."""
    cmd = hook.get("command", "") if isinstance(hook, dict) else ""
    return "/jev-sources/hooks/" in cmd and any(cmd.rstrip('"').endswith("/" + n) for n in NAMES)


def well_formed(doc):
    return (isinstance(doc, dict) and isinstance(doc.get("hooks", {}), dict)
            and all(isinstance(gs, list) and all(isinstance(g, dict) and isinstance(g.get("hooks", []), list) for g in gs)
                    for gs in doc.get("hooks", {}).values()))


def strip(doc):
    """Remove jev-sources' hooks from doc in place, keeping every other hook; a group left empty goes. Returns how
    many hooks were removed."""
    n = 0
    for event in list(doc.get("hooks", {})):
        groups = []
        for g in doc["hooks"][event]:
            mine = [h for h in g.get("hooks", []) if ours(h)]
            n += len(mine)
            if mine:
                g = dict(g, hooks=[h for h in g["hooks"] if not ours(h)])
            if g.get("hooks"):
                groups.append(g)
        if groups:
            doc["hooks"][event] = groups
        else:
            del doc["hooks"][event]
    return n


def write(path, doc):
    """Atomic replace of the file a symlinked path points to, keeping its mode; the temp file never outlives a failure."""
    path = os.path.realpath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = os.stat(path).st_mode & 0o777 if os.path.exists(path) else 0o644
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".hooks-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(doc, f, indent=2)
            f.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("install", "remove"):
        print(__doc__, file=sys.stderr)
        return 2
    if "--project" in a and a.index("--project") + 1 >= len(a):
        print(__doc__, file=sys.stderr)
        return 2
    project = a[a.index("--project") + 1] if "--project" in a else None
    path = target(project)
    if any(c in SKILL for c in '"$`\\'):
        print(f"the skill folder's path has a character a hook command can't quote: {SKILL}", file=sys.stderr)
        return 1
    doc = {"hooks": {}}
    if os.path.exists(path):
        try:
            doc = json.load(open(path, encoding="utf-8"))
        except ValueError:
            print(f"{path} is not valid JSON; fix or move it, then run this again", file=sys.stderr)
            return 1
        if not well_formed(doc):
            print(f"{path} is not a hooks file this can merge into (a \"hooks\" object of event lists); fix or move it, "
                  "then run this again", file=sys.stderr)
            return 1
        doc.setdefault("hooks", {})
    removed = strip(doc)
    if a[0] == "remove":
        write(path, doc)
        print(f"removed {removed} jev-sources hook{'s' if removed != 1 else ''} from {path}")
        return 0
    for event, matcher, name, timeout in HOOKS:
        hook = {"type": "command", "command": f'python3 "{os.path.join(SKILL, "hooks", name)}"'}
        if timeout:
            hook["timeout"] = timeout
        group = ({"matcher": matcher} if matcher else {})
        group["hooks"] = [hook]
        doc["hooks"].setdefault(event, []).append(group)
    write(path, doc)
    print(f"installed {len(HOOKS)} jev-sources hooks into {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
