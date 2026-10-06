# Installing the hooks (optional)

Two hooks keep Claude reading sources on Jev work. The Claude Code plugin install adds them automatically; don't also add them to `settings.json`, or both fire. For a copy install, add them to `~/.claude/settings.json` under `"hooks"`:

```json
"UserPromptSubmit": [
  {"hooks": [{"type": "command", "command": "python3 ~/.claude/skills/jev-sources/hooks/jev-prompt-reminder.py"}]}
],
"PreToolUse": [
  {"matcher": "Agent", "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/jev-sources/hooks/jev-dispatch-check.py"}]}
]
```

- `jev-prompt-reminder.py` adds a reminder to route and read when a message mentions Jev, and passes on any new-page notice from `check_new.py`. It never blocks.
- `jev-dispatch-check.py` refuses a subagent brief about Jev that lacks the `JEV-SOURCES:` line, and prints the line to add. A brief that makes no claim about Jev can carry `NO-JEV-CLAIMS: <why>` on its own line instead; each opt-out is logged.

Each hook logs what it did to `~/.claude/hooks/<name>.log` (or `$JEV_HOOK_LOG_DIR`).
