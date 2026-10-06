# Jevaluate, privately

Rate a project you can't publish: a client's codebase, your employer's pipeline, a design you were sent, or your own work in progress. It uses the same rubric, steps and checks as [Jevaluate](../jevaluate/), so a private verdict means what a public one does. The rating stays on your machine.

## Use it

Ask your agent: `/jevaluate-private https://github.com/you/project`, or point it at a folder: `/jevaluate-private ~/work/retrieval-graph`. "Rate this privately" works too.

## How it stays private

- Private ratings live in their own library (`~/.jevaluate-private/` by default), never the public one.
- The skill refuses to log a private rating into a public library, or to export a private library or rating.
- A local folder is read from disk. Nothing in it is fetched from or sent to GitHub.

## Needs

[Jevaluate](../jevaluate/) itself, Python 3.8+, and the GitHub CLI only when you rate a GitHub link.
