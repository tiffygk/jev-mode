[← All ratings](README.md)

> **umatter/jevtools** at [`6ab3541`](https://github.com/umatter/jevtools/tree/6ab35414c8) · library
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ●○○
>
> - Jevtools is a Python library that builds typed Jev questions to choose tools and bind their arguments from candidate pools.
> - It uses hosted Jev backends, typed answers, channel filters and risk-tiered policy.
> - Coverage of open-world values and untuned thresholds limit reliability beyond app-owned domains.
>
> **Top fix:** Separate overlapping tool actions such as `share_file` and `share_report`, or ask independent action Nouls; confirm on the merged catalog.

## What holds it back

- **Options cover every case, no overlap** (F8): A merged catalog offers near-duplicate share_file/share_report actions and yields three wrong shown writes ([`docs/BENCH.md:329`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L329)). https://docs.typesafe.ai/primitives/advanced.md
- **Choice order handled** (F13): Automatic read and external record Choices retain canonical order; reverse probes default only for critical ([`src/jevtools/policy.py:173`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L173)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Held-out result** (F17): Held-out cases were reused to select hybrid decoding, search cues, and present fallback ([`docs/BENCH.md:284`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L284)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Fair baseline** (F18): Reported app-domain comparisons are internal variants and an oracle, without a same-case LLM caller ([`docs/BENCH.md:309`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L309)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md

## Fixes (from reading the code; not tested against it)

1. F8: separate overlapping tool actions such as `share_file` and `share_report`, or ask independent action Nouls; confirm on the merged catalog. Source: https://docs.typesafe.ai/primitives/advanced.md
2. F13: average or randomize order for very high impact Choices, including tool selection and access-granting recipients. Source: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
3. F20: put candidates and draft content in structured state or question fields instead of substituted instruction strings. Source: https://docs.typesafe.ai/primitives/advanced.md

**Minor:** Data as fields, not templates (F20); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/umatter__jevtools--gpt-6-sol.md)

