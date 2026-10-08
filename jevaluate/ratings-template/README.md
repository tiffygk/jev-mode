# Jev project ratings

Jev, which TypeSafe launched on September 15, 2026, makes decisions instead of writing text. It answers typed questions with calibrated probabilities, and we're all still working out the frameworks for building with it. TypeSafe has documented a lot of what works. I downloaded and indexed all of its documentation, cookbooks and patterns, and I rate community projects against them.

## Two raters

A project can have two ratings, one from a Claude model and one from a Codex model, each in its own column. Each badge opens that model's rating. Each model rates the code on its own and writes its facts before it sees any earlier rating. Where they disagree, both stay up.

## How projects are rated

These ratings follow TypeSafe's guidelines, not my taste. Every problem cites the code at a pinned commit and links the TypeSafe page it departs from, along with the fix that page recommends. A few rules come from my own testing; those are marked.

When the two raters' verdicts differ, the list shows the higher verdict, marked "Rater disagreement: in review", until I review both ratings, on a regular cadence. After a review, the list shows the verdict I picked: that rater's badge says "used" and the other's "not used".

The Evidence score shows how well a project has measured its results. A project that claims no results needs no evidence and can still earn a 4 (Use it). Evidence changes a verdict in only two cases: results claimed with nothing measured cap it at 3 (Use with a fix), and a 5 (Learn from it) needs strong evidence. Check the score before you use a project, or test the project yourself first.

## If your project is here

The fixes are yours. Everything in this folder is released under CC0: use it, change it, ship it, no credit needed. The fixes come from reading your code and haven't been tested against it.

Open an issue if you disagree with a rating, if you've shipped improvements and want a re-rating, or if you'd like help fixing your project.

## Still improving

The Jevaluate skill is still early and doesn't handle edge cases well. The rubric, the rule set and the eval harness are still being tuned, so the AI raters will get more reliable. Until then, I regularly check new ratings, audit samples of them and rule on every verdict disagreement. As I keep improving it, some ratings will be redone. If one reads as too harsh or too generous, I'm sorry. Tell me in an issue, and it will help the next version.

The goal is a Jev community that uplevels itself, sharing resources built on the best practices TypeSafe has already laid out.
