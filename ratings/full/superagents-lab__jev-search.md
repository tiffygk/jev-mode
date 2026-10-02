[← Summary](../superagents-lab__jev-search.md)

# jev-search: full rating

**Verdict 3, Use with a fix** · workflow · rated 2026-09-30 at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe0) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Jev Search sends each request to Jev as one set of typed questions that picks a time window, sources and a query, then scores every result as a yes/no relevance question. It does this well: code proposes the query candidates and Jev only selects, the state is small, lanes are scored in parallel and streamed, and three Jev providers fall back on outage. It is held back by ignoring every confidence value Jev returns, by pinning no model version, and by publishing no measured results.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Posts state and typed questions to `{baseUrl}/v1/systemone` for intent and relevance scoring ([`src/lib/typesafe.ts:132`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L132), called at [`src/lib/typesafe.ts:360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L360) and [`src/lib/typesafe.ts:444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L444)) |
| Measured in the workflow (F7) | **no.** No accuracy numbers on its task; tests mock Jev and the README calls scores model judgments (`README.md`, `test/pipeline.test.ts`). docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Confidence drives action, low (F11) | **no.** Window and query Choices act at any probability; relevance (0.3) and source (0.6) gates hold ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L140)). docs.typesafe.ai/confidence |
| Pinned model version (F12) | **no.** Defaults are `jev-latest`, `typesafe-ai/jev` and `typesafe/jev` beside thresholds 0.6 and 0.3 ([`src/lib/typesafe.ts:73`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L73), `wrangler.jsonc:13-15`). docs.typesafe.ai/models |
| Untrusted text treated as data (F22) | **no.** Web titles and snippets and user text enter the state unflagged and no test covers injection ([`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L436), `test/typesafe.test.ts`). docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Chinese candidates and a WeChat source exist, but the tests cover candidate building only, not Jev's answers ([`src/lib/candidates.ts:13`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/candidates.ts#L13), [`test/candidates.test.ts:19`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/test/candidates.test.ts#L19)). docs.typesafe.ai/models |

<details>
<summary><b>What passes (12) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. One property each: one Noul per source, one per result, a window Choice and a query Choice ([`src/lib/typesafe.ts:320-351`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L320-L351), [`src/lib/typesafe.ts:427-434`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L427-L434)) |
| Right primitive (F2) | yes. Noul for yes/no source and relevance questions, Choice for window and candidate pick; the window is named buckets ([`src/lib/typesafe.ts:320`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L320), [`src/lib/typesafe.ts:328`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L328), [`src/lib/typesafe.ts:340`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L340)) |
| Structured state (F3) | yes. State is named fields with ids: `request`, `now`, `candidates.c0..`, and `results[]` with source, title, snippet ([`src/lib/typesafe.ts:354`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L354), [`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L436)) |
| Batching (F4) | yes. All 15 intent questions in one request; each lane's results scored in one request, 40 questions per batch ([`src/lib/typesafe.ts:360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L360), [`src/lib/typesafe.ts:406`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L406)) |
| Thresholds in code (F5) | yes. Named constants `SOURCE_PROB_THRESHOLD` 0.6 and `OFF_TOPIC` 0.3 ([`src/lib/pipeline.ts:86`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L86), `src/components/results.tsx`) |
| No invented values (F6) | yes. Code builds candidates, supplies `now` and computes ages and freshness; Jev only picks or judges ([`src/lib/candidates.ts:80`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/candidates.ts#L80), [`src/lib/freshness.ts:32`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/freshness.ts#L32)) |
| Options cover every case, no overlap (F8) | yes. Windows are any, 24h, 7d, 30d with distinct descriptions; candidates always include the untouched request ([`src/lib/sources.ts:236`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/sources.ts#L236), [`src/lib/candidates.ts:90`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/candidates.ts#L90)) |
| An other option where needed (F9) | n.a.. Every Choice already covers every case: window has `any` and the query Choice always holds the original request ([`src/lib/candidates.ts:90`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/candidates.ts#L90)) |
| Evidence recorded evenly (F10) | yes. Each source question gives both a yes and a no criterion; every result carries the same three fields ([`src/lib/typesafe.ts:331`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L331), [`src/lib/typesafe.ts:438`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L438)) |
| Choice order handled (F13) | n.a.. No high-stakes Choice: every decision is low ([`src/lib/pipeline.ts:241`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L241)) |
| Size limits respected (F14) | yes. Search text capped at 300 characters and results scored in batches of 40, so state stays small ([`src/routes/search.tsx:32`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/routes/search.tsx#L32), [`src/lib/typesafe.ts:406`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L406)) |
| Sample size adequate (F15) | n.a.. No results are claimed; the README disclaims verified accuracy (`README.md`) |
| Independent labels (F16) | n.a.. No results claimed (`README.md`) |
| Held-out result (F17) | n.a.. No results claimed (`README.md`) |
| Fair baseline (F18) | n.a.. No results claimed (`README.md`) |
| Typed answers read directly (F19) | yes. Code reads `noul`, `choice` and [`confidence`](https://docs.typesafe.ai/confidence) fields of each answer ([`src/lib/typesafe.ts:362-392`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L362-L392), [`src/lib/typesafe.ts:453`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L453)) |
| Data as fields, not templates (F20) | yes. Request and results sit in the state; questions point at `request` and `results[i]` ([`src/lib/typesafe.ts:329`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L329), [`src/lib/typesafe.ts:429`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L429)) |
| No instructions in the state (F21) | yes. State holds the request, date, candidates and result fields only ([`src/lib/typesafe.ts:354`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L354), [`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/typesafe.ts#L436)) |

</details>

## Scores

- Execution 2 of 3: questions are atomic, typed, fielded and batched with thresholds in named constants (F1-F6, F8, F10, F19 yes), but F11 is no on the low window and query Choices; the relevance decision is gated.
- Fit 2 of 3: one mismatch, the top Choice answer for window, query and entity is acted on at any confidence, where the code reads [`confidence`](https://docs.typesafe.ai/confidence) and drops it (F11 covers only the gated relevance and source decisions).
- Coverage 3 of 3: every step the README promises runs, from choosing sources, window and query to scoring and ranking results, with a failed source shown as a warning.
- Evidence n.a.: it claims no results and says percentages are model judgments, not verified accuracy (F7 no, F15-F18 n.a.).

## Why this verdict

Verdict 3, Use with a fix: F11 fails on the low window and query Choices, which act at any confidence, and that caps the verdict at 3. Execution is 2 and Fit is 2. F22 fails but only caps at very high stakes, and every decision is low. Ranking results for the person who searched is low, and the window, source and query decisions are low because chips show each choice and one click overrides it.

## Fixes (from reading the code; not tested against it)

1. F11, confidence ignored on the window and query Choices ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L140)): fall back to `any` and to `c0` below a confidence constant ([`confidence`](https://docs.typesafe.ai/confidence)).
2. F7, nothing measured: label real requests and report source-choice and relevance precision and recall ([`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)). Needs data to confirm.
3. F12, model alias: pin the versioned model once thresholds are tuned ([`models`](https://docs.typesafe.ai/models)).
4. F22, steering text unflagged: add an injection-check Noul and adversarial tests ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13)).
5. F23, non-English untested through Jev ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).

<details>
<summary><b>Files read (46)</b></summary>

- .dev.vars.example -- read
- .env.example -- read
- CONTRIBUTING.md -- read
- README.md -- read
- design-context.md -- read
- package.json -- read
- src/components/filters.tsx -- read
- src/components/home-demos.tsx -- read
- src/components/logo.tsx -- read
- src/components/pwa-register.tsx -- read
- src/components/repository-link.tsx -- read
- src/components/results.tsx -- read
- src/components/search-box.tsx -- read
- src/components/source-icon.tsx -- read
- src/components/sponsor-link.tsx -- read
- src/components/wordmark.tsx -- read
- src/components/working.tsx -- read
- src/lib/candidates.ts -- read
- src/lib/freshness.ts -- read
- src/lib/judge-config.ts -- read
- src/lib/merge.ts -- read
- src/lib/pipeline.ts -- read
- src/lib/rank.ts -- read
- src/lib/sources.ts -- read
- src/lib/stable-order.ts -- read
- src/lib/typesafe.ts -- read
- src/lib/use-ask.ts -- read
- src/lib/use-stable-order.ts -- read
- src/lib/utils.ts -- read
- src/routes/__root.tsx -- read
- src/routes/api/ask.ts -- read
- src/routes/index.tsx -- read
- src/routes/search.tsx -- read
- src/server/env.server.ts -- read
- test/candidates.test.ts -- read
- test/filters.test.ts -- read
- test/freshness.test.ts -- read
- test/judge-config.test.ts -- read
- test/merge.test.ts -- read
- test/pipeline.test.ts -- read
- test/rank.test.ts -- read
- test/results.test.ts -- read
- test/search-timeout.test.ts -- read
- test/stable-order.test.ts -- read
- test/typesafe.test.ts -- read
- wrangler.jsonc -- read

</details>
