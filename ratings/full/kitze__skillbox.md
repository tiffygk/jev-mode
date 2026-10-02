[← Summary](../kitze__skillbox.md)

# skillbox: full rating

**Verdict 4, Use it** · agent tool · rated 2026-09-30 at [`cda64ad`](https://github.com/kitze/skillbox/tree/cda64ad331) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Skillbox, a self-hosted skills library, asks Jev to score every authorized skill description from 0 to 4 against the agent's task in one request and returns the skills scoring 3 or more. It writes atomic Score questions with written levels, keeps task and descriptions in structured state, treats them as untrusted text, reads the typed score, and falls back to search with a stated reason on any failure. It measures no accuracy, sends jev-latest on the direct route, and tests only English text.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** evaluateJev posts one Score question per skill to TypeSafe, OpenRouter or Vercel gateway Jev endpoints. ([`src/server/recommendations.ts:138`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L138)) |
| Measured in the workflow (F7) | **no.** A benchmark script exists but no numbers are published in README or docs. ([`scripts/benchmark-recommendations.ts:88`](https://github.com/kitze/skillbox/blob/cda64ad331/scripts/benchmark-recommendations.ts#L88)). TypeSafe launch post, own evals |
| Pinned model version (F12) | **no.** Direct TypeSafe sends jev-latest and Gateway sends typesafe-ai/jev; only OpenRouter pins 1.13. ([`src/server/recommendations.ts:164`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L164)). [`models`](https://docs.typesafe.ai/models) |
| Non-English handled (F23) | **no.** All fixtures and tasks are English; no non-English test or English-only statement. ([`tests/fixtures/recommendation-cases.ts:44`](https://github.com/kitze/skillbox/blob/cda64ad331/tests/fixtures/recommendation-cases.ts#L44)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (12) and doesn't apply (8)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. One Score per skill on usefulness for the task, judged against five written levels. ([`src/server/recommendations.ts:16`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L16)) |
| Right primitive (F2) | yes. An ordered relevance scale is a Score, and its levels are situations with no numbers. ([`src/server/recommendations.ts:16`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L16)) |
| Structured state (F3) | yes. State holds task and a skills array of candidate label, id and description; each question names its candidate. ([`src/server/recommendations.ts:102`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L102)) |
| Batching (F4) | yes. All candidates go in one request; OpenRouter splits into 32-skill batches, two at a time. ([`src/server/recommendations.ts:110`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L110)) |
| Thresholds in code (F5) | yes. MIN_RELEVANCE, MAX_CANDIDATES and DEADLINE_MS are named constants. ([`src/server/recommendations.ts:11`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L11)) |
| No invented values (F6) | yes. Jev only rates relevance; code validates range, filters, sorts and pages. ([`src/server/recommendations.ts:413`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L413)) |
| Options cover every case, no overlap (F8) | n.a.. No Choice question is used. |
| An "other" option where needed (F9) | n.a.. No Choice question is used. |
| Evidence recorded evenly (F10) | yes. Every skill carries the same two fields, id and description, and no conclusions. ([`src/server/recommendations.ts:104`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L104)) |
| Confidence drives action, low (F11) | n.a.. The only decision is low and its answer is filtered and returned; confidence is unused. ([`src/server/recommendations.ts:413`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L413)) |
| Choice order handled, low (F13) | n.a.. No Choice question is used. |
| Size limits respected (F14) | yes. Over 200 skills or 120,000 characters falls back to search; OpenRouter batches cap at 24,000 bytes. ([`src/server/recommendations.ts:356`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L356)) |
| Sample size adequate (F15) | n.a.. No results are claimed. |
| Independent labels (F16) | n.a.. No results are claimed. |
| Held-out result (F17) | n.a.. No results are claimed. |
| Fair baseline (F18) | n.a.. No results are claimed. |
| Typed answers read directly (F19) | yes. Code reads each answer's numeric score field and never parses text. ([`src/server/recommendations.ts:208`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L208)) |
| Data as fields, not templates (F20) | yes. Task and descriptions sit in the state; the question text only splices a code-made label. ([`src/server/recommendations.ts:110`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L110)) |
| No instructions in the state (F21) | yes. The state holds task and skill fields only. ([`src/server/recommendations.ts:102`](https://github.com/kitze/skillbox/blob/cda64ad331/src/server/recommendations.ts#L102)) |
| Untrusted text treated as data (F22) | yes. Questions mark task and descriptions as untrusted; a fixture and a test cover injection. ([`tests/recommendations.test.ts:256`](https://github.com/kitze/skillbox/blob/cda64ad331/tests/recommendations.test.ts#L256)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded and batched, and the facts that apply to a low-stakes returned answer hold, from atomic questions (F1), right primitive (F2), structured state (F3), batching (F4), thresholds in code (F5), no invented values (F6), even evidence (F10) and typed answers read directly (F19).
- Fit 3 of 3: a Score fits an ordered relevance judgment, every skill rides in one request, and no action depends on confidence because the answer is only filtered and returned, so batching (F4) and right primitive (F2) carry it.
- Coverage 3 of 3: the stated goal, ranking the owner's authorized skills for a task with an explicit search fallback, is fully implemented, with limits, caching, revision checks and a test for each documented behavior.
- Evidence n.a.: the README claims no accuracy, calibration or latency results and calls its benchmark a small synthetic sample, so F7 stays a listed fix without a score.

## Why this verdict

No fact that applies fails in F1-F6, F8-F11, F19 or F21, so nothing caps the verdict at 3, and nothing sends it to 2. It is a 4 rather than a 5 because it measures no selection accuracy and never closes a loop on labels. F11 is n.a. because the only decision is low and its filtered answer is returned to the calling agent, not acted on. F12 (floating model on two of three routes) and F23 (English-only tests) are listed fixes that move nothing.

<details>
<summary><b>Files read (49)</b></summary>

- Dockerfile -- read
- README.md -- read
- SECURITY.md -- read
- deploy/umbrel/README.md -- read
- docs/deployment.md -- read
- docs/open-source-readiness.md -- read
- docs/self-hosting.md -- read
- package.json -- read
- scripts/benchmark-recommendations.ts -- read
- scripts/export.ts -- read
- scripts/import.ts -- read
- scripts/install-client.py -- read
- scripts/package-umbrel.ts -- read
- scripts/share-client-skills.py -- read
- scripts/test-self-hosting.py -- read
- src/client/access-pages.tsx -- read
- src/client/executor-settings.tsx -- read
- src/client/gateway-settings.tsx -- read
- src/client/github-import.tsx -- read
- src/client/main.tsx -- read
- src/client/skill-icon.tsx -- read
- src/client/skill-metrics.tsx -- read
- src/client/skill-reference.tsx -- read
- src/package-metrics.ts -- read
- src/server/access.ts -- read
- src/server/app.ts -- read
- src/server/auth.ts -- read
- src/server/db.ts -- read
- src/server/executor.ts -- read
- src/server/gateway.ts -- read
- src/server/github-import.ts -- read
- src/server/index.ts -- read
- src/server/library.ts -- read
- src/server/mcp.ts -- read
- src/server/recommendations.ts -- read
- src/server/schema.ts -- read
- src/server/skill-resources.ts -- read
- src/shared.ts -- read
- src/skill-manifest.ts -- read
- src/skill-references.ts -- read
- tests/fixtures/recommendation-cases.ts -- read
- tests/github-import.test.ts -- read
- tests/library.test.ts -- read
- tests/openrouter.test.ts -- read
- tests/package.test.ts -- read
- tests/recommendations.test.ts -- read
- tests/self-hosting.test.ts -- read
- tests/skill-manifest.test.ts -- read
- tests/skill-references.test.ts -- read

</details>
