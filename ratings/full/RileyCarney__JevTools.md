[← Summary](../RileyCarney__JevTools.md)

# JevTools: full rating

**Verdict 3, Use with a fix** · demo · rated 2026-09-28 at [`7f6907b`](https://github.com/RileyCarney/JevTools/tree/7f6907b4614914cb47c8b089252832f1f2da485f) · read: full · rubric 2026-09-28b (earlier) · claude-sonnet-5-5, medium effort

*Rated under an earlier rubric (2026-09-28b). A re-rating is queued.*

## Summary

JevTools is a localhost dashboard and CLI (`server.py`, `jev_demo.py`) that sends two fixed question sets to hosted Jev, one for customer reviews and one for topic classification, plus a pass-through playground for user-written questions. It does call Jev: one `requests.post` in `call_jev` ([`jev_demo.py:657`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L657)) to the OpenRouter Alpha Decisions endpoint or the TypeSafe direct API. Each fixed set goes out as one batched request, the questions use the right primitives over JSON state, and the thresholds and weights sit in code. The results only drive display labels such as `[ESCALATE]` and `[FLAG]`, so it is a demo with low stakes throughout. Two design facts fail: one review question joins two judgments (`quality_of_feedback`, [`jev_demo.py:946`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L946)), and the nine topic options overlap (science versus health, politics versus environment, education versus science). The README, the tests and the dashboard also quote a "tested" latency (300 ms in [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82) and [`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L17), 287 ms in the tests, the dashboard and [`jev_demo_README.md:11`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo_README.md#L11)) with no measurement behind it, and no accuracy is measured anywhere. Verdict 3, use with a fix.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** [`jev_demo.py:657`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L657): `requests.post(url=url, headers=..., json=payload, timeout=60, ...)` in `call_jev`, with `url` from `get_provider_config` (`OPENROUTER_API_URL = "https://openrouter.ai/api/alpha/decisions"` or `TYPESAFE_API_URL = "https://api.typesafe.ai/v1/systemone"`, model `~typesafe/jev-latest` or `jev-latest`, [`jev_demo.py:72-75`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L72-L75)). |
| Atomic questions (F1) | **no.** `quality_of_feedback` asks "How detailed and actionable is the feedback in `review`?" ([`jev_demo.py:946`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L946)), two judgments in one Score (detail and actionability), and it carries 20% of the composite ([`jev_demo.py:1017`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1017)). The other five review questions and the four topic questions each ask one property. This is one compound question among several good ones, not the main decision. Fix: F1 ([`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)). |
| Measured in the workflow (F7) | **no.** The only measurement is `measure_openrouter_latency` ([`jev_demo.py:768`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L768)), which times a fixed ping question (`state={"ping": "benchmark"}`, `Is this a test?`), not the review or topic workflow. When that request fails it times a GET to `https://openrouter.ai/api/v1/models` ([`jev_demo.py:805`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L805)), and when that fails it records `OPENROUTER_TESTED_LATENCY_MS` (300.0, [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)) as the result and logs it as `status="success"` ([`jev_demo.py:814`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L814), [`jev_demo.py:825-836`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L825-L836)). No accuracy, cost or output figure appears in the repo. Fix: F7 ([`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)). |
| Options cover every case without overlapping (F8) | **no.** `primary_topic` options overlap: `science` includes "medicine" ([`jev_demo.py:1136`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1136)) while `health` covers "personal health, fitness, nutrition, mental health" ([`jev_demo.py:1139`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1139)); `politics` includes "policy" ([`jev_demo.py:1138`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1138)) and `environment` includes "environmental policy" ([`jev_demo.py:1140`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1140)); `education` includes "academic research" ([`jev_demo.py:1142`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1142)) and `science` includes "research findings" ([`jev_demo.py:1136`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1136)). The mock's own probabilities show the pairs competing (`health` 0.82 with `politics` 0.12, [`jev_demo.py:466`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L466)). `emotion_tone` options (calm, frustrated, delighted, other) are exclusive. Fix: F8 ([`primitives`](https://docs.typesafe.ai/primitives); confirm with data). |
| Model pinned (fix-only) (F12) | **no.** Defaults are the aliases `~typesafe/jev-latest` and `jev-latest` ([`jev_demo.py:72-75`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L72-L75)), and `sanitize_model_for_provider` maps unknown IDs back to them ([`jev_demo.py:164-200`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L164-L200)). `jev-1.13.0` is only a dropdown option. Fix: F12 ([`models`](https://docs.typesafe.ai/models)). |
| Untrusted text is treated as data (fix-only) (F22) | **no.** Review, paragraph and playground text reach the state and questions with no steering flag and no injection test. [`SECURITY.md:110-113`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/SECURITY.md#L110-L113) (Pillar 3, "Control Inversion & Prompt Injection Resistance") is a claim; `tests/` contain no steering test, and the hardening tests cover the web layer (CORS, path blocking, body cap, host allowlist). Fix: F22 ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)). |
| Non-English content handled (fix-only) (F23) | **no.** Inputs are not declared English-only and nothing tests other languages. Fix: F23 ([`concepts/state`](https://docs.typesafe.ai/concepts/state)). |

<details>
<summary><b>What passes (9) and doesn't apply (8)</b></summary>

| Fact | Finding |
|---|---|
| The right primitive (F2) | yes. Nouls for yes/no (`mentions_defect`, `would_recommend`, `is_opinion`), Choices for named options (`emotion_tone`, `primary_topic`), Scores with described levels for graded properties (`overall_sentiment`, `technical_depth`, [`jev_demo.py:934-1000`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L934-L1000), [`jev_demo.py:1131-1170`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1131-L1170)). |
| Structured state (F3) | yes. State is `{"review": ..., "product": ...}` and `{"paragraph": ...}` and the questions point at backticked paths such as `` `review` `` and `` `product` `` ([`jev_demo.py:926-929`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L926-L929), [`jev_demo.py:946`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L946), [`jev_demo.py:1127`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1127)). |
| Batching (F4) | yes. All 6 review questions and all 4 topic questions go in one request ([`jev_demo.py:912`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L912), [`jev_demo.py:1125`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1125), docstring "sent in ONE request"; `call_jev_with_metrics` is called once per item). |
| Thresholds in code (F5) | yes. The gates and cut-offs are literals in code ([`jev_demo.py:1023-1034`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023-L1034), [`jev_demo.py:1198-1210`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1198-L1210)); no threshold sits in a question. They are literals in an if-chain, not named constants, and none was set from data. |
| No invented values (F6) | yes. Jev picks among Choice options or gives probabilities and scores; the composite ([`jev_demo.py:1014-1019`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1014-L1019)) and every comparison run in code. |
| An "unclear" or "other" option (F9) | yes. `emotion_tone` has `other` ("Mixed emotions, sarcasm, or tone that doesn't clearly fit the above", [`jev_demo.py:984`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L984)) and `primary_topic` has `other` ("does not clearly belong to any of the above", [`jev_demo.py:1143`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1143)); neither wording echoes state text. |
| Evidence recorded evenly (F10) | n.a.. The state is one review plus a product name, or one paragraph: no per-answer evidence. |
| Confidence drives action (F11) | n.a.. Every decision is `low` and only shown as a label, so the rubric marks F11 n.a. (the code does gate on confidence anyway: [`jev_demo.py:1023`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023), [`jev_demo.py:1198`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1198)). |
| Choice order handled (F13) | n.a.. Every Choice is `low`. |
| Size limits respected (fix-only) (F14) | n.a.. No token guard and no reported maximum size; the 1 MB body cap ([`server.py:37`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/server.py#L37)) is above the 64k-token limit, so it does not count. Unverified, which counts as n.a. |
| Typed answers read directly (F19) | yes. `extract_noul`, `extract_score` and `extract_choice` read the typed fields and probabilities ([`jev_demo.py:252-302`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L252-L302)). |
| Values from code are fields, not templates (F20) | yes. (fix-only anyway at `low`). The review, product and paragraph go in state fields; the question strings are fixed literals ([`jev_demo.py:926-1000`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L926-L1000), [`jev_demo.py:1127-1170`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1127-L1170)). The playground passes user questions straight through ([`jev_demo.py:1266`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1266)). |
| No instructions in the state (F21) | yes. The state holds the review text and product name only. |
| Sample size (F15) | n.a.. The project claims no accuracy result. |
| Independent labels (F16) | n.a.. No labeled data or accuracy claim. |
| Held-out set (F17) | n.a.. No labeled data or accuracy claim. |
| Fair baseline (F18) | n.a.. No labeled data or accuracy claim. |

</details>

## Scores

- Execution 2: anchor "Or exactly one of F1-F6 is no, and it affects only one of several similar questions, not the main decision". F1 fails on `quality_of_feedback` ([`jev_demo.py:946`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L946)) and F8 also fails on the topic Choice ([`jev_demo.py:1136-1142`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1136-L1142)); F2-F6 and F19 hold. Neither failure touches the main routing signal (the defect and emotion gates), so Execution stays at 2.
- Fit 3: anchor "Each decision uses the primitive that fits it; confidence is used wherever an action depends on it; parallel questions are used wherever questions share a state". The Choice confidences gate the human-review route ([`jev_demo.py:1023`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023), [`jev_demo.py:1198`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1198)), the Nouls carry the thresholds, and all questions over one state go together. `mentions_shipping` is asked and never used in a decision ([`jev_demo.py:1009`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1009), [`jev_demo.py:1046`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1046)), a wasted question rather than a mismatch.
- Coverage 2: anchor "50 to 79% covered" (6 of 10 steps, below).
- Evidence 0: anchor "Claims results with no measurement shown". The README claims "300 ms actual tested inference latency" ([`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L17)), [`jev_demo_README.md:11`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo_README.md#L11) claims "287 ms tested inference latency", the dashboard shows "287 ms" (`index.html`, outside the manifest), and the repo's own tests assert `OPENROUTER_TESTED_LATENCY_MS == 287.0` (`tests/test_jev_demo.py`, `test_tested_constants`) while the code sets 300.0 ([`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). No run output, log or benchmark result backs either number, the benchmark times a ping question, and its last fallback returns the constant itself. The benchmark code can return the claimed number without measuring anything, so this is 0 rather than 1 (latency measured, no accuracy).

Lineage (remix of three TypeSafe patterns, [`patterns/fan-out`](https://docs.typesafe.ai/patterns/fan-out), [`patterns/composite-scoring`](https://docs.typesafe.ai/patterns/composite-scoring), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)). Original steps and what the project does with them:
- fan-out: keep "put all questions, speculative ones included, in one request" ([`jev_demo.py:912`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L912), [`jev_demo.py:1114`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1114)); keep "code decides what is relevant after the fact" ([`jev_demo.py:1023-1034`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023-L1034)).
- composite-scoring: keep "score each dimension independently"; keep "normalize to 0-1 and weight in code" ([`jev_demo.py:1014-1019`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1014-L1019)); drop "several weight profiles over the same scores" (one profile); drop "rank candidates by the composite" (no ranking).
- confidence-routing: keep "ask a Choice for the intent" (`emotion_tone`, `primary_topic`) and "route below a confidence floor to a human" ([`jev_demo.py:1023`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023), [`jev_demo.py:1198`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1198)); change "per-action thresholds set by consequence" (thresholds differ by branch but are not tied to consequences and were not tuned); drop "ask for confirmation before a risky action" (no risky action exists).
- Covered: 6 of 10 steps (60%), the omissions unexplained. The project's own stated goal (show Jev on reviews and topics) is fully addressed.

## Why this verdict

3, Use with a fix. It is a real integration (F0 yes) with sound core design: one batched request per item, typed answers read directly, thresholds in code. The cap comes from failed F1 (one compound question) and F8 (overlapping topic options). It is not a 2: Execution is 2, F1 fails on one of six questions and not on the main decision, F6 holds, and no high-stakes action ignores confidence (every decision is `low`). The Evidence 0 also caps the verdict at 3 ("misleading claims can't score above 3"). Its main weakness for a reader is that the headline latency figures have no data behind them and disagree with each other (300 versus 287), and the README says "License MIT" ([`README.md:132`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L132), and the skill files) while [`pyproject.toml:11`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/pyproject.toml#L11) and `LICENSE` are GPL-3.0. The `skills/`, `vault/` and `jev_demo_README.md` files restate TypeSafe's public guidance; they add no Jev design of their own.

## Fixes (from reading the code; not tested against it)

1. F1: split `quality_of_feedback` into two questions, one for how detailed the feedback is and one for whether it holds an actionable suggestion; combine in code ([`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one), "Decompose the questions").
2. F8: make the nine topic options exclusive (draw a line between medicine and health, and between policy under politics and under environment), or ask independent Nouls when topics can co-occur; confirm with data on real paragraphs ([`primitives`](https://docs.typesafe.ai/primitives)).
3. F7: measure on the project's own task. Label a sample of reviews and paragraphs, report accuracy at the 0.5 and 0.75 gates, replace the ping benchmark, and remove the hardcoded 300 ms and 287 ms figures until a run backs them ([`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)).
4. F12: pin `jev-1.13.0` as the default and log the `model` field each response returns ([`models`](https://docs.typesafe.ai/models)).
5. F22: add a steering check and one adversarial test on review and paragraph text before the demo is shown to others ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)).
6. F23: test a non-English review or add an English translation beside the original ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).

<details>
<summary><b>Files read (40)</b></summary>

- LICENSE — read
- README.md — read
- SECURITY.md — read
- SECURITY_REMEDIATION_PLAN.md — read
- database.py — read
- jev_demo.py — read
- jev_demo_README.md — read
- pyproject.toml — read
- server.py — read
- skills/JEV.MD — read
- skills/JEV_SKILL.MD — read
- tests/test_database.py — read
- tests/test_jev_demo.py — read
- tests/test_server.py — read
- vault/F01-archive/Choice.md — read
- vault/F01-archive/Composing Answers in Code.md — read
- vault/F01-archive/Confidence.md — read
- vault/F01-archive/Cookbooks Index.md — read
- vault/F01-archive/HTTP API.md — read
- vault/F01-archive/How to Build with Jev.md — read
- vault/F01-archive/JavaScript SDK.md — read
- vault/F01-archive/Jev MOC.md — read
- vault/F01-archive/Noul.md — read
- vault/F01-archive/Pattern - Composite Scoring.md — read
- vault/F01-archive/Pattern - Confidence-Gated Routing.md — read
- vault/F01-archive/Pattern - Intent Routing.md — read
- vault/F01-archive/Pattern - Speculative Fan-Out.md — read
- vault/F01-archive/Primitives Overview.md — read
- vault/F01-archive/Python SDK.md — read
- vault/F01-archive/Question Design Rules.md — read
- vault/F01-archive/Score.md — read
- vault/F01-archive/State.md — read
- vault/F01-archive/System One.md — read
- vault/F01-archive/Use-Case Map.md — read
- vault/Jev Core.md — read
- vault/Jev Design.md — read
- vault/Jev MOC.md — read
- vault/Jev Patterns.md — read
- vault/Jev SDK & API.md — read
- extra/index.html — read (markup and script, lines 2855-6386, in full; the CSS block at lines 23-2854 was not read and holds no requests or claims)

</details>
