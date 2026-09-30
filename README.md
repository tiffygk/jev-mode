# Jev Mode

Skills for Claude Code and Codex, and a study course, for building with Jev, TypeSafe's System One model. Not every skill calls Jev: some are guides and evaluators for building with it. The table says which, and each folder's README gives the details.

| Name | What it does | Calls Jev | Status |
|---|---|---|---|
| [Jevaluate](jevaluate/) | Reads a Jev project's code and rates how well it uses Jev, with provenance for every finding | No: an evaluator that runs on the LLM alone | Available |
| [Jev Lens](jev-lens/) | Turns images into a neutral JSON state that Jev can read, one shared schema across the set | Only for an optional check of the finished state | Available |
| [Jevaluate Harness](jevaluate-harness/) | Runs rating rounds, re-rates and rubric calibration for Jevaluate | No | Available |
| [Jev Best Practices Study](study/) | A five-level course: summaries of TypeSafe's cookbooks and docs, then quizzes on the concepts and new glossary terms | No: a web course, nothing to install | **[Open the Claude artifact](https://claude.ai/artifact/W1pVFeGkbcLzndA5xa1RE9)** (recommended, Claude grades your definitions)<br>[Open in GitHub Pages](https://tiffygk.github.io/jev-mode/study/) |

Take the course as the Claude artifact when you can: Claude grades your glossary definitions on meaning, while the GitHub Pages copy uses an untested keyword check.

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

Any other coding harness that loads skills can run them with small changes.

Ratings of community Jev projects are in [`ratings/`](ratings/), released under CC0: use and change them freely.

Not affiliated with TypeSafe. The skills are licensed under [PolyForm Noncommercial 1.0.0](LICENSE.md): free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
