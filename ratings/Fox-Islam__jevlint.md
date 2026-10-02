[← All ratings](README.md)

> **Fox-Islam/jevlint** at [`582c0b8`](https://github.com/Fox-Islam/jevlint/tree/582c0b8be0) · library
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●●○
>
> - A linter that sends a user's Jev query to Jev as state and asks 25 calibrated yes/no checks about it, reporting findings by severity.
>
> **Top fix:** Hold out a slice of the gold and docs tiers that no wording or trigger change ever sees, and report that slice.

## What holds it back

- **Held-out result** (F17): Wordings and triggers were changed after reading the same corpus tiers whose rates are then reported ([`docs/evidence.md:322`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L322)). docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Fair baseline** (F18): Arms compare a check with its repaired query or a coin flip; no rules or LLM baseline ([`docs/evidence.md:944`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L944)). docs.typesafe.ai/concepts/how-to-build-with-system-one

## Fixes (from reading the code; not tested against it)

1. F17: hold out a slice of the gold and docs tiers that no wording or trigger change ever sees, and report that slice. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence).
2. F18: run a keyword-rules linter and a plain-LLM prompt over the same gold set and report both beside the checks. Source: [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook).
3. F12: default the client to a versioned `jev-1.13.x` ID, since triggers were tuned for that build, and log the `model` each response names. Source: [`models`](https://docs.typesafe.ai/models).

**Minor:** Pinned model version (F12); Data as fields, not templates (F20); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/Fox-Islam__jevlint.md)

