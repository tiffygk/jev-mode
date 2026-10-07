# Contributing

Pull requests are welcome. Every change reaches `main` through a PR, and CI runs the tests and the docs check below.

## Keep the docs from going stale

Three rules keep this repo's docs true as it changes:

1. **One place per fact.** A fact lives in one file, and other files link to it. Tables that come from data are generated, never typed: the ratings table comes from `library.py export`.
2. **No counts or versions in prose.** "19 ratings" or "rubric 2026-09-29" in a sentence goes stale the next time the number moves. Link to the table or file that holds it instead. A quoted, dated sample is fine: it is meant to stay as written.
3. **The root README gives one line per folder.** Each folder's README owns that folder's detail.

## The docs check

[`docs-map.json`](docs-map.json) lists which docs describe which code: the root README lists the skills, each skill's README describes its scripts, and so on. [`scripts/docs_check.py`](scripts/docs_check.py) runs in CI on every pull request and in the local pre-push hook. It fails a change that touches a source but none of the docs that describe it, and it flags counts or versions written into README prose. Test files never need a doc. It also enforces [`retired-names.json`](retired-names.json): once something is renamed, its old name may appear only in the files listed for it, each with a reason. A file that uses an old name in its other, intended sense goes on the list with that reason, and then passes.

When a change needs no doc update, say why in the PR description or a commit message:

```
Docs checked: jevaluate/README.md unchanged because the change is internal to the check
```

When you add a script or a skill, add its rule to `docs-map.json` in the same PR.
