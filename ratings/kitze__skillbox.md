[← All ratings](README.md)

> **kitze/skillbox** at [`cda64ad`](https://github.com/kitze/skillbox/tree/cda64ad331) · agent tool
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - Skillbox, a self-hosted skills library, asks Jev to score every authorized skill description from 0 to 4 against the agent's task in one request and returns the skills scoring 3 or more.
> - It writes atomic Score questions with written levels, keeps task and descriptions in structured state, treats them as untrusted text, reads the typed score, and falls back to search with a stated reason on any failure.
> - It measures no accuracy, sends jev-latest on the direct route, and tests only English text.

## What holds it back

- **Measured in the workflow** (F7): A benchmark script exists but no numbers are published in README or docs. ([`scripts/benchmark-recommendations.ts:88`](https://github.com/kitze/skillbox/blob/cda64ad331/scripts/benchmark-recommendations.ts#L88)). TypeSafe launch post, own evals

**Minor:** Pinned model version (F12); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/kitze__skillbox.md)

