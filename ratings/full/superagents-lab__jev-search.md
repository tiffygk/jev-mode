[← Summary](../superagents-lab__jev-search.md)

# jev-search: full rating

**Verdict 3, Use with a fix** · workflow · rated 2026-10-06 at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe09d1ccfe720f38998f36cc25f4176df) · read: full · rubric 2026-09-29.2 · claude-sonnet-5-5, medium effort

## Summary

Jev Search sends each request to hosted Jev to pick a time window, sources and the engine query, then scores every returned result's relevance with one Noul each. It handles provider fallback, streaming, source overrides and result ordering carefully, and a user can override every inferred filter. It has no measurement of whether Jev's choices or scores are right, ignores Choice confidence, and never lets Jev's uncertainty change an action beyond fixed cut-offs.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Posts state and typed questions to `{baseUrl}/v1/systemone` for intent and relevance ([`src/lib/typesafe.ts:132`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L132)) |
| Measured in the workflow (F7) | **no.** No accuracy, cost or latency numbers on the search task; every test stubs Jev's answers ([`test/pipeline.test.ts:24`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L24)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) |
| Options cover every case, no overlap (F8) | **no.** Window has no option for "last 3 months", which the code expects; 30d would drop older rows ([`src/lib/sources.ts:219`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L219), [`src/lib/candidates.ts:10`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L10)). [`primitives/choice`](https://docs.typesafe.ai/primitives/choice) |
| An "other" option where needed (F9) | **no.** Entity Choice has no none-of-these; a described movie with no title still sends a forced pick to IMDb ([`src/lib/typesafe.ts:346`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L346), [`src/lib/sources.ts:174`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L174)). [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced) |
| Confidence drives action, low (F11) | **no.** Source Noul is gated at 0.6, but window and query Choice picks apply at any confidence ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L140)). [`confidence`](https://docs.typesafe.ai/confidence) |
| Pinned model version (F12) | **no.** Cut-offs 0.6 and 0.3 sit beside the unpinned `jev-latest` alias; no tuning record ([`src/lib/typesafe.ts:73`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L73), [`src/lib/pipeline.ts:86`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L86)). [`models`](https://docs.typesafe.ai/models) |
| Data as fields, not templates, high or low (F20) | **no.** Candidate strings built from the user's request are also spliced in as Choice option text ([`src/lib/typesafe.ts:337`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L337), [`src/lib/typesafe.ts:357`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L357)). [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced) |
| Untrusted text treated as data, high or low (F22) | **no.** Web titles and snippets enter the state unflagged and no test tries steering text ([`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436), [`test/pipeline.test.ts:38`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L38)). [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13) |
| Non-English handled (F23) | **no.** Chinese cues exist but only candidate-building is tested, never Jev's answers on Chinese text ([`src/lib/candidates.ts:13`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L13), [`test/candidates.test.ts:19`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/candidates.test.ts#L19)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (10) and doesn't apply (5)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each question asks one property: recency, one source fit, one candidate pick, one result's topicality ([`src/lib/typesafe.ts:320`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L320), [`src/lib/typesafe.ts:429`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L429)) |
| Right primitive (F2) | yes. Noul for source fit and topicality, Choice for window and candidate pick, no ordered scale needed ([`src/lib/typesafe.ts:320`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L320), [`src/lib/typesafe.ts:428`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L428)) |
| Structured state (F3) | yes. Objects with named fields and candidate IDs; results are addressed by array index, not an id ([`src/lib/typesafe.ts:354`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L354), [`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436)) |
| Batching (F4) | yes. All 15 intent questions share one request; each lane's rows share one relevance request ([`src/lib/typesafe.ts:360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L360), [`src/lib/typesafe.ts:423`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L423)) |
| Thresholds in code (F5) | yes. Named constants hold 0.6 and 0.3; display-only dot cut-offs 0.7 and 0.4 are inline ([`src/lib/pipeline.ts:86`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L86), [`src/components/results.tsx:62`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/components/results.tsx#L62)) |
| No invented values (F6) | yes. Code computes ages and freshness; Jev only picks a window or candidate and judges topicality ([`src/lib/freshness.ts:32`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/freshness.ts#L32), [`src/lib/pipeline.ts:205`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L205)) |
| Evidence recorded evenly (F10) | yes. State holds the request, date, candidates and each result's source, title and snippet, no conclusions ([`src/lib/typesafe.ts:354`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L354)) |
| Choice order handled, low (F13) | n.a.. No decision is a high or very high Choice |
| Size limits respected (F14) | yes. Request capped at 300 characters and 8 rows per lane; snippet length itself is uncapped ([`src/components/search-box.tsx:81`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/components/search-box.tsx#L81), [`src/lib/pipeline.ts:87`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L87)) |
| Sample size adequate (F15) | n.a.. README claims no accuracy result; says percentages are unverified ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)) |
| Independent labels (F16) | n.a.. README claims no accuracy result ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)) |
| Held-out result (F17) | n.a.. README claims no accuracy result ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)) |
| Fair baseline (F18) | n.a.. README claims no accuracy result ([`README.md:138`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L138)) |
| Typed answers read directly (F19) | yes. Code reads `.noul`, `.choice` and `.confidence` fields from the typed answers ([`src/lib/typesafe.ts:362`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L362), [`src/lib/typesafe.ts:453`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L453)) |
| No instructions in the state (F21) | yes. State holds request, date, candidates and result rows only; directions sit in the questions ([`src/lib/typesafe.ts:354`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L354), [`src/lib/typesafe.ts:436`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L436)) |

</details>

## Scores

- Execution 2 of 3: questions are atomic, typed, fielded and batched, but the window, the entity pick and Choice confidence fall short, from F8, F9 and F11.
- Fit 2 of 3: primitives and batching fit, with exactly one mismatch: Choice confidence is read but never gates the window or query pick, from F11.
- Coverage 3 of 3: every goal the README states runs in code: source choice, time range, query choice, relevance ranking and streaming, from the Decisions list.
- Evidence n.a.: the README claims no accuracy result and says its percentages are unverified, from F7 and F15 to F18.

## Why this verdict

Jev picks the time window, sources and query and scores each result, and every pick can be overridden or reviewed, so all five decisions are low. Execution is 2, not 1, because F1 to F6 all hold. F8, F9 and F11 fail and cap it at 3 rather than 4; none is a fatal flaw because no decision is high or very high. The borderline call is stakes: ranking search results is listed as reaching other people, but the asker sees their own results and can unfold any hidden row in one click, so they are low.

## Fixes (from reading the code; not tested against it)

1. **F11:** Gate the window, query and entity picks on [`confidence`](https://docs.typesafe.ai/confidence); below a floor, use "any time" and the original request. Confirm the floor with labeled queries. [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)
2. **F8:** Add windows for spans between 30 days and any time, or ask recency as independent Nouls, so "last 3 months" is not forced into 30d. Confirm with data. [`primitives/choice`](https://docs.typesafe.ai/primitives/choice)
3. **F9:** Add a none-of-these option to the entity Choice, worded unlike the candidates, and fall back to the keyword query. [`primitives/choice`](https://docs.typesafe.ai/primitives/choice)
4. **F7:** Label a sample of requests and results, then report source and relevance precision and recall at 0.6 and 0.3. [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)
5. **F20:** Keep candidate strings in the state only and make the Choice options short labels that point at them. [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced)
6. **F22:** Mark web titles and snippets as untrusted input and test steering snippets before deploying. [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
7. **F12:** Pin the versioned model ID and retune 0.6 and 0.3 after any upgrade. [`models`](https://docs.typesafe.ai/models)
8. **F23:** Test Jev's judgments on Chinese requests and snippets or add a translation beside them. [`concepts/state`](https://docs.typesafe.ai/concepts/state)

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
