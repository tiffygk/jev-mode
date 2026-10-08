[← Summary](../superagents-lab__jev-search--gpt-6-sol.md)

# jev-search: full rating

**Verdict 2, Rework it** · workflow · rated 2026-10-06 at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe09d1ccfe720f38998f36cc25f4176df) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jev Search uses Jev to choose a search configuration and rank Search1API results. It batches typed judgments, keeps thresholds in code, and lets readers override filters. Ungated Choice decisions and untested search quality limit its reliability.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Posts typed state and questions to TypeSafe; also supports Jev gateway models ([`src/lib/typesafe.ts:132-137`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L132-L137)). |
| Structured state (F3) | **no.** Result objects omit IDs although result questions address array positions; `results` from a lane reaches ranking ([`src/lib/typesafe.ts:426-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L426-L444)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Measured in the workflow (F7) | **no.** Tests use mocked Jev answers; no measured task accuracy, cost or latency is reported ([`test/pipeline.test.ts:16-42`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L16-L42), [`README.md:51`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L51)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Options cover every case, no overlap (F8) | **no.** Original and stripped query candidates overlap for “New papers on speculative decoding,” changing search terms ([`src/lib/candidates.ts:80-102`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L80-L102), [`README.md:19`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L19)). https://docs.typesafe.ai/primitives/advanced.md |
| An "other" option where needed (F9) | **no.** Entity Choice lacks a none option for topic searches without a named entity, affecting IMDb queries ([`src/lib/typesafe.ts:346-351`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L346-L351), [`src/lib/sources.ts:156-165`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L156-L165)). https://docs.typesafe.ai/cookbooks/semantic_find.md |
| Confidence drives action, high or very high (F11) | **no.** Window, keyword and entity Choices act without checking confidence ([`src/lib/pipeline.ts:131-142`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L131-L142)). https://docs.typesafe.ai/confidence.md |
| Choice order handled, high (F13) | **no.** Window and candidate Choices run once in fixed order before routing ([`src/lib/typesafe.ts:318-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L318-L360)). https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md |
| Size limits respected (F14) | **unknown.** `src/lib/validate.ts` and `src/lib/search1api.ts` fetch failed; their input and result caps could answer this ([`src/lib/typesafe.ts:354-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L354-L360), [`src/lib/typesafe.ts:436-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436-L444)). |
| Untrusted text treated as data (F22) | **no.** User request and web snippets enter state without an untrusted marker or steering test ([`src/lib/typesafe.ts:354-358`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L354-L358), [`src/lib/typesafe.ts:436-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436-L444); [`test/typesafe.test.ts:1-274`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/typesafe.test.ts#L1-L274)). https://docs.typesafe.ai/model-jaggedness/jev-1.13.md |
| Non-English handled (F23) | **no.** Chinese candidate stripping is tested, but Jev judgments on non-English requests are not ([`test/candidates.test.ts:19-21`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/candidates.test.ts#L19-L21), [`test/pipeline.test.ts:71-240`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L71-L240)). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (9) and doesn't apply (5)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Window, source, query, entity and per-result relevance are separate judgments ([`src/lib/typesafe.ts:318-352`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L318-L352), [`src/lib/typesafe.ts:426-434`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L426-L434)). |
| Right primitive (F2) | yes. Binary source and relevance checks use Noul; window and candidate selection use Choice ([`src/lib/typesafe.ts:320-350`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L320-L350), [`src/lib/typesafe.ts:427-434`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L427-L434)). |
| Batching (F4) | yes. Intent questions share one request; each lane's relevance questions share one request ([`src/lib/typesafe.ts:316-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L316-L360), [`src/lib/typesafe.ts:423-445`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L423-L445)). |
| Thresholds in code (F5) | yes. Source 0.6 and off-topic 0.3 are named constants ([`src/lib/pipeline.ts:86`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L86), [`src/components/results.tsx:73`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/components/results.tsx#L73)). |
| No invented values (F6) | yes. Code builds candidate strings and calculates dates; Jev selects or judges supplied values ([`src/lib/candidates.ts:80-102`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L80-L102), [`src/lib/freshness.ts:31-55`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/freshness.ts#L31-L55)). |
| Evidence recorded evenly (F10) | yes. Every ranked result carries the same source, title and snippet fields ([`src/lib/typesafe.ts:436-443`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436-L443)). |
| Pinned model version (F12) | n.a.. No threshold tuning is documented ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)). |
| Sample size adequate (F15) | n.a.. No accuracy result claimed ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)). |
| Independent labels (F16) | n.a.. No accuracy result claimed ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)). |
| Held-out result (F17) | n.a.. No accuracy result claimed ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)). |
| Fair baseline (F18) | n.a.. No accuracy result claimed ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)). |
| Typed answers read directly (F19) | yes. Code reads typed Choice and Noul fields and probabilities ([`src/lib/typesafe.ts:362-390`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L362-L390), [`src/lib/typesafe.ts:448-454`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L448-L454)). |
| Data as fields, not templates (F20) | yes. Requests and snippets stay in state; question text contains only fixed paths and indexes ([`src/lib/typesafe.ts:327-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L327-L360), [`src/lib/typesafe.ts:426-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L426-L444)). |
| No instructions in the state (F21) | yes. Intent and relevance state hold content and dates; instructions live in questions ([`src/lib/typesafe.ts:318-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L318-L360), [`src/lib/typesafe.ts:425-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L425-L444)). |

</details>

## Scores

- Execution 2 of 3: Structured result state omits item IDs, and Choice options overlap or lack a none case (F3, F8, F9); confidence does not gate Choices (F11).
- Fit 1 of 3: The typed, batched judgments fit search, but missing result IDs, overlapping candidate Choices and ungated routing are multiple mismatches (F2, F3, F4, F8, F11).
- Coverage 3 of 3: It implements source, window and query selection plus relevance ranking across its listed engines (F0, F4, F5, F19).
- Evidence n.a.: It claims no measured accuracy or comparative result (F7, F15-F18).

## Why this verdict

Jev chooses the search configuration and ranks results, but Choice confidence does not control the high-stakes routing decisions. That F11 failure makes the verdict 2 rather than 3. Overlapping query options and no none case for entity selection add avoidable failure paths.

## Fixes (from reading the code; not tested against it)

1. **F11:** Gate window, keyword and entity Choice actions on confidence; fall back to a wider window or original request when uncertain. Confirm the cutoffs with labeled queries. https://docs.typesafe.ai/confidence.md
2. **F8, F9:** Make candidate options exclusive and add a none case for entity selection; confirm query changes against real searches. https://docs.typesafe.ai/primitives/choice.md
3. **F3:** Add stable IDs to result state and address them explicitly in questions. https://docs.typesafe.ai/concepts/state.md
4. **F13:** Check high-stakes Choices across option orders before trusting a selected route. https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
5. **F7:** Label search requests and results, then report source and relevance precision and recall at the chosen thresholds. https://docs.typesafe.ai/cookbooks/classification_using_confidence.md
6. **F22:** Mark or check steering text in user requests and web snippets, and test adversarial cases. https://docs.typesafe.ai/model-jaggedness/jev-1.13.md
7. **F23:** Test Jev judgments on Chinese and Russian requests and snippets or provide translations beside them. https://docs.typesafe.ai/concepts/state.md

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
