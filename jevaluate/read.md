# Jevaluate: read mode

Rate one project. Work through the phases in order; each phase's output goes into the rating file. Keep reads capped: never load a whole repo or long page into context.

## 1. Intake
Record: project name, URL, **owner** (the GitHub owner, or the publisher of a post), today's date, and the **commit or version rated** (`git ls-remote <url> HEAD`, or the post's date). A rating without a commit can't be compared later.

## 2. Read
- `python3 scripts/fetch_repo.py <owner/repo> --out <tmpdir> --files 4 --cap 4000` (the defaults) writes `meta.json` (owner, stars, dates, license, commit), `extract.md` (the file list, the README, and matching lines from the 4 files most likely to hold Jev calls, capped at 4,000 characters each), and the full text of those files in `files/`.
- Read the file list first. If Jev code sits in files the extract didn't pick (a JSON check catalogue, a second source file), rerun with `--also <path>,<path>`; don't fetch whole files into context. Files that hold the decision logic (thresholds, routing, confidence) count even when the extract shows 0 Jev keywords for them.
- For a post, a docs page or a product without code, read the page itself (capped).
- **Record the depth read:** `full` (every Jev-relevant file read), `extract` (capped extract), or `readme-only`. Readme-only ratings are usually "Can't rate yet."

## 3. Stats
`python3 scripts/jev_callsites.py <tmpdir>/files` counts these (or run it on a local clone). **Never run it on `extract.md`:** the extract keeps only matching lines, so calls that span lines get miscounted. Check its output against what you read:
- Jev call sites, and **requests per item** (one batched request, or several in a row)
- **Atomic questions**: the total, and the average per request
- Question types: Nouls, Choices, Scores; options per Choice
- Whether confidence or probabilities drive an action
- Thresholds: how many, and whether they live in code or prose
- Model: pinned to a version (`jev-1.13.0`) or an alias (`jev-latest`, or none)
- Approximate state size

If there are zero call sites, check whether Jev is reached some other way (an HTTP call to `api.typesafe.ai`, an MCP tool, a wrapper). If Jev is never called, the verdict is **1, Jev in name only**.

## 4. Lineage
Classify the project as one of:
- **Remix of a TypeSafe cookbook or pattern.** Find it in `https://docs.typesafe.ai/llms.txt` (sections Cookbooks and Patterns), fetch it as `.md`, and read the parts the project uses. Condense MDX pages to prose before reading.
- **Remix of another project** (a fork, a port, or an adaptation). Fetch the upstream the same way as in phase 2.
- **New.**

For a remix, list the original's decisions or steps, and mark which the project keeps, changes or drops. That list is its **coverage**.

## 5. Facts
Answer every fact in `rubric.md` as **yes / no / not applicable**, with evidence: a `file:line` or a short quote. No evidence means "no," or "unknown" if the file wasn't read. Before recording unknown, rerun `fetch_repo.py --also` on the file that would answer it; unknown stands only if that fetch fails or no file would answer it, and the fact's line must say which (`--also <path>`, `fetch failed` or `no file would answer it`); `library.py check` refuses it otherwise. Unknowns lower the depth, not the score.

## 6. Scores and stages
- Score each dimension 0 to 3 using the anchors in `rubric.md`. Each score names its anchor and cites the facts behind it.
- Mark the **build stages** it covers, and whether it **closes the loop** (evaluates on labels, then calibrates the numbers and/or revises the questions or state).

## 7. Compare with the library
`python3 scripts/library.py similar --lineage <x> --stage <y> --exclude <owner/repo>` returns past ratings with the same lineage or stage, leaving out this project's own past ratings. Ratings marked `old rubric` were made before the 2026-09-28 rubric: read them for context, never as precedent. For a blind re-rate (a consistency test), whoever dispatches the rater runs `library.py blind --exclude <owner/repo> --out <dir>` and sets `JEVALUATE_LIBRARY=<dir>` for it; the rater's `add` lands in that copy, and the dispatcher adds it to the real library after comparing. Read up to three. If your verdict differs from a similar project's, add one sentence on why. Name only the projects you compared; don't restate scores a rating quotes for a third project. That sentence is how the library keeps ratings consistent.

## 8. Verdict and fixes
- Choose the verdict from the anchors in `rubric.md`. One fatal flaw caps the verdict, whatever the other scores are. The current anchors decide; a past rating that reads them differently is not precedent.
- For a verdict of 3 or below, list the **core fixes**: each is an entry from `fix-catalog.md`, citing the failed fact it answers. Put the most important fix first.
- When a fix can only be confirmed with data (is this question actually producing wrong answers?), say so. That's diagnosis work, not a design fix.
- Offer to draft the fixed version (for example, rewritten questions). Don't draft it unless asked.

## 9. Log
`python3 scripts/library.py add <rating.md>` first runs `library.py check`, which refuses a rating with a missing fact, an unknown with no `--also` fetch noted, no `rubric:` date, or a verdict above what the facts allow. Fix what it lists and rerun. It then saves the rating as `ratings/YYYY-MM-DD-<owner>-<repo>.md` and rebuilds `index.md`. Use this template:

```markdown
---
project: <name>
url: <url>
owner: <github owner>
rated: YYYY-MM-DD
rubric: 2026-09-28   # the date at the top of rubric.md's Verdict anchors
commit: <sha or version>
depth: full | extract | readme-only
lineage: cookbook:<slug> | project:<owner/repo> | new
stages: [data-prep, question-state, execution, decision]   # only these four labels, exactly as written
closes_loop: none | calibrates | revises | both
verdict: 5 | 4 | 3 | 2 | 1 | cant-rate   # cant-rate = "Can't rate yet"
scores: {execution: n, fit: n, coverage: n, evidence: n}
---
## Summary
One paragraph: what it does with Jev, and the verdict in plain words.
## Stats
## Facts (with evidence)
- F1 <name> — yes. <file:line or quote>   # one line per fact, F1-F23; value is yes, no, n.a. or unknown
## Scores (anchor named for each)
## Compared with
## Verdict and reasoning
## Core fixes
```

Report the rating to the user: the verdict, the stats line, the top fixes, and the path to the saved file.
