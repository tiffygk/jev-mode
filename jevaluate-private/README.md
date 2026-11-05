# Jevaluate-private

Updated private version of Jevaluate for how devs and teams build and eval their own projects. Rate a project you can't publish: a client's codebase, your employer's pipeline, a design you were sent, or your own work in progress. It uses the same rubric, steps and checks as [Jevaluate Publish](../jevaluate/), so a private verdict means the same as a public one. The rating stays on your machine, so the skill skips the publishing steps.

After you get your rating:
- Read the verdict and tune the rating to your own product judgment by talking it through with the skill. The rater may have missed some of your API calls, or made calls you don't agree with.
- Run [Jevaluate Report](../jevaluate-report/) to write a Markdown file of the proposed fixes, which your agents build and test in your Jev project.

How is this different from Jevaluate Publish?
Jevaluate Publish rates a project in full and publishes the rating to this repo's ratings page, so the community can find the quality Jev integrations. Its ratings shouldn't be tuned, since they are an unbiased eval for the community.

## Use it

Ask your agent to run `jevaluate-private https://github.com/you/project`, or give it a folder: `jevaluate-private ~/work/retrieval-graph`. "Rate this privately" works too.

## How it stays private

- Private ratings live in their own library (`~/.jevaluate-private/` by default), never the public one.
- The skill refuses to log a private rating into a public library, or to export a private library or rating.
- A local folder is read from disk. Nothing in it is fetched from or sent to GitHub.

## Install

Needs Claude Code or Codex, [Jevaluate Publish](../jevaluate/), Python 3.8+, and the GitHub CLI only when you rate a GitHub link. In Codex, approve the prompt to save to the private library, which sits outside your project folder.

In Claude Code:

```
claude plugin marketplace add tiffygk/jev-mode
claude plugin install jevaluate-private@jev-mode
claude plugin install jevaluate@jev-mode
```

In Codex:

```
codex plugin marketplace add tiffygk/jev-mode
codex plugin add jevaluate-private@jev-mode
codex plugin add jevaluate@jev-mode
```

To install every jev-mode skill at once, or to copy skills by hand, see the [repo README](../README.md#install).
