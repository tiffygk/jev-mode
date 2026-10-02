[← All ratings](README.md)

> **qkal/Canny** at [`f2c5e53`](https://github.com/qkal/Canny/tree/f2c5e53779) · workflow
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●●○
>
> - Canny is a hook layer for Claude Code and Codex CLI that asks Jev two kinds of yes/no question: whether the agent's last message claims it is done, and whether an edit breaks a project rule.
> - It keeps facts in code and lets Jev only relax a block or add a note, with 0.9 and 0.1 cut-offs, a content-hash cache and a replayable ledger.
> - The model is the unpinned `jev-latest` alias, and the agent's own text goes in unflagged.
>
> **Top fix:** Flag the agent's message and diff as untrusted, add an injection-check Noul, or test a steering message against `claims_done`.

## What holds it back

Nothing that lowers the verdict.

## Fixes (from reading the code; not tested against it)

1. F22: flag the agent's message and diff as untrusted, add an injection-check Noul, or test a steering message against `claims_done`. Confirm with data. [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13); [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages).
2. F12: default to a versioned model ID, log the returned `model`, and retune 0.9 and 0.1 after upgrades. [`models`](https://docs.typesafe.ai/models).
3. Loop: label a small set of done-claims and rule breaks, then derive the cut-offs from the observed probabilities. [`confidence`](https://docs.typesafe.ai/confidence); [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).

**Minor:** Pinned model version (F12); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/qkal__Canny.md)

