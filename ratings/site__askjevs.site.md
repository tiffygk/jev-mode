[← All ratings](README.md)

> **Ask Jevs** [https://askjevs.site/](https://askjevs.site/), site-snapshot-2026-10-05 · workflow
> ### Verdict 2: Rework it
> Execution ●○○ · Fit ●○○ · Coverage ●○○ · Evidence ●○○
>
> - Ask Jevs sends each visitor question through one Jev request that sorts it by kind and marks its alternatives, then a second request that picks, confirms or rates, and shows every Jev reply.
> - It batches its independent questions, uses fitting primitives, reads typed answers directly and shows its work.
> - It passes the visitor's raw question to Jev with no standard, offers overlapping or incomplete alternatives, mixes directions into the state, and gates nothing on probability.

## What holds it back

- **Atomic questions** (F1): The raw visitor question is the yes Noul, with no standard: "Is a hot dog a sandwich?" (`files/ask.js:10`). Jev docs: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Thresholds in code** (F5): The server holds the cut-off, about 0.8 in the captures; fetch failed for limits.mjs, api/jevs.js and server.mjs, all 404 (`responses/11.json:8`)
- **Measured in the workflow** (F7): No accuracy, cost or latency figures; the page only prints per-ask milliseconds and tokens (`files/ask.js:137`). Jev docs: evals
- **Options cover every case, no overlap** (F8): Kind's choice and noul options overlap: "da Vinci or Raphael" scored choice 0.58, noul 0.41 (`responses/02.json`). Jev docs: primitives/advanced
- **An "other" option where needed** (F9): Visitor alternatives get no "none of these": "star or planet" picked planet at 1.00 (`responses/13.json:8`). https://docs.typesafe.ai/primitives/advanced.md
- **Confidence drives action, low** (F11): Kind routes at 0.47 and a coin-flip refund answer shows; the page never reads lowConfidence (`responses/05.json`). Jev docs: confidence
- **No instructions in the state** (F21): state.rules holds directions for the word questions; the answer-step context says "Answer from general knowledge" (`responses/01.json`). Jev docs: concepts/state

**Minor:** Pinned model version (F12); Data as fields, not templates (F20); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/site__askjevs.site.md)

