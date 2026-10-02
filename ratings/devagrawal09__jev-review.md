[← All ratings](README.md)

> **devagrawal09/jev-review** at [`31f8960`](https://github.com/devagrawal09/jev-review/tree/31f89602797fb7bea007f8a480bf368bf564954e) · workflow
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence n.a.
>
> - It runs a staged code review: five Noul risk screens per file or 160-line region, then evidence-hunk, mechanism, severity and owner questions for the top 8 flagged signals.
> - Calls are narrow with explicit options, thresholds live in one config file in code, and confidence gates the evidence step.
> - It never checks its own results, pins no model, and its saved findings only inform a dashboard.
>
> **Top fix:** Ask each stage over the code itself and its own evidence, and keep the earlier probabilities out of the profile and later states, confirming with data by removing one field at a time and rerunning ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).

## What holds it back

- **Measured in the workflow** (F7): No accuracy, precision or cost numbers on any codebase; README calls it an experiment ([`README.md:78`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L78)). concepts/how-to-build-with-system-one
- **Evidence recorded evenly** (F10): Earlier Jev conclusions (screening probabilities, suspectedConcern with probability) go into later states as facts ([`src/review/judgments.ts:140`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L140)). concepts/state

## Fixes (from reading the code; not tested against it)

1. F10: ask each stage over the code itself and its own evidence, and keep the earlier probabilities out of the profile and later states, confirming with data by removing one field at a time and rerunning ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).
2. F14: filter the profile state to relevant fields, split long patches, and keep state plus the longest question under 32k tokens ([`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13)).
3. F22: flag reviewed code as untrusted, add an injection-check Noul, and test adversarial patches ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13); [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)).

**Minor:** Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/devagrawal09__jev-review.md)

