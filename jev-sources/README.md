# Jev Sources

Jev Sources finds the TypeSafe docs and cookbook sections that answer a Jev question, and makes Claude read them in full before it makes a claim.

| Situation | Use |
|---|---|
| Asking whether a design works with Jev | Route the question, read the sections it lists |
| Reviewing a Jev design or rating | Quote each rule with its page and heading |
| Briefing a subagent on Jev work | Paste the `JEV-SOURCES:` line into the brief |
| Passing on a subagent's Jev finding | Read its cited section first |

## Who it's for

- Developers designing with Jev who want answers from TypeSafe's pages.
- Teams running agents on Jev reviews who need findings they can check.

## Sample

> **route.py** on "can I put 30 passages in one call?"
> ### 3 reference rules to read in full
> Topics matched: batching, re-ranking
>
> - `docs/primitives__noul.md#Structured instructions`
> - `docs/primitives__noul.md#Good practice: ask more than one question per call`
> - `docs/concepts__state.md#State can be a simple string or a structured JSON value`
>
> **Next:** `read.py` each one, then answer with a quote and its heading.

## Results

| Label | Means | Set by |
|---|---|---|
| **READ&nbsp;FULL** | Read it before any claim | The question limits a design, the section is short, or it defines a primitive you named |
| **EXTRACT** | Can point you somewhere; a claim resting on it is unverified | A longer section on a question that doesn't limit a design |
| **Reference&nbsp;rule** | What the API allows | A docs page |
| **Pattern** | A design TypeSafe recommends | A patterns page |
| **Cookbook&nbsp;example** | One way someone built it | A cookbook |
| **No&nbsp;section&nbsp;found** | The library has no answer | Nothing matched; Claude says so and doesn't fill the gap |

## How it works

1. `refresh.sh --fetch` downloads every page TypeSafe lists in `llms.txt` and splits them into sections.
2. `route.py` matches your question to topics and words, and ranks the sections.
3. `read.py` prints a section in full, with any scope note from elsewhere in the file, such as a cookbook's "for clarity" caveat.
4. Claude answers with a verbatim quote, the path and heading, and the label.

The downloaded pages and the index persist in `~/.claude/jev-sources-data/` (or `$JEV_SOURCES_DATA`). A weekly `check_new.py` run can tell you when TypeSafe adds a page.

## Why the hooks

Written instructions alone didn't hold:

- A reviewer agent reported "one call per passage" as a Jev rule. It came from a cookbook's teaching layout, and the finding was passed on unread. Now the prompt hook reminds Claude to route and read whenever a message is about Jev.
- Subagents answered Jev questions from memory. Now the dispatch hook refuses a Jev brief that lacks the `JEV-SOURCES:` line.

## Where the rules come from

This skill holds no rules. It decides what to read; TypeSafe's pages say what Jev allows, and [`jevaluate/jev-rules.md`](../jevaluate/jev-rules.md) holds the design rules. For example, a cookbook that sends one request per candidate shows one way to build it. Whether you must do the same is answered by a docs page.

## Install and use

Needs Claude Code, git and Python 3.8+. No packages.

```
git clone https://github.com/tiffygk/jev-mode
cp -r jev-mode/jev-sources ~/.claude/skills/
bash ~/.claude/skills/jev-sources/refresh.sh --fetch
python3 ~/.claude/skills/jev-sources/scripts/route.py "can I put 30 passages in one call?"
```

The hooks are optional: [`hooks/install-hooks.md`](hooks/install-hooks.md) has the settings lines. Run the tests with `python3 -m pytest tests`.

## Limits

It doesn't call Jev, so it needs no TypeSafe key. TypeSafe's pages aren't in the repo; you download your own copy, and a page that fails to download is named and skipped. Routing finds sections by topic and words, so a question in unusual words can miss; route it again in other words. Not affiliated with TypeSafe.

## License

PolyForm Noncommercial 1.0.0: free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
