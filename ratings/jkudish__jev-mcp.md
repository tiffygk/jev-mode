[← All ratings](README.md)

> **jkudish/jev-mcp** at [`fcd18d8`](https://github.com/jkudish/jev-mcp/tree/fcd18d8609ba05a2f1988af91407d86377801ca0) · agent tool
> ### Verdict 3: Use with a fix
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - jev-mcp is an MCP server that gives coding agents twelve Jev judgment tools (verify, screen, find, rerank, classify, decide, compare, extract, audit, review, gate), each one batched request returning typed probabilities plus an auto or review action.
> - Question wording, Choice and Score use, validation that fails closed, and caller-set thresholds are all strong, and the tools keep policy in code.
> - The README reports live captures and one cookbook benchmark figure but no accuracy or calibration measurement of its own, and several cutoffs are fixed in code.
>
> **Top fix:** Move the directives out of the state (F21): drop or replace the `purpose` sentences with a caller-supplied content field, and keep the judgment in the questions.

## What holds it back

- **Measured in the workflow** (F7): README claims 150 to 500 ms and a fraction of a cent with no measurement; only usage captures ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). concepts/how-to-build-with-system-one
- **No instructions in the state** (F21): State carries a `purpose` field with directives like "Verify each claim in claims against the evidence" ([`src/server.ts:230`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L230), [`src/server.ts:1990`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1990)). concepts/state

## Fixes (from reading the code; not tested against it)

1. Move the directives out of the state (F21): drop or replace the `purpose` sentences with a caller-supplied content field, and keep the judgment in the questions. https://docs.typesafe.ai/concepts/state.md
2. Measure the tools (F7, closes_loop none): label a sample of claims, injected pages and classes, report precision and recall at the 0.8 and 0.75 defaults and the real latency, then calibrate. https://docs.typesafe.ai/cookbooks/classification_using_confidence.md (confirmed only with data)
3. Pass caller text as fields (F20): point questions at `claims[i].text`, `query` and `propositions[i]` as jev_classify does. https://docs.typesafe.ai/primitives/advanced.md

**Minor:** Pinned model version (F12); Size limits respected (F14); Data as fields, not templates, high or low (F20); Untrusted text treated as data, high or low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/jkudish__jev-mcp.md)

