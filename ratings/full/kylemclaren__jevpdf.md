[← Summary](../kylemclaren__jevpdf.md)

# JevPDF: full rating

**Verdict 4, Use it** · workflow · rated 2026-09-30 at [`7f23037`](https://github.com/kylemclaren/jevpdf/tree/7f23037096) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

JevPDF extracts PDF text locally, then asks Jev one noul per line ("does this line answer the query?") in batches of 16 sharing a page-text state, and ranks and highlights lines by the returned probability. It does this well: narrow self-contained questions, token-limit guards, retries, caching and a near-miss fallback. It claims no measured results and never checks the 0.55 hit threshold against labelled data.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** A proxy forwards each batch of noul questions to api.typesafe.ai systemone with the model set to jev-latest. ([`server/jev-upstream.ts:45`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/server/jev-upstream.ts#L45)) |
| Measured in the workflow (F7) | **no.** No precision, recall or latency numbers; README cost and 150-page timing are estimates. ([`README.md:38`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/README.md#L38), [`src/lib/jev-config.ts:28`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L28)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence) |
| Pinned model version (F12) | **no.** Model is the `jev-latest` alias beside a fixed 0.55 cut-off; cached nouls are keyed on the alias. ([`src/lib/jev-config.ts:6`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L6)). [`models`](https://docs.typesafe.ai/models) |
| Untrusted text treated as data (F22) | **no.** Uploaded PDF text and the query go in unflagged; the question says judge only the quoted line, no test. ([`src/lib/jev-config.ts:56`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L56)). [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13) |
| Non-English handled (F23) | **no.** Arbitrary PDFs are accepted; the sample and demo queries are English and no other language is tested. ([`scripts/make-sample.ts:3`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/scripts/make-sample.ts#L3)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (11) and doesn't apply (8)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. One noul per line: "does the quoted line answer the query?", with true and false criteria spelled out. ([`src/lib/jev-config.ts:52`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L52)) |
| Right primitive (F2) | yes. Yes/no relevance per line is a Noul; no ordered scale or named options are needed. ([`src/lib/jev-config.ts:54`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L54)) |
| Structured state (F3) | yes. State is named fields (query, page, page_text); page_text is one text and each question quotes its own line. ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L93)) |
| Batching (F4) | yes. Up to 16 questions share one state per request, 16 requests in flight. ([`src/lib/jev.ts:70`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L70), [`src/lib/jev-config.ts:25`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L25)) |
| Thresholds in code (F5) | yes. HIT_THRESHOLD 0.55, near-miss floor 0.3 and limit 3 are named constants in one config file. ([`src/lib/jev-config.ts:12`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L12)) |
| No invented values (F6) | yes. Code extracts, groups, ranks and merges lines; Jev only judges relevance. ([`src/lib/results.ts:18`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/results.ts#L18)) |
| Options cover every case (F8) | n.a.. No Choice question is used. |
| An "other" option where needed (F9) | n.a.. No Choice question is used. |
| Evidence recorded evenly (F10) | n.a.. State holds only the query and raw page text, with no per-answer evidence to weigh. ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L93)) |
| Confidence drives action, low (F11) | yes. The noul gates hits at 0.55, ranks them, and shows 0.3 to 0.55 only as near-misses. ([`src/lib/results.ts:28`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/results.ts#L28)) |
| Choice order handled, low (F13) | n.a.. No Choice question is used. |
| Size limits respected (F14) | yes. Guard throws when state plus longest question tops 32k or the total tops 64k tokens. ([`src/lib/jev.ts:112`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L112)) |
| Sample size adequate (F15) | n.a.. No accuracy results claimed. |
| Independent labels (F16) | n.a.. No accuracy results claimed. |
| Held-out result (F17) | n.a.. No accuracy results claimed. |
| Fair baseline (F18) | n.a.. No accuracy results claimed. |
| Typed answers read directly (F19) | yes. Code reads each answer's numeric `noul` field, never reasoning text. ([`src/lib/jev.ts:172`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L172)) |
| Data as fields, not templates (F20) | yes. The line rides in its own `line` field of the instructions object, not spliced into a string. ([`src/lib/jev-config.ts:55`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L55)) |
| No instructions in the state (F21) | yes. State is query, page number and page text only; the task is in the question. ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev.ts#L93)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded and batched, and the one decision is gated on probability, F1-F6, F11 and F19 all yes.
- Fit 3 of 3: a Noul per line fits a yes/no relevance judgment, confidence gates hits and near-misses, and 16 questions share one state per request, F2, F4 and F11.
- Coverage 3 of 3: the stated goal, finding lines that answer a question in other words, is fully built, with exact search, caching, retries and a near-miss fallback around it.
- Evidence n.a. of 3: it reports no accuracy results; its cost and timing figures are estimates from published pricing and limits, F7 no.

## Why this verdict

Verdict 4, Use it: no failed fact caps it, Execution and Fit are both 3, and no accuracy results are claimed, so Evidence is n.a. It is not a 5 because nothing is measured on labeled data and no loop closes (`closes_loop: none`). Failed facts F7, F12, F22 and F23 are fix-only at low stakes. Borderline call: typed workflow rather than demo because code thresholds, merges and ranks the answers before showing them, with stakes low because results stay with the asker.

<details>
<summary><b>Files read (24)</b></summary>

- .env.example -- read
- Dockerfile -- read
- README.md -- read
- scripts/make-sample.ts -- read
- server/index.ts -- read
- server/jev-upstream.ts -- read
- server/typesafe-proxy.ts -- read
- src/App.tsx -- read
- src/components/api-key-dialog.tsx -- read
- src/components/pdf-viewer.tsx -- read
- src/components/search-panel.tsx -- read
- src/components/ui/label.tsx -- read
- src/components/ui/switch.tsx -- read
- src/hooks/use-jev-pdf.ts -- read
- src/lib/api-key.ts -- read
- src/lib/exact.ts -- read
- src/lib/extract.ts -- read
- src/lib/geometry.ts -- read
- src/lib/jev-config.ts -- read
- src/lib/jev.ts -- read
- src/lib/results.ts -- read
- src/lib/types.ts -- read
- src/main.tsx -- read
- vite.config.ts -- read

</details>
