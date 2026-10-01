[← Summary](../AkashPriyadarshii__jev-superpowers.md)

# jev-superpowers: full rating

**Verdict 1, False marketing: Jev in name only** · jev replacement · rated 2026-09-30 at [`4e5f569`](https://github.com/AkashPriyadarshii/jev-superpowers/tree/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

The repo is a skill pack, three hooks and a local bridge, `scripts/serve-laya.py`, that accepts Jev's `/v1/systemone` request format and answers Choice, Score and Noul questions by word overlap and keyword lists. Its skills and hooks are clearly written and put a stop on failures, but no code in the repo creates a TypeSafe client, posts to `api.typesafe.ai` or names a gateway model ID. The README says Jev gates every decision and quotes latency, cost and hallucination figures with no capture behind them.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** `jev_callsites.py` flags no file; the seven mentions are docs. `hooks/pre-commit:20` only runs the external `git jev check` binary. (`hooks/pre-commit:20`) Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md |

## Why this verdict

Routing gives 1a, so the verdict is 1 and no score is set. The project is typed jev-replacement because the one running code that speaks Jev's request format is `scripts/serve-laya.py`, which answers by word overlap and keyword lists and reports `laya-421m` as its model even when `laya` is installed ([`scripts/serve-laya.py:64`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/scripts/serve-laya.py#L64), [`scripts/serve-laya.py:99`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/scripts/serve-laya.py#L99), [`scripts/serve-laya.py:230`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/scripts/serve-laya.py#L230)). The README says Jev gates every decision ([`README.md:56`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/README.md#L56)), yet the calls sit in other repos (`hooks/pre-commit:20` runs the external `git jev check`) and no line here posts to `api.typesafe.ai`. Borderline: those external tools are real Jev clients, so the claim may hold across the owner's ecosystem; this rating covers only this commit.

## Fixes (from reading the code; not tested against it)

1. Failed F0: either make a traced call to hosted Jev through the SDK or `api.typesafe.ai` and let its typed answers drive a decision, or say plainly in the README that this repo does not call Jev and the bridge is a keyword stand-in ([`introduction/quickstart`](https://docs.typesafe.ai/introduction/quickstart), `sdk`).

<details>
<summary><b>Files read (58)</b></summary>

- .claude-plugin/plugin.json -- read
- .codex-plugin/plugin.json -- read
- .cursor-plugin/plugin.json -- read
- .kimi-plugin/plugin.json -- read
- .opencode/INSTALL.md -- read
- .pi/extensions/superpowers.ts -- read
- AGENTS.md -- read
- CHANGELOG.md -- read
- CLAUDE.md -- read
- README.md -- read
- docs/ARCHITECTURE.md -- read
- docs/CONFIDENCE.md -- read
- docs/DESIGN-site.md -- read
- docs/DESIGN.md -- read
- docs/FOSS_LAYA.md -- read
- docs/HANDOFF.md -- read
- docs/PRD.md -- read
- docs/USAGE.md -- read
- gemini-extension.json -- read
- install.ps1 -- read
- install.sh -- read
- memory/DECISIONS.md -- read
- scripts/serve-laya.py -- read
- scripts/test.ps1 -- read
- scripts/test.sh -- read
- site/about.html -- read
- site/index.html -- read
- site/lexicon.html -- read
- site/llms.txt -- read
- site/matrix.html -- read
- site/privacy.html -- read
- site/script.js -- read
- site/style.css -- read
- site/system-one.html -- read
- site/workflows.html -- read
- skills/brainstorming/SKILL.md -- read
- skills/brainstorming/scripts/helper.js -- read
- skills/brainstorming/scripts/server.cjs -- read
- skills/brainstorming/visual-companion.md -- read
- skills/executing-plans/SKILL.md -- read
- skills/finishing-a-development-branch/SKILL.md -- read
- skills/jev-brainstorming/SKILL.md -- read
- skills/jev-executing-plans/SKILL.md -- read
- skills/jev-systematic-debugging/SKILL.md -- read
- skills/jev-using-superpowers/SKILL.md -- read
- skills/jev-verification/SKILL.md -- read
- skills/jev-writing-plans/SKILL.md -- read
- skills/requesting-code-review/SKILL.md -- read
- skills/systematic-debugging/CREATION-LOG.md -- read
- skills/test-driven-development/SKILL.md -- read
- skills/test-driven-development/writing-good-tests.md -- read
- skills/using-superpowers/SKILL.md -- read
- skills/writing-plans/SKILL.md -- read
- skills/writing-skills/SKILL.md -- read
- skills/writing-skills/anthropic-best-practices.md -- read
- skills/writing-skills/graphviz-conventions.dot -- read
- skills/writing-skills/render-graphs.js -- read
- skills/writing-skills/testing-skills-with-subagents.md -- read

</details>
