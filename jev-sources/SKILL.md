---
name: jev-sources
description: Use when a question, review, design or claim involves Jev, TypeSafe, System One, Nouls, or Choice/Score questions, including whether something should be built with Jev, reviewing a Jev design, briefing a subagent on Jev work, or relaying a subagent's Jev finding.
---

# Jev sources

Answers about Jev rest on TypeSafe sections you opened in full this session, found by the router, not by grep or memory. This skill decides what to read; deciding what it means for a design belongs to `jev-mode/jevaluate/jev-rules.md`.

## Before any Jev claim

1. Route: `python3 ~/.claude/skills/jev-sources/scripts/route.py "<the question, in your words>"`. Route each separate question on its own.
2. Read every **READ FULL** item: `python3 ~/.claude/skills/jev-sources/scripts/read.py '<id>'`. Read the reference rules first, then the patterns, then the cookbook examples.
3. An **EXTRACT** item (`read.py '<id>' --extract <word> <word>`) can point you somewhere. A claim resting on it is labeled **unverified**.
4. If the router prints "no section found", say so, then run the refresh steps or read `Jev Docs Index.md`. Never fill the gap from memory.

## What a claim looks like

Each claim carries:
- a verbatim quote,
- the `SOURCE` path#heading from the read.py header,
- the KIND: **reference rule** (docs pages: what the API allows) or **cookbook example** (one way someone built it).

A cookbook's code layout, diagram or call count is an example, never an API limit. "The cookbook does one request per candidate" is a fact about that cookbook. Whether you must do it too is answered by a reference rule, or by the cookbook's own scope note, which read.py prints under "Scope notes elsewhere in this file". Read that note before quoting the cookbook.

When the reference pages don't settle a question, say "the docs don't say" and stop there. Your own inference is labeled as yours and is never the verdict.

## Briefing a subagent on Jev

Paste this line into the brief (the dispatch hook refuses a Jev brief without it):

```
JEV-SOURCES: before any finding, run route.py on the question and read every READ FULL item with read.py (~/.claude/skills/jev-sources/scripts); quote verbatim, give path#heading, label reference rule or cookbook example; findings without this are unverified.
```

## Relaying a subagent's Jev finding

Before you pass on a finding, read its cited section with read.py yourself. A finding you have not read is relayed as "unverified". A finding that would override a user ruling is never relayed unverified: read it first or drop it.

## Refresh

`bash ~/.claude/skills/jev-sources/refresh.sh --fetch` downloads every page TypeSafe lists in llms.txt and rebuilds the index. Pages live in `$JEV_SOURCES_DATA` (default `~/.claude/jev-sources-data`). Run it on first install, and again when a source is missing or older than the question needs.
