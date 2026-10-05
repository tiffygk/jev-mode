# Jevaluate: rating a project

Rate one project in the phases below, in order. Phases 3, 5, 6, 7 and 8 start with `python3 scripts/step.py next <rating.md>`, which serves the rubric section for that phase once the previous phase is written in the rating file. Keep reads capped: never load a whole repo or long page into context.

## 1. Intake
Record the project name, URL, owner (the GitHub owner, or a post's publisher), today's date, and the commit or version rated (`git ls-remote <url> HEAD`, or the post's date). A rating without a commit can't be compared later.

## 2. Read
- `python3 scripts/coverage_manifest.py <owner/repo> <tmpdir>` writes `manifest.md`, `meta.json` and the files in `files/`. Read every manifest file that could change a fact or the verdict, and list each under `## Coverage` as `read` or `skipped: <reason>`. Files holding decision logic (thresholds, routing, confidence) count even with no Jev keywords.
- `step.py` prints the cost estimate and stops above 200k until the controller approves it; a scoped rating is the controller's call.
- For a quick look, `python3 scripts/fetch_repo.py <owner/repo> --out <tmpdir>` fetches the file list, README and likeliest files; `--also <path>` fetches more. For a post or page without code, read the page itself.
- **Depth:** `full` (every manifest file read), `extract` (a scope approved by the controller, such as the 6 files holding the Jev calls) or `readme-only` (the repo holds only a README).

## 3. Route
- `python3 scripts/jev_callsites.py <tmpdir>/files` counts `hosted_calls`; only those are calls. Never run it on `extract.md`. Before recording calls Jev as no, look for a call it can't see: a wrapper, an MCP tool, or a server behind the site's own `/api`.
- Write the routing calls into the front matter: `project_type`, calls Jev (the F0 line), `verdict_1_code`, `citation`, and the five fields for a jev-mention-only. A yes cites the `path:line` of the call in a code file; a no names each file `jev_callsites.py` flags and says why it isn't a call.
- Write `## Decisions`, one line per decision Jev makes, with its stakes as you read them (none for a client, a guide or a routed code). Code fills in kind and top stakes.
- A project routed to 1a, 1b, 1c, 1r or 1t (every guide is 1t) stops here: write the Summary and go to phase 7.
- Fill `## Stats` (the template lists what goes there).

## 4. Lineage
A remix of a TypeSafe cookbook or pattern (`cookbook:<slug>`, found in `https://docs.typesafe.ai/llms.txt`; read the parts the project uses), a remix of another project (`project:<owner/repo>`, fetched as in phase 2), or `new`. For a remix, list the original's decisions or steps and mark which the project keeps, changes or drops: that list is its coverage.

## 5. Facts
One line for every fact the type leaves in play. Before recording unknown, rerun `fetch_repo.py --also` on the file that would answer it, and say on the line which file (or `fetch failed`, or `no file would answer it`).

## 6. Scores, stages and the loop
Score each dimension, naming the anchor and the facts behind it. Mark the build stages and `closes_loop`.

## 7. Compare with the library
`step.py next` prints short cards of past ratings, closest first; `python3 scripts/step.py full <rating.md> <past rating>` prints the two closest in full, and the project's previous rating. Ratings marked `old rubric` are context, never precedent. If your verdict differs from a similar project's, say why in one sentence.

## 8. Verdict and fixes
Set the verdict and `why`. For a verdict of 3 or below, list the core fixes, most important first, each from the fix-catalog rows `step.py` served, citing the failed fact and its TypeSafe page. Say when a fix can only be confirmed with data.

## 9. Log
`python3 scripts/library.py add <rating.md> --evidence <tmpdir> --link-docs` runs `library.py check` first; when it refuses, fix each line it names and rerun. A revision of a same-day rating uses `--supersedes <old file>`. Ratings are published: write findings only, with no revision history ("second pass") or first-person choices ("I kept 2"), other ratings only in Stats and `## Compared with`, people only by their GitHub or Hugging Face handle, and nothing said privately. Template:

```markdown
---
project: <name>
url: <url>
owner: <github owner>
rated: YYYY-MM-DD
rubric: 2026-09-29   # the date in rubric.md's title
project_type: workflow | library | client | agent-tool | display | guide | jev-replacement | jev-mention-only
verdict_1_code: 1a | 1b | 1c | 1r | 1t | none
citation: <the exact claim to use or call Jev, with file:line> | none
# jev-mention-only only: type_best_match, code_functionality, replaces_jev, intended_call (rubric.md section 1)
rater: <model id>   # e.g. claude-sonnet-5-5
effort: medium | high
commit: <sha or version>
depth: full | extract | readme-only
lineage: cookbook:<slug> | project:<owner/repo> | new
stages: [data-prep, question-state, execution, decision]   # only these labels
closes_loop: none | calibrates | revises | both
verdict: 5 | 4 | 3 | 2 | 1 | cant-rate   # cant-rate = "Can't rate yet"
why: <at most 20 words: the one reason for this verdict, for the public index>
scores: {execution: n, fit: n, coverage: n, evidence: n}   # n.a. for a routed code; evidence n.a. when it claims no results
via: direct | list:<name>   # direct = someone named it; list:<name> = it came off a curated list
---
## Summary
Three sentences: what it does with Jev; what it does well; what holds it back.
## Stats
- Requests per item; atomic questions, total and per request; question types and options per Choice; whether confidence drives an action; thresholds and where they live; model ID; approximate state size.
## Decisions
- <decision> | <Noul, Choice or Score> | <very high, high or low> | acts at <file:line> | <what code does with the answer>   # one line per decision; none for a client, a guide or a routed code
## Facts (with evidence)
- F0 Calls hosted Jev -- yes. <what the call is, in at most 20 words> (`file:line`)
- F1 <name> -- no. <the finding, in at most 20 words> (`file:line`). <TypeSafe page>
# One line per fact: the value, a finding of at most 20 words, the file:line; a no ends with its TypeSafe page.
## Scores
- <Dimension> <n> of 3: <what that score means for this project, in plain words>, <the facts behind it, by name>.   # the anchor's meaning, never a quote of it
## Compared with
## Verdict and reasoning
At most five sentences: why this verdict and not the one above it, and any borderline call.
## Core fixes
## Coverage
- <path> -- read | skipped: <reason>   # one line per manifest file
```

Report to the user: the verdict, the stats line, the top fixes, and the path to the saved file.
