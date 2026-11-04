# Jevaluate-private

Updated private version of Jevaluate for how devs and teams build and eval their own projects. Rate a project you can't publish: a client's codebase, your employer's pipeline, a design you were sent, or your own work in progress. It uses the same rubric, steps and checks as [Jevaluate](../jevaluate/), so a private verdict means the same a public one does. The rating stays on your machine, so the skill doesn't load the publish steps of Jevaluate. 

After receiving your Jevaluate-private rating:
- Read the verdict and tune the rating at the end to your own product judgement by conferring with the skill, as the rater may have missed some of your API calls or made calls you don't agree with.
-  Run Jevaluate-report to generate a ready to work off of md file for your agents to incorporate and test proposed improvements to your Jev project

How is this different than Jevaluate (classic)?
Jevaluate classic is meant to be used as a comprehensive rating of a project that publishes to the ratings page of this repo, so the community can separate quality Jev integrations. Jevaluate classic ratings should not be tuned as they are an unbiased eval for the community.

## Use it

Ask your agent to run `jevaluate-private https://github.com/you/project`, or give it a folder: `jevaluate-private ~/work/retrieval-graph`. "Rate this privately" works too.

## How it stays private

- Private ratings live in their own library (`~/.jevaluate-private/` by default), never the public one.
- The skill refuses to log a private rating into a public library, or to export a private library or rating.
- A local folder is read from disk. Nothing in it is fetched from or sent to GitHub.

## Needs

Claude Code or Codex, [Jevaluate](../jevaluate/) itself, Python 3.8+, and the GitHub CLI only when you rate a GitHub link. In Codex, approve the prompt to save to the private library, which sits outside your project folder.
