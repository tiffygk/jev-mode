---
name: jev-sources
description: Finds and quotes TypeSafe's docs on Jev, including Noul, Choice, Score and Box questions, models and limits. Use when a question, review, design or claim involves Jev or System One, when briefing a subagent on Jev work, or when relaying a subagent's Jev finding.
---

# Jev sources

Answers about Jev rest on TypeSafe sections you opened in full this session, found by the router, not by grep or memory. This skill decides what to read; deciding what it means for a design belongs to `jev-mode/shared/jev-rules.md`.

## Before any Jev claim

`<skill>` below is this skill's base directory, shown when the skill loads; write it out in full, since the shell runs in the user's project.

Run one command and read what it prints:

```
python3 <skill>/scripts/jev.py "<the question, in your words>" --docs-words "<the same question in the docs' words>"
```

Add `--model <id>` when the project pins a model. The docs' words are the terms the docs use (for example "second request", "depends on", "one request", "Choice options", "threshold"); the command routes both phrasings and merges them. It reads every READ FULL section, reference rules first, then patterns, SDK pages, cookbook examples and vendor claims, within a token cap (`--cap N`), and starts each with a `CITE AS:` line to quote. Route each separate question on its own.

- A section printed under `NOT YET READ (over the cap)` comes with its `read.py` command: run it before relying on that section.
- An `EXTRACT` line points somewhere (`read.py '<id>' --extract <word> <word>`). A claim resting on it is labeled **unverified**.
- If it prints "no section found", say so, then run `bash <skill>/refresh.sh --fetch` and ask again. Never fill the gap from memory.

`route.py` (pick the sections) and `read.py` (print one section) are the parts `jev.py` uses; run them directly to look at one section or one routing.

## What a claim looks like

Each claim carries:
- a verbatim quote,
- the path#heading from the `CITE AS:` line,
- the label on that line: **reference rule** (docs pages: what the API allows), **pattern**, **cookbook example** (a working build TypeSafe published), **sdk reference** or **vendor claim**.

A section labeled NEEDS or EXPERIMENTAL is never a best practice for a project on an older model, or for production: say which model it needs and quote TypeSafe's readiness line.

A cookbook's code layout, diagram or call count is an example, never an API limit. "The cookbook does one request per candidate" is a fact about that cookbook. Whether you must do it too is answered by a reference rule, or by the cookbook's own scope note, which the printout shows under "Scope notes elsewhere in this file". Read that note before quoting the cookbook.

When the reference pages don't settle a question, say "the docs don't say" and stop there. Your own inference is labeled as yours and is never the verdict.

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

Before you pass on a finding, read its cited section yourself (`jev.py`, or `read.py '<id>'` for one section). A finding you have not read is relayed as "unverified". A finding that would override a user ruling is never relayed unverified: read it first or drop it.

## Refresh

With the reminder hook installed (the Claude Code plugin, or hooks added by hand), the library checks TypeSafe's pages every two days and fetches only new or re-dated pages and new posts. Without it, including in Codex, nothing refreshes on its own: run `bash <skill>/refresh.sh --fetch` on first install, and again when a source is missing or older than the question needs. That command downloads every page TypeSafe lists (the docs sitemap, llms.txt, the cookbook list and typesafe.ai's blog) and rebuilds the index. `SOURCES.md` in the data folder lists every page held and when it was saved. Pages live in `$JEV_SOURCES_DATA` (default `~/.claude/jev-sources-data`).
