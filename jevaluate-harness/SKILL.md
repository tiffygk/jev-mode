---
name: jevaluate-harness
description: Use when running a jevaluate rating round, re-rating after a rubric change, changing the jevaluate rubric, running its judgment eval, or publishing ratings to the jev-mode ratings folder.
---

# Jevaluate Harness

Companion to `jevaluate` (`jevaluate/read.md` covers one rating). This file covers rounds and the rubric.

Paths like `jevaluate/scripts/...` are relative to the plugin root, the folder that holds `jevaluate/` and `jevaluate-harness/`.

## Settings (yours, not in this skill)
`$PRIVATE_TERMS`: a file of regexes, one per line, for lines never to publish. `library.py export` refuses a match but reads only `$JEVALUATE_LIBRARY/private-terms.txt`, so point `$PRIVATE_TERMS` at that file. Your own pre-push hook should read `$PRIVATE_TERMS` too; jev-mode ships none.

## 1. Pick and screen
Run `python3 jevaluate/scripts/screen_list.py <list README> --known-yes <repo that calls Jev> --known-no <repo that doesn't>`; it stops if either control is misclassified. Quote counts from its output, never by eye. Never classify repos with GitHub code search.

## 2. Size before spending
Run `python3 jevaluate/scripts/coverage_manifest.py <owner/repo> <dir>` for every project and apply `read.md`'s cost rule (section 2) to each. Sum the estimates and agree the total, and every scoped rating, with the user before dispatch; an unattended rater can't ask.

## 3. Brief raters
Give each rater `rater-brief.md`, filling PROJECT, SLUG, PREV (the previous rating file), VIA, SCOPE, RATER (the rater's model ID: `claude-sonnet-5-5` in Claude Code, `gpt-6-luna` in Codex) and JEVALUATE (the absolute path to the plugin's `jevaluate/` folder), and changing its paths if your round folder differs: own folder only, facts written before reading the old rating, no `library.py add`, commit or push.

## 4. Log one at a time
As controller, run `python3 jevaluate/scripts/library.py add <rating> --evidence <dir> --link-docs` for one rating at a time, since `add` rebuilds the shared index and numbers same-day files. Send a refused rating back to its rater; never hand-fix it. Keep a ledger: project, verdict, tokens, flags.

## 5. Adjudicate
Send any verdict move of 2 or more points, and any rubric line a rater called ambiguous, to a fresh reviewer subagent given only the facts. Answer "what would X get?" from that re-verdict, never from memory.

## 6. Calibrate
- Run the judgment eval (`jevaluate/evals/`, see its README; if the folder isn't there yet, say so and skip this step) before and after any rubric change. Tune only on tuning-set failures, never on held-out cases.
- When raters disagree on a fact across re-rates, tighten that fact's anchor, then re-run the eval.
- Test wording with `claude -p --setting-sources "" --strict-mcp-config --tools "" --system-prompt-file <f> --model <m> --effort <e> --output-format json < prompt.md` (`--bare` fails on OAuth logins). In Codex: `codex exec --ignore-user-config --ephemeral --skip-git-repo-check -s read-only -m <m> -c model_reasoning_effort=<e> -c model_instructions_file=<absolute path to f> --json < prompt.md`; `usage` is on the `turn.completed` line, and Codex's tools can't be turned off, so each call carries about 12k tokens of built-in overhead. Agent token logs miss these calls; add each call's `usage` to your spend.
- Measure a cheaper rating mode on one real repo before building it. A quick mode measured at 78k tokens left 10 of 24 facts unknown and was dropped.
- Record each round's findings in `jevaluate/CALIBRATION.md` (create it if missing).

## 7. Publish
1. Give every rating a `why:` line (20 words at most).
2. Run `library.py export <preview dir>`; render it and read the index, a detail page and a full page.
3. Have a fresh reviewer subagent read every page for private context (anything crediting a private conversation, people named other than by their GitHub or Hugging Face handle), rater process notes, and broken or unlinked `file:line` references. Brief it to skip hedging and tone suggestions.
4. Check the README's claims against the skill's current files.
5. Export into `ratings/`, run a GitHub readiness audit, push once.

Publish only full or agreed-scoped ratings under the current rubric; never evidence folders.
