[← Summary](../RileyCarney__JevTools.md)

# JevTools: full rating

**Verdict 3, Use with a fix** · demo · rated 2026-10-01 at [`7f6907b`](https://github.com/RileyCarney/JevTools/tree/7f6907b461) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

JevTools sends review and topic text to hosted Jev through OpenRouter or the TypeSafe API, with six and four typed questions per request, and shows the answers plus a rule-based suggested action in a CLI and a local dashboard. It decomposes questions well, keeps policy in code and gates on Choice confidence, though a mock mode replaces Jev for offline runs. Nothing acts on the suggestions, no thresholds or results were checked on data, and the README latency figures disagree with each other and with the code.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Posts state and typed questions to OpenRouter's decisions endpoint or api.typesafe.ai and reads the answers ([`jev_demo.py:657`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L657)) |
| Measured in the workflow (F7) | **no.** Only a latency figure is claimed, 300 ms here and 287 elsewhere, with no recorded runs ([`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/README.md#L17)). Parallel questions cookbook |
| Options cover every case, no overlap (F8) | **no.** Topic options overlap: medicine sits in science and health, environmental policy in environment and politics ([`jev_demo.py:1136-1140`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1136-L1140)). Primitives advanced page |
| Size limits respected (F14) | **no.** Custom text has no token guard; the only cap is 1 MB, far above 64k tokens ([`server.py:37`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/server.py#L37)). Models page |
| Sample size adequate (F15) | **no.** The latency claim names no run count, and sources disagree on its value ([`tests/test_jev_demo.py:247`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/tests/test_jev_demo.py#L247)). Launch post and evals page |
| Untrusted text treated as data (F22) | **no.** Review text goes in unmarked with no injection test; SECURITY.md only claims resistance ([`SECURITY.md:113`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/SECURITY.md#L113)). Jev 1.13 model-jaggedness page |
| Non-English handled (F23) | **no.** Reviews and topics are English only, with no test or translation ([`jev_demo.py:1022`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1022)). State concepts page |

<details>
<summary><b>What passes (11) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each question judges one property with written criteria; "detailed and actionable" feedback is the loosest ([`jev_demo.py:933-985`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L933-L985)) |
| Right primitive (F2) | yes. Scores carry level text, Nouls cover yes/no checks, and tone and topic are Choices ([`jev_demo.py:933-1175`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L933-L1175)) |
| Structured state (F3) | yes. Review state is `{review, product}` and questions point at those fields; a topic is one string field ([`jev_demo.py:926-929`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L926-L929)) |
| Batching (F4) | yes. All six review questions, or four topic questions, go in one request per item ([`jev_demo.py:657`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L657)) |
| Thresholds in code (F5) | yes. Cut-offs sit in code beside the Jev call, not in question text, but as inline literals, not named constants ([`jev_demo.py:1023-1031`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1023-L1031)) |
| No invented values (F6) | yes. Code computes the composite and normalizes Scores; Jev only judges ([`jev_demo.py:1014-1020`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1014-L1020)) |
| An "other" option where needed (F9) | yes. Tone and topic Choices each carry an "other" option worded unlike the state ([`jev_demo.py:984`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L984), [`jev_demo.py:1143`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1143)) |
| Evidence recorded evenly (F10) | n.a.. A single review or paragraph is judged, with no per-answer evidence list ([`jev_demo.py:926`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L926)) |
| Confidence drives action, low (F11) | yes. Tone or topic Choice confidence below 0.5 turns the suggested label into a human-review flag ([`jev_demo.py:1023`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1023), [`jev_demo.py:1198`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1198)) |
| Pinned model version (F12) | n.a.. No threshold was tuned on data; the default alias is `~typesafe/jev-latest` ([`jev_demo.py:72`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L72)) |
| Choice order handled, low (F13) | n.a.. Always n.a. for this fact |
| Independent labels (F16) | n.a.. Only a latency claim is made, and it needs no labels ([`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/README.md#L17)) |
| Held-out result (F17) | n.a.. No threshold or wording was tuned against a reported number ([`jev_demo.py:1023`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1023)) |
| Fair baseline (F18) | n.a.. No comparison with an LLM or rules baseline is claimed ([`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/README.md#L17)) |
| Typed answers read directly (F19) | yes. Code reads the noul, score, choice, probabilities and confidence fields ([`jev_demo.py:252-300`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L252-L300)) |
| Data as fields, not templates (F20) | yes. Question text is static and refers to backticked `review`, `product` and `paragraph`; values stay in the state ([`jev_demo.py:933-1175`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L933-L1175)) |
| No instructions in the state (F21) | yes. State holds the review and product name, or the paragraph, only ([`jev_demo.py:926-929`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L926-L929)) |

</details>

## Scores

- Execution 2 of 3: the questions are atomic, typed, fielded, batched and kept free of invented values, but one Choice has overlapping options (F1-F6 yes, F8 no).
- Fit 3 of 3: every decision uses the fitting primitive, the two Choice-based flags are gated on confidence, and each item goes in one request (F2, F4, F11 yes).
- Coverage 3 of 3: the toolkit, two demos, custom playground, history store and knowledge vault the README lists are all present and wired together.
- Evidence 1 of 3: only a latency figure is claimed, with no run count, and the code, docs and tests give 300 and 287 ms (F7 no, F15 no).

## Why this verdict

It is a 3 because F8 fails: the topic Choice lets medicine fall under science or health and environmental policy under environment or politics, and any F8 failure caps the verdict at 3. Nothing sends it to 2, since Execution is 2, F1 and F6 hold, and every decision only shows a suggested label. It is not a 4 because of that capping failure, and Evidence is 1 because the only claim is a latency figure that the README, docs, code and tests state differently. The all-low stakes and the "Fit 3" rest on its suggestions being shown rather than acted on; routing it to a real queue would need confidence gates on the Noul decisions too. F5 is borderline: the cut-offs are inline literals in one policy block, not named constants.

## Fixes (from reading the code; not tested against it)

1. Make the topic options exclusive and exhaustive, or switch to independent Nouls where topics can co-occur, and confirm the change with data (F8; [`primitives`](https://docs.typesafe.ai/primitives) Choice page).
2. Add an evaluation: label a sample of reviews and paragraphs, report precision and recall at the chosen thresholds, and replace the 300 and 287 ms figures with recorded runs that state how many (F7, F15; [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence), TypeSafe's workflow evals).
3. After evaluating, calibrate the thresholds or revise the questions for the misses, then re-measure (closes_loop none; [`confidence`](https://docs.typesafe.ai/confidence), [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery)).
4. Flag steering text in reviews, add an injection-check Noul and test adversarial inputs before the suggestions drive any queue (F22; [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)).
5. Filter or split long custom inputs to stay under 32k tokens (F14; [`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13)), and test or translate non-English text (F23; [`concepts/state`](https://docs.typesafe.ai/concepts/state)).

<details>
<summary><b>Files read (39)</b></summary>

- LICENSE -- read
- README.md -- read
- SECURITY.md -- read
- SECURITY_REMEDIATION_PLAN.md -- read
- database.py -- read
- jev_demo.py -- read
- jev_demo_README.md -- read
- pyproject.toml -- read
- server.py -- read
- skills/JEV.MD -- read
- skills/JEV_SKILL.MD -- read
- tests/test_database.py -- read
- tests/test_jev_demo.py -- read
- tests/test_server.py -- read
- vault/F01-archive/Choice.md -- read
- vault/F01-archive/Composing Answers in Code.md -- read
- vault/F01-archive/Confidence.md -- read
- vault/F01-archive/Cookbooks Index.md -- read
- vault/F01-archive/HTTP API.md -- read
- vault/F01-archive/How to Build with Jev.md -- read
- vault/F01-archive/JavaScript SDK.md -- read
- vault/F01-archive/Jev MOC.md -- read
- vault/F01-archive/Noul.md -- read
- vault/F01-archive/Pattern - Composite Scoring.md -- read
- vault/F01-archive/Pattern - Confidence-Gated Routing.md -- read
- vault/F01-archive/Pattern - Intent Routing.md -- read
- vault/F01-archive/Pattern - Speculative Fan-Out.md -- read
- vault/F01-archive/Primitives Overview.md -- read
- vault/F01-archive/Python SDK.md -- read
- vault/F01-archive/Question Design Rules.md -- read
- vault/F01-archive/Score.md -- read
- vault/F01-archive/State.md -- read
- vault/F01-archive/System One.md -- read
- vault/F01-archive/Use-Case Map.md -- read
- vault/Jev Core.md -- read
- vault/Jev Design.md -- read
- vault/Jev MOC.md -- read
- vault/Jev Patterns.md -- read
- vault/Jev SDK & API.md -- read

</details>
