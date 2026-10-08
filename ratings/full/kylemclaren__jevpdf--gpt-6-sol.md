[← Summary](../kylemclaren__jevpdf--gpt-6-sol.md)

# jevpdf: full rating

**Verdict 3, Use with a fix** · display · rated 2026-10-06 at [`7f23037`](https://github.com/kylemclaren/jevpdf/tree/7f230370961c4a8e2f8b19c1729085b852124448) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

JevPDF asks hosted Jev whether each extracted PDF line answers a reader's query, then displays ranked highlights. Its narrow Noul questions, batching, local extraction, and visible confidence support the search task. The fixed thresholds and lack of measured retrieval quality limit confidence in its matches.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The app proxy posts batched Noul questions and page text to TypeSafe ([`server/jev-upstream.ts:45`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/server/jev-upstream.ts#L45)). |
| Structured state (F3) | **no.** Page lines are joined into untagged `page_text`; questions repeat text without pointing to line IDs ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L93)). https://docs.typesafe.ai/concepts/state |
| Measured in the workflow (F7) | **no.** The README claims speed and cost, but provides no task measurements ([`README.md:47`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L47)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Untrusted text treated as data (F22) | **no.** An uploaded PDF reaches `page_text` without source flag or steering test ([`src/lib/jev.ts:96`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L96)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** The PDF picker accepts arbitrary PDFs, with no translation or language test ([`src/App.tsx:41`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/App.tsx#L41)). https://docs.typesafe.ai/models |

<details>
<summary><b>What passes (9) and doesn't apply (10)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each Noul judges whether one quoted line answers the query ([`src/lib/jev-config.ts:56`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L56)). |
| Right primitive (F2) | yes. A yes/no relevance judgment uses Noul ([`src/lib/jev-config.ts:54`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L54)). |
| Batching (F4) | yes. Up to 16 independent line questions share each request's page context ([`src/lib/jev.ts:70`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L70)). |
| Thresholds in code (F5) | yes. Named hit and near-miss cutoffs live in config ([`src/lib/jev-config.ts:12`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L12)). |
| No invented values (F6) | yes. Jev only judges relevance; code computes ranks and display values ([`src/lib/results.ts:95`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/results.ts#L95)). |
| Options cover every case (F8) | n.a.. No Choice questions ([`src/lib/jev-config.ts:54`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L54)). |
| Other option (F9) | n.a.. No Choice questions ([`src/lib/jev-config.ts:54`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L54)). |
| Evidence recorded evenly (F10) | n.a.. Each question judges one line with shared page context ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L93)). |
| Confidence drives action (F11) | n.a.. Answers only control the asker's display ([`src/lib/results.ts:28`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/results.ts#L28)). |
| Pinned model version (F12) | n.a.. No threshold tuning shown ([`src/lib/jev-config.ts:12`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L12)); alias `jev-latest` remains a fix. |
| Choice order handled (F13) | n.a.. No Choice questions ([`src/lib/jev-config.ts:54`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L54)). |
| Size limits respected (F14) | yes. Requests guard both documented token ceilings before sending ([`src/lib/jev.ts:107`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L107)). |
| Sample size adequate (F15) | n.a.. No accuracy results claimed ([`README.md:37`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L37)). |
| Independent labels (F16) | n.a.. No accuracy results claimed ([`README.md:37`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L37)). |
| Held-out result (F17) | n.a.. No accuracy results claimed ([`README.md:37`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L37)). |
| Fair baseline (F18) | n.a.. No accuracy results claimed ([`README.md:37`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L37)). |
| Typed answers read directly (F19) | yes. Code reads each named answer's `noul` field ([`src/lib/jev.ts:171`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L171)). |
| Data as fields (F20) | yes. Query is in state, and line text is a structured instruction field ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L93), [`src/lib/jev-config.ts:57`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev-config.ts#L57)). |
| No instructions in state (F21) | yes. State contains only query, page number, and page text ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L93)). |

</details>

## Scores

- Execution 2 of 3: one core structure flaw leaves page lines untagged in state; F3 is no while F1, F2, F4, F5, F6 and F19 hold.
- Fit 3 of 3: independent Nouls, shared page state, and confidence based display fit line search; F2, F4, F5 and F19 hold.
- Coverage 3 of 3: local extraction, meaning search, exact search and highlights cover the stated text-PDF task; F1, F4 and F19 hold.
- Evidence 0 of 3: speed and cost claims have no project measurements, labels, or retrieval comparison; F7 is no.

## Why this verdict

**3 — Use with a fix.** F3 caps the verdict because shared page text lacks item IDs and the questions do not point into it. Execution remains 2, so the project does not meet the 4 anchor, while its narrow Nouls and bounded batches avoid a fatal flaw. The unmeasured speed and cost claims leave Evidence at 0.

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
