# Jev Mode

Context and eval tools for building with Jev, TypeSafe's System One model, in Claude Code and Codex, plus a study course. In the Ratings folder find the list of rated Jev projects and our eval methodology for user safety and quality.

None of these skills calls Jev, so none needs a TypeSafe key: the LLM in your coding agent does the work. Each skill is its own plugin, named in the table.

| Name | What it does | Get it |
|---|---|---|
| [Jevaluate, privately](jevaluate-private/) | The usual way to rate your own, your team's or a client's project: a verdict and fixes from its code, with nothing published. Run `/jevaluate-private <link or folder>` | Plugin `jevaluate-private` |
| [Jevaluate Publish](jevaluate/) | Rates a community Jev project with the same rubric for this repo's public ratings list, with provenance for every finding | Plugin `jevaluate` |
| [Jevaluate Report](jevaluate-report/) | After you agree with a rating from Jevaluate, privately, writes one file your coding agents work through before a pull request: the verdict, a ranked fix table, and each fix as a change to try with a test to run. Run `/jevaluate-report <repo or rating>` | Plugin `jevaluate-report` |
| [Jevaluate Harness](jevaluate-harness/) | Runs rating rounds, re-rates and rubric tuning for Jevaluate | Plugin `jevaluate-harness` |
| [Jevaluate Eval](jevaluate-eval/) | Tests whether Jevaluate's rubric leads graders to the right answers, before a rubric change reaches any rating | Plugin `jevaluate-eval`; run it from a clone of this repo |
| [Jev Sources](jev-sources/) | Finds the TypeSafe docs, patterns, cookbook and blog sections that answer a Jev question, by keyword and by meaning, and tells your coding agent (Claude or Codex) to read them before any claim | Plugin `jev-sources`. Updated for Jev 1.14, including image input and Box questions |
| [Jev Best Practices Study](study/) | A five-level course: summaries of TypeSafe's cookbooks and docs, then quizzes on the concepts and new glossary terms | A web course, nothing to install. **[Open the Claude artifact](https://claude.ai/artifact/W1pVFeGkbcLzndA5xa1RE9)** (recommended, Claude grades your definitions)<br>[Open in GitHub Pages](https://tiffygk.github.io/jev-mode/study/) |

Jev Lens, which turned images into a JSON state, is retired: Jev reads images directly, and that works better. It's kept, unmaintained, in [`archive/jev-lens`](archive/jev-lens/).

How the Jevaluate skills work together, with diagrams: the [system page](https://tiffygk.github.io/jev-mode/system/).

## Install

This repo is a plugin marketplace for Claude Code and Codex. The `jev-mode` plugin installs every skill. Each skill is also its own plugin. Install `jev-mode` or single plugins: a skill installed both ways loads twice.

In Claude Code:

```
claude plugin marketplace add tiffygk/jev-mode
claude plugin install jev-mode@jev-mode
```

To pick skills instead, use any of these in place of the `jev-mode` line:

```
claude plugin install jev-sources@jev-mode
claude plugin install jevaluate-private@jev-mode
claude plugin install jevaluate-report@jev-mode
claude plugin install jevaluate@jev-mode
claude plugin install jevaluate-harness@jev-mode
claude plugin install jevaluate-eval@jev-mode
```

After installing Jev Sources, ask your agent to refresh Jev Sources once: it runs `refresh.sh --fetch`, which downloads TypeSafe's docs, cookbooks and blog posts into `~/.claude/jev-sources-data`.

In Codex:

```
codex plugin marketplace add tiffygk/jev-mode
codex plugin add jev-mode@jev-mode
```

To pick skills instead, use any of these in place of the `jev-mode` line:

```
codex plugin add jev-sources@jev-mode
codex plugin add jevaluate-private@jev-mode
codex plugin add jevaluate-report@jev-mode
codex plugin add jevaluate@jev-mode
codex plugin add jevaluate-harness@jev-mode
codex plugin add jevaluate-eval@jev-mode
```

To pull later changes in Claude Code, run `claude plugin marketplace update jev-mode`, then update each plugin you installed, such as `claude plugin update jevaluate@jev-mode`. In Codex, run `codex plugin marketplace upgrade jev-mode`, then add each plugin again, such as `codex plugin add jevaluate@jev-mode`.

To install without the plugin system, copy a skill's folder into `~/.claude/skills/` for Claude Code, or `~/.agents/skills/` for Codex:

```
git clone https://github.com/tiffygk/jev-mode
mkdir -p ~/.claude/skills
cp -r jev-mode/jevaluate ~/.claude/skills/
cp -r jev-mode/jevaluate-private ~/.claude/skills/
cp -r jev-mode/jevaluate-harness ~/.claude/skills/
cp -r jev-mode/jevaluate-report ~/.claude/skills/
cp -r jev-mode/jevaluate-eval ~/.claude/skills/
cp -r jev-mode/jev-sources ~/.claude/skills/
cp -r jev-mode/shared ~/.claude/skills/
```

Any other coding harness that loads skills can run them with small changes.

Ratings of community Jev projects are in [`ratings/`](ratings/), released under CC0: use and change them freely.

Not affiliated with TypeSafe. The skills are licensed under [PolyForm Noncommercial 1.0.0](LICENSE.md): free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
