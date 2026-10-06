---
name: jev-sources
description: Use when a question, review, design or claim involves Jev, TypeSafe, System One, Nouls, or Choice/Score questions, including whether something should be built with Jev, reviewing a Jev design, briefing a subagent on Jev work, or relaying a subagent's Jev finding.
---

# Jev sources

Answers about Jev rest on TypeSafe sections you opened in full this session, found by the router, not by grep or memory. This skill decides what to read; deciding what it means for a design belongs to `jev-mode/shared/jev-rules.md`.

## Before any Jev claim

`<skill>` below is this skill's base directory, shown when the skill loads; write it out in full, since the shell runs in the user's project.

1. Route: `python3 <skill>/scripts/route.py "<the question, in your words>"`. Route each separate question on its own. The router matches words, and adds up to two sections by meaning when its semantic index is on (the output's last line says which). Meaning-matching is a safety net, not a substitute, so still route a design question twice: once in your words, and once in the docs' words (for example "second request", "depends on", "one request", "Choice options", "threshold").
2. Read every **READ FULL** item: `python3 <skill>/scripts/read.py '<id>'`. Read the reference rules first, then the patterns, then the cookbook examples.
3. An **EXTRACT** item (`read.py '<id>' --extract <word> <word>`) can point you somewhere. A claim resting on it is labeled **unverified**.
4. If the router prints "no section found", say so, then run `bash <skill>/refresh.sh --fetch` and route again. Never fill the gap from memory.

## What a claim looks like

Each claim carries:
- a verbatim quote,
- the `SOURCE` path#heading from the read.py header,
- the KIND: **reference rule** (docs pages: what the API allows) or **cookbook example** (a working build TypeSafe published).

A cookbook's code layout, diagram or call count is an example, never an API limit. "The cookbook does one request per candidate" is a fact about that cookbook. Whether you must do it too is answered by a reference rule, or by the cookbook's own scope note, which read.py prints under "Scope notes elsewhere in this file". Read that note before quoting the cookbook.

When the reference pages don't settle a question, say "the docs don't say" and stop there. Your own inference is labeled as yours and is never the verdict.

## Briefing a subagent on Jev

Paste this line into the brief with `<skill>` written out in full, since the subagent has no skill folder (the dispatch hook refuses a Jev brief without it):

```
JEV-SOURCES: before any finding, run route.py on the question and read every READ FULL item with read.py (<skill>/scripts); quote verbatim, give path#heading, label reference rule or cookbook example; findings without this are unverified.
```

## Claims the docs don't hold: speed, cost and accuracy

The router indexes TypeSafe's docs, patterns and cookbooks, not its blog. The speed, cost and accuracy claims against frontier LLMs live in the launch post, so `route.py` finds nothing for them. That does not make them unverified. Read and quote the local capture: `<data>/blog/introducing-system-one-models-and-jev.txt`, where `<data>` is `$JEV_SOURCES_DATA` or `~/.claude/jev-sources-data` (from https://typesafe.ai/blog/introducing-system-one-models-and-jev, captured 2026-10-02; if the file is missing, save that page's text there). Label it **vendor claim (launch post)**, attribute it to TypeSafe, and quote one of:
- line 163: "End-to-end response time is 70ms-500ms for TypeSafe. This can range from 40x-200x faster for the same levels of frontier intelligence for System One shaped queries."
- line 36: "Jev achieves similar levels of intelligence on System One tasks compared to existing LLMs, while being two orders of magnitude faster and more efficient."
- line 263: "193.6x faster, 444.6x cheaper ... we expect that these are on the higher end of real world gains."

Price and rate limits are in the docs (`docs/models.md#Current models`, reference rule).

## Relaying a subagent's Jev finding

Before you pass on a finding, read its cited section with read.py yourself. A finding you have not read is relayed as "unverified". A finding that would override a user ruling is never relayed unverified: read it first or drop it.

## Refresh

`bash <skill>/refresh.sh --fetch` downloads every page TypeSafe lists in llms.txt and rebuilds the index. Pages live in `$JEV_SOURCES_DATA` (default `~/.claude/jev-sources-data`). Run it on first install, and again when a source is missing or older than the question needs.
