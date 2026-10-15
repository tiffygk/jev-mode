# Installing the hooks (optional)

Three hooks go with the skill: a reminder and a dispatch check that keep Claude reading sources on Jev work, and a ledger (below). The Claude Code plugin install adds all three automatically; don't also add them to `settings.json`, or both fire. For a copy install, add the first two to `~/.claude/settings.json` under `"hooks"`:

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

A third hook, `jev-ledger.py`, keeps a record of which sections were routed and read. After each Bash command that runs `route.py`, `read.py` or `jev.py`, it appends one line to `<data>/logs/ledger/<hash of the session id>.jsonl`, with the time, session, folder, the event (`routed` or `read`) and the `path#heading` of each section. It stays on this machine, sends nothing, prints nothing and never blocks; `JEV_LOG=off` turns it off. The plugin install adds it. For a copy install, add it by hand to `~/.claude/settings.json` under `"hooks"`:

```json
"PostToolUse": [
  {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/jev-sources/hooks/jev-ledger.py"}]}
]
```

## Logs and settings

The reminder logs every decision, fire or skip, to `<data>/logs/reminder.jsonl`: the session, the rule, the matched words and the first 120 characters of the message. The dispatch check logs each decision to `<data>/logs/dispatch.jsonl`. `<data>` is `$JEV_SOURCES_DATA`, else `~/.claude/jev-sources-data`. The logs stay on your machine.

- `JEV_LOG=off` turns these logs off.
- `JEV_FIRE_RULE=<rule>` runs another rule from `hooks/firing.py`, for testing. An unknown name falls back to the default.
- `python3 scripts/firing_report.py [--since YYYY-MM-DD]` reports prompts, fires and reasons per day.

## In Codex

Codex runs the same reminder from `~/.codex/hooks.json`. Use absolute paths:

```json
{"hooks": {"UserPromptSubmit": [
  {"hooks": [{"type": "command", "command": "/usr/bin/python3 /path/to/jev-sources/hooks/jev-prompt-reminder.py", "timeout": 30}]}
]}}
```

Codex runs a new hook only after you review and trust it in Codex. If you also installed the plugin in Codex, check that the reminder doesn't appear twice; if it does, remove this entry. The dispatch check has no Codex version.
