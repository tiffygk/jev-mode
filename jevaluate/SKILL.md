---
name: jevaluate
description: Use when rating whether a project, repo, skill, workflow, plugin, agent product or post uses TypeSafe's Jev (System One) model well -- "is this a good use of Jev?", "rate this Jev integration", "jevaluate <url>", or a link to something named after Jev. Also use to check whether something that calls itself Jev actually uses it. It rates, logs the rating to a private library, and lists design fixes; it never edits the project.
---

# Jevaluate

Rates how well something uses Jev, TypeSafe's System One model (typed questions over a JSON `state`, answered in parallel with calibrated probabilities). Every rating is evidence-backed, dated, tied to a commit, and logged, so the library of past ratings anchors future ones.

## How to rate

Follow `read.md`, with `rubric.md`, `fix-catalog.md` and `jev-rules.md`. Jevaluate rates projects; it doesn't run or diagnose your own pipeline. If asked for that, say so and stop.

## Model

Run on a Sonnet-class model at medium effort, the same one every time: ratings stay comparable only if the rater doesn't change. In Codex, run on `gpt-6-luna` at medium effort. In another harness, pick one model and effort and keep them. Record both in the rating (`rater`, `effort`); a rating by a different model is a different rater's.

## Verdicts

| Score | Verdict | Means |
|---|---|---|
| 5 | Learn from it | Follows the principles and is measured on labels; reference-grade |
| 4 | Use it | Correct use with minor gaps; plausible but unmeasured |
| 3 | Use with a fix | Right idea, one fixable design flaw (for untrusted text or spliced values, only when a decision acts on sensitive data with no review) |
| 2 | Rework it | Core principles broken; results likely unreliable |
| 1 | False marketing: Jev in name only | Claims to use Jev, and no traced request shows it calling Jev |
| 1 | Not a Jev integration | Never claims to call Jev (a Jev-like model, say), or calls it and the answers drive nothing |
| -- | Can't rate yet | Too little visible to judge (for example, README only, no code) |

These are the names only; the rules that decide each verdict are in `rubric.md`, and the verdict comes from them, never from averaging dimension scores. Any verdict of 3 or below always states its reasoning and the core fixes. Offer to write the fixed version only if the user asks.

## The library

Ratings are logged outside this skill so the skill can be shared without them. Location: `$JEVALUATE_LIBRARY` if set, else `~/.claude/jevaluate-library/` if it exists (libraries made before Codex support), else `~/.jevaluate-library/`. A new user starts with an empty library; `scripts/library.py` creates it. Never overwrite a past rating: projects change, so a re-rating is a new dated entry.

Ratings live under `projects/<slug>/YYYY-MM-DD.md`, one folder per project, so a project's history sits together; a second same-day rating is `YYYY-MM-DD-2.md`. A `<date>-evidence/` folder beside a rating holds its supporting files and is never read as a rating. Curated lists (an awesome-list screen, for example) live under `lists/<name>/`, saved with `library.py list-add`.

## Sources

Only public sources: the docs at docs.typesafe.ai (page list: `https://docs.typesafe.ai/llms.txt`; append `.md` to any page for markdown) and the project's own public files. Credit a repo to its GitHub owner, never to its banner or branding. A project's claims about its own results are claims until the rating checks them.

## In Codex

Codex's default sandbox blocks the network and writes outside the workspace. Fetching a repo (`gh`, `git`) and `library.py add` need your approval, or run with network access and the library folder as a writable root.
