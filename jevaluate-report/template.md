# Report template

Copy this file, fill every `<placeholder>`, and delete each instruction line in angle brackets. Keep the order: front matter, title, opening, summary table, Rating, What already works, fixes. Nothing comes after the last fix but link definitions. `scripts/report_check.py` checks the order, the five labels, the table and the links.

```markdown
---
title: "<Project>: Jevaluate report, rating and <N> fixes to test"
repo: https://github.com/<owner>/<repo>
commit: <the 40-character commit the rating read>
date: <YYYY-MM-DD>
method: "Jevaluate rubric <version> (https://github.com/tiffygk/jev-mode/blob/rubric-<version>-frozen/jevaluate/rubric.md)<, plus a statistics check of the published eval>"
verdict: <n> "<verdict name>"
scores: {execution: <n>, fit: <n>, coverage: <n>, evidence: <n or n.a.>}
fixes:
  - S1: <one-line title>
  - S2: <one-line title>
---

# <Project>: Jevaluate report and fixes to test

This report lists changes to try in <project>, from a Jevaluate rating of commit [`<short commit>`](<tree link at the commit>). Jevaluate checks the design against TypeSafe's documented practice, so each fix is advice to test: none is shown to improve <project> until it passes its test on your own eval.

The verdict is <n> "<name>" (see [Rating](#rating), below the table) because <one cause, in the project's own terms>. <Only when published numbers were checked: the main finding of that check and the headline number it explains.> Start with these fixes:

<When the rating's own reasoning says what reaching a better verdict takes, write "Start with these fixes, which the rating says could reach <n> "<name>" if their tests pass:"; otherwise keep "Start with these fixes:".>

- [<fix title>](#<fix-anchor>): <one line on what to try>
- [<fix title>](#<fix-anchor>): <one line>
- [<fix title>](#<fix-anchor>): <one line>

**For the agent working from this file.** Take one fix at a time, in the table's order. Run its "How to check it" test on the current code first and note the result, then make the change and run the test again. Keep the change only if it meets the bar, and tell the person you're working with each result, kept or not. If a fix conflicts with something the team has already tested, ask before changing it. When Jev Sources is installed, use it for any question about Jev.

| ID | Fix | Where | Order |
|---|---|---|---|
| S1 | [<fix title>](#<fix-anchor>) | [`<file>:<line>`](<permalink at the commit>) | 1, Jev question and model |
| S2 | [<fix title>](#<fix-anchor>) | [`<file>:<line>`](<permalink>) | 2, eval method |

<Optional, one line: terms from the project's own eval, each defined so it can't be read two ways.>

## Rating

**Verdict <n>, "<name>"** at [`<short commit>`](<tree link at the commit>), rubric <version>. <Link the full rating when it is public.>

| Score | Result | What it means |
|---|---|---|
| Execution | <n> of 3 | <the rubric's meaning in one plain line, and the facts behind this score> |
| Fit | <n> of 3 | <same> |
| Coverage | <n> of 3 | <same> |
| Evidence | <n of 3, or n.a.> | <same; n.a. when the project claims no results> |

**Why this verdict.** <The rating's reasoning in two or three sentences, and what would move it.>

## What already works

- <True, specific and linked: the rating's passing facts and, when it ran, what the statistics check found sound.>

## Fixes: <rank group, such as "Jev question and model">

### S1: <fix title>

**What we saw.** <A quote and its permalink. When the project already tried something close, say what it tried and what it found.>

**Why it matters.** <The consequence for the project's users. Say "may" where the effect is not measured.>

**Source.** <A docs URL and its label (reference rule, pattern, cookbook example, sdk reference), or a public statistics source.>

**Suggested change.** Try <a concrete change in the project's own terms>. <When the project tested a version and rejected it, propose a different version and keep the current design as the control.>

**How to check it.** <The test, the measure (or a pass-or-fail outcome) and the bar, set before the run: for example, rerun on held-out goals and compare recall at 10 with and without the change, each with n and an interval.>
```

## Rules for filling it

- **Rank groups, in order:** changes to the Jev question and model (they change what the tool decides), then eval method, then reporting, then minor items. Use only the groups that have fixes.
- **Cross-references** link a section by its name, never a bare `S3`. The ID appears only in headings, the table's ID column and the front matter.
- **Figures** carry n and an interval ("52 of 52 goals, Wilson 95% interval 0.93 to 1.00"). A project that publishes no numbers gets no figures, no statistics section and no "eval" fixes beyond a fix that says how to start measuring.
- **Claims stay inside the rating.** Praise, What already works, the target verdict and every finding say no more than the rating, the docs quote or the line itself. "Checks that share evidence go in one request" never becomes "all checks go in one request".
- **A fix that moves the verdict** is framed as a test with a bar on held-out data, never as a sure win.
- **Plain words.** A person new to the project reads the opening and knows what to do first and that each fix is a test. Name Jev ideas the way the docs do and explain any term the project coined.
- **Repo links** are permalinks at the front-matter commit. For a design doc or folder, replace `repo` and `commit` with `target: <url or folder>`.
