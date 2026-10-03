# Jev Mode

Skills for Claude Code and Codex, and a study course, for building with Jev, TypeSafe's System One model. Not every skill calls Jev: some are guides and evaluators for building with it. The table says which, and each folder's README gives the details.

| Name | What it does | Calls Jev | Status |
|---|---|---|---|
| [Jevaluate](jevaluate/) | Reads a Jev project's code and rates how well it uses Jev, with provenance for every finding | No: an evaluator that runs on the LLM alone | Available |
| [Jev Lens](jev-lens/) | Turns images into a neutral JSON state that Jev can read, one shared schema across the set | Only for an optional check of the finished state | Available |
| [Jevaluate Harness](jevaluate-harness/) | Runs rating rounds, re-rates and rubric calibration for Jevaluate | No | Available |
| [Jevaluate Eval](jevaluate-eval/) | Tests whether Jevaluate's rubric leads graders to the right answers, before a rubric change reaches any rating | No | Available |
| [Jev Sources](jev-sources/) | Finds the TypeSafe docs and cookbook sections that answer a Jev question, and makes Claude read them before any claim | No | Available |
| [Jev Best Practices Study](study/) | A five-level course: summaries of TypeSafe's cookbooks and docs, then quizzes on the concepts and new glossary terms | No: a web course, nothing to install | **[Open the Claude artifact](https://claude.ai/artifact/W1pVFeGkbcLzndA5xa1RE9)** (recommended, Claude grades your definitions)<br>[Open in GitHub Pages](https://tiffygk.github.io/jev-mode/study/) |

Take the course as the Claude artifact when you can: Claude grades your glossary definitions on meaning, while the GitHub Pages copy uses an untested keyword check.

How the three Jevaluate skills work together, with diagrams: the [system page](https://tiffygk.github.io/jev-mode/system/).

## Install

This repo is a plugin marketplace for Claude Code and Codex. It has two plugins:

- `jevaluate`: the Jevaluate and Jevaluate Harness skills
- `jev-lens`: the Jev Lens skill

In Claude Code:

```
claude plugin marketplace add tiffygk/jev-mode
claude plugin install jevaluate@jev-mode
claude plugin install jev-lens@jev-mode
```

In Codex:

```
codex plugin marketplace add tiffygk/jev-mode
codex plugin add jevaluate@jev-mode
codex plugin add jev-lens@jev-mode
```

Pull later changes with `claude plugin marketplace update jev-mode` or `codex plugin marketplace upgrade jev-mode`.

Jev Sources installs by copy only. To install without the plugin system, copy a skill's folder into `~/.claude/skills/`:

```
git clone https://github.com/tiffygk/jev-mode
cp -r jev-mode/jevaluate ~/.claude/skills/
cp -r jev-mode/jev-lens ~/.claude/skills/
cp -r jev-mode/jevaluate-harness ~/.claude/skills/
cp -r jev-mode/jevaluate-eval ~/.claude/skills/
cp -r jev-mode/jev-sources ~/.claude/skills/
cp -r jev-mode/shared ~/.claude/skills/
```

Any other coding harness that loads skills can run them with small changes.

Ratings of community Jev projects are in [`ratings/`](ratings/), released under CC0: use and change them freely.

Not affiliated with TypeSafe. The skills are licensed under [PolyForm Noncommercial 1.0.0](LICENSE.md): free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
