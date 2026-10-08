# jev-mode

Skills for building with Jev, TypeSafe's System One model. Each skill has its own folder: `jevaluate/`, `jevaluate-harness/`, `jevaluate-eval/`, `jev-lens/`, `jev-sources/`. `ratings/` holds published ratings, `shared/` holds rules more than one skill reads, `study/` is the Cookbook Study site and `system/` its start page.

## Locked files

Everything in `jevaluate/`, `jevaluate-harness/`, `jevaluate-eval/` and `shared/` decides how ratings and evals are scored: the rubric, rater instructions, scripts and eval answer keys. On the owner's machine these files are read-only in the main checkout, and a hook blocks agent edits.

To change one, work on a branch in its own worktree. In a fork, first add the upstream remote:

    git remote add upstream https://github.com/tiffygk/jev-mode
    git worktree add -b <name> ../jev-mode-<name> upstream/main

For any rating rule, follow the rubric-change guide in `jevaluate-harness/`, then open a pull request. The owner merges it.

## Branches and tags

- Never commit on `main`. Open a pull request from a branch; `main` changes only by merged PR.
- The owner sets freeze tags (`rubric-<version>-frozen`, such as `rubric-2026-09-29.2-frozen`) on merged commits. Never create, move or delete one.

## Plans and notes

Plans, specs, handoffs and working notes never go in this repo, not even in an ignored folder. Keep them outside the checkout. This overrides any skill that saves plans to `docs/` by default.

## Before an eval run or a merge

Run `git fetch upstream && git log <branch>..upstream/main -- jevaluate/ jevaluate-harness/`. If another branch changed the rubric or the harness, rebase first. Otherwise the eval's answer key and the rubric can disagree.

## Before a push

Before pushing, run the full test suite (`python3 -m pytest`) and fix any failure. Contributors push to their fork and open a pull request. Its description has a `Scope:` line naming the folders and files it changes; the `pr-contents` check fails on any file outside it, and on any file that reads like a plan or a private note. Run the check's tests with `python3 -m pytest .github/scripts`. Before asking for a merge, confirm every check on the pull request is green. Keep personal names, emails and private notes out of every file. On the owner's machine, a pre-push hook (not part of the clone) refuses private terms and checks freeze tags.

## Ratings

- Rating files are written only by `library.py add`. Never edit one by hand.
- In the ratings library, files sort by date, then the same-day number (`2026-09-28-2` follows `2026-09-28`). Use `library.rating_key`, never a name sort.
- A rating of record uses the rubric version of the newest freeze tag on GitHub. Until that tag exists, `step.py` and `library.py check` refuse to rate.

## Writing in this repo

State each rule plainly, with no person's name attached. No em-dashes. Each skill gets a one-page README of 750 words at most.
