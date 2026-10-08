[← Summary](../kitze__skillbox--gpt-6-sol.md)

# skillbox: full rating

**Verdict 4, Use it** · agent tool · rated 2026-10-06 at [`cda64ad`](https://github.com/kitze/skillbox/tree/cda64ad3310abe690c6d497352791da4cfeb9a0a) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Skillbox sends an agent's task and authorized skill descriptions to hosted Jev for relevance scores. Its bounded catalog, validation, permission recheck and explicit search fallback support dependable recommendations. The score cutoff lacks calibration against real agent outcomes.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Sends Score questions to TypeSafe, Vercel Gateway or OpenRouter Jev endpoints ([`src/server/recommendations.ts:138`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L138)). |
| Measured in the workflow (F7) | **no.** A live benchmark script exists, but no result for real agent loads is recorded ([`scripts/benchmark-recommendations.ts:40`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/scripts/benchmark-recommendations.ts#L40)). https://docs.typesafe.ai/cookbooks/skill_suggestion.md |
| Size limits respected (F14) | **no.** A 120,000-character catalog plus repeated questions has no token guard for TypeSafe or Vercel ([`src/server/recommendations.ts:357`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L357)). https://docs.typesafe.ai/models.md |
| Non-English handled (F23) | **no.** English task examples and tests leave non-English tasks unmeasured ([`tests/fixtures/recommendation-cases.ts:34`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/tests/fixtures/recommendation-cases.ts#L34)). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (11) and doesn't apply (9)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each question rates one candidate's usefulness for one task under explicit criteria ([`src/server/recommendations.ts:111`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L111)). |
| Right primitive (F2) | yes. Five described, ordered usefulness levels make Score suitable ([`src/server/recommendations.ts:16`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L16)). |
| Structured state (F3) | yes. Task and each candidate's ID and description are named JSON fields ([`src/server/recommendations.ts:102`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L102)). |
| Batching (F4) | yes. One request carries every candidate question; OpenRouter splits bounded batches ([`src/server/recommendations.ts:110`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L110)). |
| Thresholds in code (F5) | yes. Minimum relevance is a named constant ([`src/server/recommendations.ts:15`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L15)). |
| No invented values (F6) | yes. Jev judges usefulness; code supplies IDs, computes limits, and sorts scores ([`src/server/recommendations.ts:413`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L413)). |
| Options cover every case, no overlap (F8) | n.a.. No Choice questions. |
| An other option where needed (F9) | n.a.. No Choice questions. |
| Evidence recorded evenly (F10) | yes. Every candidate has the same ID and description fields ([`src/server/recommendations.ts:104`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L104)). |
| Confidence drives action, low (F11) | n.a.. The agent receives scores and chooses whether to load ([`src/server/mcp.ts:200`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/mcp.ts#L200)). |
| Pinned model version (F12) | n.a.. The score cutoff was not tuned on observed data ([`src/server/recommendations.ts:15`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L15)). |
| Choice order handled, low (F13) | n.a.. No Choice questions. |
| Sample size adequate (F15) | n.a.. No measured outcome claim. |
| Independent labels (F16) | n.a.. No measured outcome claim. |
| Held-out result (F17) | n.a.. No measured outcome claim. |
| Fair baseline (F18) | n.a.. No measured outcome claim. |
| Typed answers read directly (F19) | yes. The code validates named Score answers and reads their score fields ([`src/server/recommendations.ts:200`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L200)). |
| Data as fields, not templates, low (F20) | yes. Task and descriptions remain in state; question instructions are fixed ([`src/server/recommendations.ts:100`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L100)). |
| No instructions in the state (F21) | yes. State carries task and candidate fields, while rubric directions are in questions ([`src/server/recommendations.ts:102`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/src/server/recommendations.ts#L102)). |
| Untrusted text treated as data, low (F22) | yes. Instructions flag untrusted text and a default test checks injection separation ([`tests/recommendations.test.ts:256`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/tests/recommendations.test.ts#L256)). |

</details>

## Scores

- Execution 3 of 3: atomic per-skill Scores, structured state, batching, a named cutoff and typed answers satisfy the design facts F1–F6, F10 and F19.
- Fit 3 of 3: Score fits ordered relevance, independent candidate questions share a request, and results are returned to the requesting agent, F2, F4 and F11.
- Coverage 2 of 3: broad catalog scoring, no-match and agent-facing suggestions cover three of five skill-suggestion steps; shortlist recheck and measured agent loads are absent.
- Evidence n.a.: no observed result is claimed; the optional benchmark is a script without a recorded run, F7 and F15–F18.

## Why this verdict

Verdict 4 follows from fully typed, batched Scores and an agent-facing result with no capping failure. It does not reach 5 because no labeled outcome evaluation closes the loop. The fixed score cutoff is uncalibrated, but the agent decides whether to load a returned skill. The two code uses of scores filter and order the returned suggestions and have low stakes.

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
