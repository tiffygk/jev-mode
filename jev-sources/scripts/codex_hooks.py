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
MARK = os.sep + "jev-sources" + os.sep + "hooks" + os.sep


def target(project):
    if project:
        return os.path.join(os.path.abspath(project), ".codex", "hooks.json")
    return os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "hooks.json")


def ours(group):
    return any(MARK in h.get("command", "") or "/jev-sources/hooks/" in h.get("command", "") for h in group.get("hooks", []))


def strip(doc):
    """Remove jev-sources' groups from doc in place; return how many were removed."""
    n = 0
    for event in list(doc.get("hooks", {})):
        keep = [g for g in doc["hooks"][event] if not ours(g)]
        n += len(doc["hooks"][event]) - len(keep)
        if keep:
            doc["hooks"][event] = keep
        else:
            del doc["hooks"][event]
    return n


def write(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".hooks-")
    with os.fdopen(fd, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("install", "remove"):
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
        doc.setdefault("hooks", {})
    removed = strip(doc)
    if a[0] == "remove":
        write(path, doc)
        print(f"removed {removed} jev-sources hooks from {path}")
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
