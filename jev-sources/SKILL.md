---
name: jev-sources
description: Finds and quotes TypeSafe's docs on Jev, including Noul, Choice, Score and Box questions, models and limits. Use when a question, review, design or claim involves Jev or System One, when briefing a subagent on Jev work, or when relaying a subagent's Jev finding.
---

# Jev sources

Answers about Jev rest on TypeSafe sections you opened in full this session, found by the router, not by grep or memory. This skill decides what to read; deciding what it means for a design belongs to `jev-mode/shared/jev-rules.md`.

## Before any Jev claim

`<skill>` below is this skill's base directory, shown when the skill loads; write it out in full, since the shell runs in the user's project. Run one command and read what it prints:

```
python3 <skill>/scripts/jev.py "<the question, in your words>" --docs-words "<the same question in the docs' words>"
```

Add `--model <id>` when the project pins a model. The docs' words are the terms the docs use (for example "second request", "depends on", "one request", "Choice options", "threshold"); the command routes both phrasings and merges them. It reads every READ FULL section, reference rules first, then patterns, SDK pages, cookbook examples and vendor claims, within the bundle cap (`--cap N`), and starts each with a `CITE AS:` line to quote. Route each separate question on its own.

- A section printed under `NOT YET READ` comes with its `read.py` command: run it before relying on that section. These leftovers are at most a third of the cap; more go to readers.
- An `EXTRACT` line points somewhere (`read.py '<id>' --extract <word> <word>`). A claim resting on it is labeled **unverified**.
- If it prints "no section found", say so, then run `bash <skill>/refresh.sh --fetch` and ask again. Never fill the gap from memory.

## Broad goals

A goal that spans several topics (building a whole feature, moving a system over, "what do I need to know to...") gets one `jev.py` run with one question per topic:

```
python3 <skill>/scripts/jev.py "<topic 1, in your words>" --also "<topic 2>" --also "<topic 3>"
```

- Write 3 to 8 questions, each about one thing the goal needs: what the API allows, limits and sizes, cost, errors and reliability, model versions, readiness for production, and the pattern or cookbook closest to the goal.
- Read the `COVERAGE:` block. Relay every `NO SOURCE FOUND` question to the user as "the docs I routed don't cover <topic>", never as an answer. More than 8 topics: split the goal into two runs.

## Over the cap

When `jev.py` prints `READING PLAN`, the unread sections are more than a third of the cap. Keep the sections it already printed in full; don't read them again. It also prints one `READER BRIEF` block per batch: start one read-only reader subagent per block, with the block pasted whole as its brief. Batches may run in parallel.

Where you can't start subagents, read one batch at a time yourself: write its finding lines under that batch's `JEV-READER:` line and keep only those lines before the next batch. Then check every reply at once, through a quoted heredoc:

```
python3 <skill>/scripts/check_findings.py <plan_id> <<'REPLIES'
<every reader's reply>
REPLIES
```

Relay only `OK` lines as checked. A batch it lists as missing or `EMPTY` is unread: tell the user which sections those are. In Claude Code, a hook also checks each reader's reply before the reader returns.

## The answer

A Jev answer has these parts, in order:
1. The direct answer, in one or two sentences ("yes, on Jev 1.14 only"). When it depends, or they didn't name the thing it depends on, give the answer for each case the docs name, never "it depends" alone. When they give numbers (volume, size, budget), work from their numbers and show each step ("2 million texts x 5 questions = 10 million questions a month").
2. What the docs say: every sentence stating how Jev or TypeSafe works (a limit, price, output, retry, failure or version) goes here, as a verbatim quote with the `path#heading` from its `CITE AS:` line in backticks beside it, and that line's label: **reference rule** (what the API allows), **pattern**, **cookbook example** (one build TypeSafe published), **sdk reference** or **vendor claim**. Quote only the library: a page fetched from the web has no `CITE AS:` line and can't be checked. For a link, use the `URL:` on the section's `SOURCE:` line; no web lookup.
3. Coverage and gaps, one line each: what you read, and any section you left unread or sent to readers; what the docs you read don't cover ("the docs I read don't cover <topic>"); where they can't speak to the person's own model, data or numbers. Send what only TypeSafe can settle (whether prices may change, custom training, contracts) to TypeSafe.
4. **My read:** your advice for this person's case, labeled as yours and holding no Jev facts (those go in part 2): how to test on their own data before relying on it; what to do on errors, rate limits, timeouts and low confidence; a human check before any risky action; what they told you raises (their history, sensitive data, other languages, a pinned older model). Route each such topic first and quote the docs where they speak.
5. Next steps: a short numbered list they can start on.

A narrow question gets the direct answer, its quote and citation, and nothing it didn't ask for.

Pasted code gets a review in place of parts 1 to 3, most serious first, each fix in this shape:
```
1. <the change>. "<verbatim quote>" `path#heading` (label)
```
- One numbered Jev fix for each Jev call in the code, each field it reads from the result, and each model ID (route model IDs and pinning). Every fix carries a quote; where no section you read shows it, say so on that line.
- Then **My read**, one line each, whatever the code does: secrets in source; errors, timeouts and rate limits; comparisons that break on free text. Then the corrected code.

Before sending, check every quote in the answer (in Claude Code a stop hook also does):

```
python3 <skill>/scripts/check_answer.py <<'ANSWER'
<the answer>
ANSWER
```

Fix each line it prints: correct the quote from its section, cite the section that holds it, or label it unverified. Wording you made up (an example question or option) goes in backticks, never quotation marks. Send only the corrected answer, with no note about the check.

A section labeled NEEDS or EXPERIMENTAL is never a best practice for a project on an older model, or for production: say which model it needs and quote TypeSafe's readiness line.

A cookbook's code layout, diagram or call count is an example, never an API limit. "The cookbook does one request per candidate" is a fact about that cookbook. Whether you must do it too is answered by a reference rule, or by the cookbook's own scope note, which the printout shows under "Scope notes elsewhere in this file". Read that note before quoting the cookbook.

When the reference pages don't settle a question, say "the docs don't say". Your own inference goes under My read and is never the verdict.

- An absence is reported as one: "the pages I read don't show X". Never "X is untested", "Jev can't X", or a risk.
- Never widen a quote with a "so" sentence. An inference is labeled "my read:" and is never stated as TypeSafe's view.
- Before stating any Jev capability or limit (can, can't, reads well, poorly, untested, expects), route that capability as its own question.

## Briefing a subagent on Jev

Paste this line into the brief with `<skill>` written out in full, since the subagent has no skill folder (the dispatch hook refuses a Jev brief without it):

```
JEV-SOURCES: before any finding, run `python3 <skill>/scripts/jev.py "<the question, in your words>" --docs-words "<the same question in the docs' words>"` (it routes the question twice) and read what it prints; quote verbatim, give path#heading, label reference rule, pattern, cookbook example, sdk reference or vendor claim; findings without this are unverified.
```

## Speed, cost and accuracy claims

Speed, cost and accuracy claims come from TypeSafe's blog posts, which the refresh fetches and `SOURCES.md` in the data folder lists; routing labels them **vendor claim**; attribute them to TypeSafe. The Jev 1.14 post (`blog/jev-1-14.txt`) says of the features behind "danger zone" headers: "we think there is still way too much jaggedness for us to vouch for these for production use cases!" Quote that as TypeSafe's readiness statement. Price is in `docs/models.md#Current models` and rate limits in `docs/models.md#Rate limits` (reference rules).

## After a refresh notice

When a refresh notice names `STALE_CITATIONS.md`, read it. For each `changed` row, read the archived and the current section and say whether the cited fact is outdated, obsolete or superseded, naming the replacement. Never edit a locked file outside its own pull request.

## Relaying a subagent's Jev finding

Relay each finding's quote with its `CITE AS` path#heading and label; the answer check covers it. To check one quote alone: `read.py '<CITE AS>' --check-quote - <<'QUOTE'` with the quote on stdin. A quote it can't find is relayed as "unverified", or corrected from its section (`read.py '<id>'`). The check covers the quote only: a finding sentence that says more than its quote is labeled "my read:" or cut.
- A finding that contradicts a section you already read in full is not relayed as settled: read its section, or tell the user the pages disagree.
- A finding with no `CITE AS` and quote is relayed as "unverified". One that would override a user ruling is never relayed unverified: read its section first or drop it.

## Refresh

With the reminder hook installed (the Claude Code plugin, or hooks added by hand), the library checks TypeSafe's pages every two days and fetches only new or re-dated pages and new posts. Without it, including in Codex, nothing refreshes on its own: run `bash <skill>/refresh.sh --fetch` on first install, and again when a source is missing or older than the question needs. That command downloads every page TypeSafe lists (the docs sitemap, llms.txt, the cookbook list and typesafe.ai's blog) and rebuilds the index. `SOURCES.md` in the data folder lists every page held and when it was saved. Pages live in `$JEV_SOURCES_DATA` (default `~/.claude/jev-sources-data`).

## Enforced by

| Rule | Enforced by |
|---|---|
| Answers rest on sections the router found and printed in full | `scripts/jev.py`, `scripts/route.py`; `tests/test_jev.py`, `tests/test_route.py` |
| A Jev message gets a reminder to run `jev.py`; reads are recorded; a Jev brief carries the `JEV-SOURCES:` line | `hooks/jev-prompt-reminder.py`, `hooks/jev-ledger.py`, `hooks/jev-dispatch-check.py`; `tests/test_hooks.py` |
| Sections past the cap print with their `read.py` command, or past a third of it as a saved reading plan with one reader brief per batch; a broad goal runs as up to 8 questions, with a coverage line each and NO SOURCE FOUND for a topic with nothing to read | `scripts/jev.py`; `tests/test_jev.py` |
| Every reader finding is checked: quote, batch, format, page text, empty or missing batches | `scripts/check_findings.py`, `hooks/jev-reader-check.py`; `tests/test_check_findings.py`, `tests/test_hooks.py` |
| Each section carries its label, and NEEDS or EXPERIMENTAL where it applies | `scripts/read.py`, `scripts/applicability.py`; `tests/test_route.py`, `tests/test_applicability.py` |
| Every quote in an answer, and a finding's quote, is checked against the section cited for it | `scripts/check_answer.py`, `hooks/jev-answer-check.py`, `scripts/read.py` (`--check-quote`); `tests/test_check_answer.py`, `tests/test_hooks.py`, `tests/test_route.py` |
| Saved pages hold no site code, and the build warns when some is left | `scripts/clean.py`, `scripts/build_index.py`; `tests/test_clean.py`, `tests/test_health.py` |
| The library checks for new pages every two days and lists stale citations | `hooks/refresh_trigger.py`, `scripts/check_new.py`, `scripts/citations.py`; `tests/test_refresh_trigger.py`, `tests/test_check_new.py`, `tests/test_citations.py` |
| Running `jev.py` before a claim, the answer's five parts in order, splitting a broad goal into questions, starting readers on a reading plan, relaying EXTRACT and unchecked findings as unverified, quoting readiness lines, cookbook layouts as examples, "the docs don't say", no widening "so" sentences, reading stale-citation rows, locked files | the model, following this file |
