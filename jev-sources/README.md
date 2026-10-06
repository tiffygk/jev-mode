# Jev Sources

Jev Sources finds the sections of TypeSafe's own docs, patterns and cookbooks that answer a Jev question, by keyword and by meaning, and tells Claude to read them in full before any claim.

| Situation | Use |
|---|---|
| Asking whether a design works with Jev | Route the question, read the sections it lists |
| Asking in your own words | Route it as asked; sections also match by meaning |
| Reviewing a Jev design | Quote each rule with page and heading |
| Briefing a subagent, or passing on its finding | Paste the `JEV-SOURCES:` line into the brief; read its cited section first |

## Who it's for

- Developers designing with Jev who want TypeSafe's answers.
- Teams whose agents review Jev designs and need checkable findings.

## Sample

> **route.py** on "can I put 30 passages in one call?"
> ### 11 sections to read in full, reference rules first
>
> - `docs/primitives__noul.md#Structured instructions`
> - `docs/primitives__noul.md#Good practice: ask more than one question per call`
> - ...9 more
>
> **Next:** `read.py` every READ FULL item before any claim.

## Results

| Label | Means | Set by |
|---|---|---|
| **READ&nbsp;FULL** | Read it before any claim | A design-limiting question, a short section, or a named primitive |
| **EXTRACT** | A pointer; claims from it are unverified | Long or meaning-only sections, unless the question limits a design |
| **Reference&nbsp;rule** | What the API allows | A TypeSafe docs page |
| **Pattern** | A design TypeSafe recommends | A TypeSafe patterns page |
| **Cookbook&nbsp;example** | A working build TypeSafe published | A TypeSafe cookbook |
| **No&nbsp;section&nbsp;found** | Nothing to quote; rephrase or refresh | Nothing matched |

## How it works

1. Download every page TypeSafe lists in `llms.txt` with `refresh.sh --fetch`, which indexes each section by word and by meaning.
2. Route a question with `route.py`: it ranks sections by topics and words, then adds up to two by meaning.
3. Read a section in full with `read.py`, which adds any scope note elsewhere in its file.
4. Claude answers with a verbatim quote, the path and heading, and the label.

Pages and indexes persist in `~/.claude/jev-sources-data/`.

### Matching by meaning

Keyword results come first, unchanged. A small local model (`minishlab/potion-base-8M`) then adds sections worded differently from your question, offline; a question routes in about 0.3 s on an Apple Silicon Mac. On 20 questions written without the docs' words, 16 found their exact section, against 14 on keywords alone; the same 20 were used to tune it. `JEV_SEMANTIC=off` turns it off; the output's last line says which.

## Why the hooks

Instructions didn't hold:

- A reviewer agent reported a cookbook's "one call per passage" layout as a Jev rule. Now a prompt hook reminds Claude to route and read when a message mentions Jev.
- Subagents answered Jev questions from memory. Now a dispatch hook refuses a Jev brief without the `JEV-SOURCES:` line.

## Where the rules come from

This skill adds no rules of its own; it pulls up TypeSafe's text, quoted with page and heading. [jevaluate](../jevaluate/) rates designs against [`shared/jev-rules.md`](../shared/jev-rules.md), which names each rule's source, TypeSafe's or its own. For example, a cookbook that sends one request per candidate is one build TypeSafe shows; a reference rule decides whether yours must.

## Install and use

Needs Claude Code, git and Python 3.9+. The first refresh installs model2vec with pip for matching by meaning; if that fails, routing uses keywords only.

As a Claude Code plugin, with the hooks:

```
claude plugin marketplace add tiffygk/jev-mode
claude plugin install jev-sources@jev-mode
```

Then ask Claude to refresh Jev Sources once.

By copy:

```
git clone https://github.com/tiffygk/jev-mode
cp -r jev-mode/jev-sources ~/.claude/skills/
bash ~/.claude/skills/jev-sources/refresh.sh --fetch
python3 ~/.claude/skills/jev-sources/scripts/route.py "can I put 30 passages in one call?"
```

The first fetch downloads about 130 pages. Copy installs add the hooks by hand: [`hooks/install-hooks.md`](hooks/install-hooks.md).

## Limits

It doesn't call Jev, so it needs no TypeSafe key. You download TypeSafe's pages yourself; a failed page is named and skipped. A question can still miss; route it again in other words. Not affiliated with TypeSafe.

## License

PolyForm Noncommercial 1.0.0: free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
