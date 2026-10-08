[← Summary](../AkashPriyadarshii__jev-superpowers--gpt-6-sol.md)

# jev-superpowers: full rating

**Verdict 1, False marketing: Jev in name only** · jev replacement · rated 2026-10-06 at [`4e5f569`](https://github.com/AkashPriyadarshii/jev-superpowers/tree/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

This skills framework claims TypeSafe Jev gates and offers a local System One compatible endpoint, but its runnable code sends no requests to hosted Jev. Its six Jev-prefixed skills give concrete CLI commands and a written confidence policy. The bridge returns keyword and text-overlap heuristics even when Laya is installed, while its site describes physical hooks and measured performance without supporting implementation or measurements.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** The local bridge answers requests itself; installer only sets keys; skill files instruct external CLI use ([`scripts/serve-laya.py:202`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/scripts/serve-laya.py#L202), [`install.sh:50`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/install.sh#L50), [`skills/jev-brainstorming/SKILL.md:25`](https://github.com/AkashPriyadarshii/jev-superpowers/blob/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9/skills/jev-brainstorming/SKILL.md#L25)). |

## Scores

- Execution n.a.; Fit n.a.; Coverage n.a.; Evidence n.a.: verdict 1a is decided at routing.

## Why this verdict

The repository claims TypeSafe Cloud Jev gates, yet no runnable project code calls hosted Jev. The runnable bridge serves Jev-style typed answers with keyword and token-overlap rules and labels responses `laya-421m` even when only those rules execute. Those claims and the offered compatible endpoint put the project on the 1a route. The previous 2 assumed the external CLI instructions were a project Jev integration.

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
