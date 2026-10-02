[← Summary](../jkudish__jev-mcp.md)

# jev-mcp: full rating

**Verdict 3, Use with a fix** · agent tool · rated 2026-09-30 at [`fcd18d8`](https://github.com/jkudish/jev-mcp/tree/fcd18d8609ba05a2f1988af91407d86377801ca0) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

jev-mcp is an MCP server that gives coding agents twelve Jev judgment tools (verify, screen, find, rerank, classify, decide, compare, extract, audit, review, gate), each one batched request returning typed probabilities plus an auto or review action. Question wording, Choice and Score use, validation that fails closed, and caller-set thresholds are all strong, and the tools keep policy in code. The README reports live captures and one cookbook benchmark figure but no accuracy or calibration measurement of its own, and several cutoffs are fixed in code.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Every tool sends state and questions to TypeSafe direct, or to OpenRouter, Cloudflare or Vercel gateway slugs ([`src/server.ts:211`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L211), [`src/server.ts:939`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L939)) |
| Measured in the workflow (F7) | **no.** README claims 150 to 500 ms and a fraction of a cent with no measurement; only usage captures ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). concepts/how-to-build-with-system-one |
| Pinned model version (F12) | **no.** Default is the `jev-latest` alias beside 0.85 and 0.5 defaults said to come from spike testing ([`src/server.ts:86`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L86), [`README.md:341`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L341)). docs.typesafe.ai/models.md |
| Size limits respected (F14) | **no.** Per-field character caps exist, but worst-case gate state (about 380k characters) can exceed 64k tokens; no token guard ([`src/lib.ts:258`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L258), [`src/lib.ts:261`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L261)). docs.typesafe.ai/models.md |
| Data as fields, not templates, high or low (F20) | **no.** Query, claim, proposition and candidate text are spliced into question strings ([`src/server.ts:435`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L435), [`src/server.ts:510`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L510), [`src/server.ts:939`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L939)). primitives/advanced |
| No instructions in the state (F21) | **no.** State carries a `purpose` field with directives like "Verify each claim in claims against the evidence" ([`src/server.ts:230`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L230), [`src/server.ts:1990`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1990)). concepts/state |
| Untrusted text treated as data, high or low (F22) | **no.** Only audit, review and gate questions carry injection framing; the other tools' questions carry none ([`src/server.ts:1451`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1451), [`src/server.ts:211`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L211)). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No non-English test or translation step appears in the tests or docs (`test/mock.test.mjs`). docs.typesafe.ai/models.md |

<details>
<summary><b>What passes (11) and doesn't apply (5)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. One property per question: a claim relation, an injection yes/no, one rubric, one failure mode per record ([`src/server.ts:211`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L211), [`src/server.ts:1390`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1390)) |
| Right primitive (F2) | yes. Noul for yes/no, Choice for named options, Score with three situation-worded levels for rubrics ([`src/server.ts:1457`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1457)) |
| Structured state (F3) | yes. Objects with named fields and ids; questions point at paths such as records[i] and files[i] ([`src/server.ts:1373`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1373)) |
| Batching (F4) | yes. All questions for a call go in one request; classify and rerank send one question per item ([`src/server.ts:659`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L659), [`src/server.ts:939`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L939)) |
| Thresholds in code (F5) | yes. Cutoffs are named parameters or constants, not question wording ([`src/lib.ts:290`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L290), [`src/server.ts:190`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L190)) |
| No invented values (F6) | yes. Code computes margin, composite and regex matches; Jev only picks or scores ([`src/lib.ts:345`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L345), [`src/server.ts:1175`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1175)) |
| Options cover every case, no overlap (F8) | yes. Fixed relations are exclusive; callers supply class and candidate sets, and the docs say to make them exclusive ([`src/lib.ts:64`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L64), [`README.md:343`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L343)) |
| An "other" option where needed (F9) | yes. decide has ask_user, investigate and none; extract has none_of_them; find pairs an exists Noul; classify leaves it to callers ([`src/lib.ts:153`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L153), [`src/server.ts:1173`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1173)) |
| Evidence recorded evenly (F10) | yes. State holds claims, evidence, diffs and tests as supplied; no conclusions are written into fields ([`src/server.ts:229`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L229)) |
| Confidence drives action, low (F11) | yes. Confidence and margin gate auto versus review in every tool that returns an action ([`src/lib.ts:71`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L71), [`src/lib.ts:137`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L137), [`src/lib.ts:404`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L404)) |
| Choice order handled, low (F13) | n.a.. Every decision is low and returned to the caller ([`src/server.ts:858`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L858)) |
| Sample size adequate (F15) | n.a.. No accuracy or calibration results are claimed; the README says to tune thresholds on your own data ([`README.md:731`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L731)) |
| Independent labels (F16) | n.a.. No accuracy results are claimed ([`README.md:731`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L731)) |
| Held-out result (F17) | n.a.. No accuracy results are claimed ([`README.md:731`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L731)) |
| Fair baseline (F18) | n.a.. No accuracy results are claimed ([`README.md:731`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L731)) |
| Typed answers read directly (F19) | yes. Code reads typed choice, probabilities, noul and score fields and validates them before acting ([`src/server.ts:1580`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1580), [`src/server.ts:1618`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1618)) |

</details>

## Scores

- Execution 3 of 3: questions are atomic, typed, fielded, batched and gated, and every F8-F11 applies and holds, with F1-F6, F8-F11 and F19 all yes.
- Fit 3 of 3: each decision uses the fitting primitive, confidence and margin gate every returned action, and each call is one request, from F2, F4 and F11.
- Coverage 3 of 3: all twelve promised tools exist and run as described, with limits and failure branches documented, from F0 and the tool list at [`README.md:12`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L12).
- Evidence 1 of 3: only speed and cost are stated, with usage captures but no latency measurement or accuracy run, from F7; F15-F18 are n.a. because no accuracy is claimed.

## Why this verdict

3, use with a fix. F21 fails at any stakes: the state carries a builder-written `purpose` directive in verify, audit, review and gate ([`src/server.ts:230`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L230), [`src/server.ts:1374`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1374), [`src/server.ts:1990`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1990)), and nothing sends it to 2 because F1 and F6 hold and Execution is 3. It is not a 4 because of that one capping failure. F20, F22, F14, F12 and F23 do not move the verdict at low stakes, since every tool returns a label to an agent rather than acting ([`README.md:252`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L252)). Evidence is 1 because only speed and cost are stated, with no measurement shown.

## Fixes (from reading the code; not tested against it)

1. Move the directives out of the state (F21): drop or replace the `purpose` sentences with a caller-supplied content field, and keep the judgment in the questions. https://docs.typesafe.ai/concepts/state.md
2. Measure the tools (F7, closes_loop none): label a sample of claims, injected pages and classes, report precision and recall at the 0.8 and 0.75 defaults and the real latency, then calibrate. https://docs.typesafe.ai/cookbooks/classification_using_confidence.md (confirmed only with data)
3. Pass caller text as fields (F20): point questions at `claims[i].text`, `query` and `propositions[i]` as jev_classify does. https://docs.typesafe.ai/primitives/advanced.md
4. Frame and test untrusted text in every tool (F22): add the existing injection sentence to verify, find, rerank, noul, compare, extract, classify and decide. https://docs.typesafe.ai/cookbooks/classifying_rag_passages.md
5. Guard size in tokens (F14): bound the gate and classify state under 64k tokens, and state plus the longest question under 32k. https://docs.typesafe.ai/models.md
6. Pin a versioned model where thresholds are tuned (F12), and add one non-English test (F23). https://docs.typesafe.ai/models.md and https://docs.typesafe.ai/concepts/state.md

<details>
<summary><b>Files read (24)</b></summary>

- .github/workflows/ci.yml -- read
- CHANGELOG.md -- read
- CONTRIBUTING.md -- read
- README.md -- read
- SECURITY.md -- read
- examples/exa-classify.md -- read
- examples/exa-classify.mjs -- read
- package.json -- read
- skills/jev/SKILL.md -- read
- skills/jev/reference/tools.md -- read
- src/http.ts -- read
- src/index.ts -- read
- src/lib.ts -- read
- src/provider.ts -- read
- src/server.ts -- read
- test/e2e.test.mjs -- read
- test/exa-example.test.mjs -- read
- test/fixtures/typesafe-abort-child.mjs -- read
- test/http.test.mjs -- read
- test/mock.test.mjs -- read
- test/provider.test.mjs -- read
- test/server.test.mjs -- read
- test/typesafe-abort-regression.test.mjs -- read
- test/unit.test.mjs -- read

</details>
