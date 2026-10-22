# Installing the hooks (optional)

Five hooks go with the skill: a reminder and a dispatch check that keep Claude reading sources on Jev work, a ledger, a reader check and an answer check (all below). The Claude Code plugin install adds all five automatically; don't also add them to `settings.json`, or both fire. For a copy install, add the first two to `~/.claude/settings.json` under `"hooks"`:

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

A fourth hook, `jev-reader-check.py`, runs when a subagent stops. A reader subagent of a saved reading plan starts its reply with `JEV-READER: plan <id> batch <n>` on a line of its own (a short preamble before it is allowed). The hook runs `scripts/check_findings.py` on that reply, for that batch only. If a quote is altered, a finding is outside the batch, a line holds 8 words in a row from a section of the batch, the reply carries more than 600 characters outside its finding lines, there are more than 12 findings, there are none, or the batch number is not in the plan, it blocks the stop once for that agent and prints the failing lines, so the reader fixes them while it still holds the pages. The reason never carries section text and is at most 4,000 characters. The same agent's next stop passes (the loop guard; state in `<data>/logs/reader_check_state.json`, owner-only, the newest 500 agent ids, and an empty lock file beside it). A reply with `FINDING:` lines but no `JEV-READER:` line is sent back once to add it. A reply with neither passes silently; a missing plan file or any fault passes with no output and is logged. It logs counts, never the reply, to `<data>/logs/reader_check.jsonl`; `JEV_LOG=off` turns the log off. It is a quality check, not a security boundary: after 15 seconds Claude Code lets the reply through. The plugin install adds it. For a copy install, add it by hand to `~/.claude/settings.json` under `"hooks"`:

```json
"SubagentStop": [
  {"hooks": [{"type": "command", "command": "python3 ~/.claude/skills/jev-sources/hooks/jev-reader-check.py", "timeout": 15}]}
]
```

A fifth hook, `jev-answer-check.py`, runs when the main session finishes a reply. If the reply cites a section of the library (`docs/`, `cookbooks/`, `patterns/` or `blog/`), it runs `scripts/check_answer.py` on it: each quote in double quotes is checked against the section cited beside it, or, when it has no citation of its own, against its parent bullet's citation and the other citations under the same heading. A quote not on its cited section, a citation that names no section, or a quote of 8 or more words that no citation around it holds blocks the stop once with those lines (never page text), so the model corrects the quote, cites the section that holds it, or labels it unverified. The next stop passes. A reply that cites no section passes with no output and no log. It logs counts to `<data>/logs/answer_check.jsonl`; `JEV_LOG=off` turns the log off. Any fault passes and is logged. The plugin install adds it. For a copy install, add it by hand:

```json
"Stop": [
  {"hooks": [{"type": "command", "command": "python3 ~/.claude/skills/jev-sources/hooks/jev-answer-check.py", "timeout": 15}]}
]
```

## Logs and settings

The reminder logs every decision, fire or skip, to `<data>/logs/reminder.jsonl`: the session, the rule, the matched words and the first 120 characters of the message. The dispatch check logs each decision to `<data>/logs/dispatch.jsonl`, the reader check to `<data>/logs/reader_check.jsonl`. `<data>` is `$JEV_SOURCES_DATA`, else `~/.claude/jev-sources-data`. The logs stay on your machine.

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

Codex runs a new hook only after you review and trust it in Codex. If you also installed the plugin in Codex, check that the reminder doesn't appear twice; if it does, remove this entry. The dispatch check and the reader check have no Codex version: Codex has no `SubagentStop` as of this writing. There, run `python3 scripts/check_findings.py <plan_id> < replies.txt` on the readers' replies before relaying them.
