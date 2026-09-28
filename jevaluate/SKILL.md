---
name: jevaluate
description: Use when rating whether a project, repo, skill, workflow, plugin, agent product or post uses TypeSafe's Jev (System One) model well -- "is this a good use of Jev?", "rate this Jev integration", "jevaluate <url>", or a link to something named after Jev. Also use to check whether something that calls itself Jev actually uses it. Read mode rates, logs the rating to a private library, and lists design fixes; it never edits the project.
---

# Jevaluate

Rates how well something uses Jev, TypeSafe's System One model (typed questions over a JSON `state`, answered in parallel with calibrated probabilities). Every rating is evidence-backed, dated, tied to a commit, and logged, so the library of past ratings anchors future ones.

## Pick the mode

| Asked for | Mode | Open |
|---|---|---|
| Rate a project, repo, skill, workflow, product or post | **read** | `read.md` (with `rubric.md`, `fix-catalog.md` and `jev-rules.md`) |
| Diagnose your own Jev pipeline on your own data | **diagnose** | `diagnose.md` -- not included in this version; say so and stop |

Read only the file for the chosen mode.

## Model

Run on a Sonnet-class model at high effort, the same one every time: ratings stay comparable only if the rater doesn't change.

## Verdicts

| Score | Verdict | Means |
|---|---|---|
| 5 | Learn from it | Follows the principles and is measured on labels; reference-grade |
| 4 | Use it | Correct use with minor gaps; plausible but unmeasured |
| 3 | Use with a fix | Right idea, one fixable design flaw |
| 2 | Rework it | Core principles broken; results likely unreliable |
| 1 | Jev in name only | Jev's output doesn't drive any decision, or it doesn't call Jev at all |
| -- | Can't rate yet | Too little visible to judge (for example, README only, no code) |

These are the names only; the rules that decide each verdict are in `rubric.md`, and the verdict comes from them, never from averaging dimension scores. Any verdict of 3 or below always states its reasoning and the core fixes. Offer to write the fixed version only if the user asks.

## The library

Ratings are logged outside this skill so the skill can be shared without them. Location: `$JEVALUATE_LIBRARY` if set, else `~/.claude/jevaluate-library/`. A new user starts with an empty library; `scripts/library.py` creates it. Never overwrite a past rating: projects change, so a re-rating is a new dated entry.

## Sources

Only public sources: the docs at docs.typesafe.ai (page list: `https://docs.typesafe.ai/llms.txt`; append `.md` to any page for markdown) and the project's own public files. Credit a repo to its GitHub owner, never to its banner or branding. A project's claims about its own results are claims until the rating checks them.
