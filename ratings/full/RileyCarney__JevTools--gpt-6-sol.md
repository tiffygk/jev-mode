[← Summary](../RileyCarney__JevTools--gpt-6-sol.md)

# JevTools: full rating

**Verdict 3, Use with a fix** · display · rated 2026-10-06 at [`7f6907b`](https://github.com/RileyCarney/JevTools/tree/7f6907b4614914cb47c8b089252832f1f2da485f) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

The CLI and local dashboard send typed Jev questions for customer-review analysis, topic classification, and arbitrary user questions, then show suggested actions. It batches independent questions, preserves answer probabilities, and computes review scores and routing labels in Python. The labels are suggestions rather than executed handoffs, and the repository shows no labeled live-outcome evaluation.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Python posts model, state and typed questions to OpenRouter or TypeSafe decisions endpoint ([`jev_demo.py:657`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L657)). |
| Thresholds in code (F5) | **no.** Review and topic cutoffs are inline literals rather than named constants or config ([`jev_demo.py:1014-1036`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1014-L1036), [`jev_demo.py:1200-1209`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1200-L1209)). https://docs.typesafe.ai/confidence.md |
| Measured in the workflow (F7) | **no.** A 300 ms latency constant and mock tests do not show measured live task outcomes ([`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82), [`jev_demo.py:790-819`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L790-L819); [`tests/test_jev_demo.py:163-230`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/tests/test_jev_demo.py#L163-L230)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Options cover every case, no overlap (F8) | **no.** A medical research paragraph fits science and health; that can change expert versus standard labels ([`jev_demo.py:1135-1144`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1135-L1144), [`jev_demo.py:1205-1209`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1205-L1209)). https://docs.typesafe.ai/primitives/advanced.md |
| Pinned model version (F12) | **no.** Numeric routing cutoffs use `jev-latest` aliases by default ([`jev_demo.py:72`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L72), [`jev_demo.py:75`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L75), [`jev_demo.py:1023-1036`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023-L1036), [`jev_demo.py:1200-1209`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1200-L1209)). https://docs.typesafe.ai/models.md |
| Size limits respected (F14) | **no.** Custom state and questions pass through without a token budget; a large state can fail live evaluation ([`server.py:807-833`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/server.py#L807-L833); [`jev_demo.py:645-662`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L645-L662)). https://docs.typesafe.ai/models.md |
| Sample size adequate (F15) | **no.** The claimed tested latency gives no live run count or captured timings ([`README.md:18`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L18); [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Data as fields, not templates (F20) | **no.** Custom playground forwards a user's questions as model instructions; a user-written judgment can change answers ([`server.py:807-833`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/server.py#L807-L833)). https://docs.typesafe.ai/primitives/advanced.md |
| Untrusted text treated as data (F22) | **no.** Custom reviews and paragraphs reach Jev without source flags or adversarial steering tests ([`jev_demo.py:922-925`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L922-L925), [`jev_demo.py:1126`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1126); [`tests/test_jev_demo.py:163-230`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/tests/test_jev_demo.py#L163-L230)). https://docs.typesafe.ai/model-jaggedness/jev-1.13.md |
| Non-English handled (F23) | **no.** CLI accepts arbitrary review and topic text, but tests cover English examples only ([`jev_demo.py:1344-1420`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1344-L1420); [`tests/test_jev_demo.py:163-230`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/tests/test_jev_demo.py#L163-L230)). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (8) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. The ten fixed questions each ask one review or paragraph property ([`jev_demo.py:933-984`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L933-L984), [`jev_demo.py:1131-1176`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1131-L1176)). |
| Right primitive (F2) | yes. Binary signals use Noul, categories Choice, and described degrees Score ([`jev_demo.py:933-984`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L933-L984), [`jev_demo.py:1131-1176`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1131-L1176)). |
| Structured state (F3) | yes. Review and product, or paragraph, travel as named JSON fields ([`jev_demo.py:922-925`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L922-L925), [`jev_demo.py:1126`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1126)). |
| Batching (F4) | yes. Each review sends six questions and each paragraph four in one request ([`jev_demo.py:992-1005`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L992-L1005), [`jev_demo.py:1178-1191`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1178-L1191)). |
| No invented values (F6) | yes. Jev judges supplied text; code normalizes scores and calculates the composite ([`jev_demo.py:1008-1020`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1008-L1020)). |
| An other option where needed (F9) | yes. Topic has other; tone has other for mixed or unclear emotion ([`jev_demo.py:981-983`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L981-L983), [`jev_demo.py:1143-1144`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1143-L1144)). |
| Evidence recorded evenly (F10) | n.a.. Each request judges one supplied review or paragraph without per-answer evidence lists ([`jev_demo.py:922-925`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L922-L925), [`jev_demo.py:1126`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1126)). |
| Confidence drives action (F11) | n.a.. Code produces labels for the asker and logs them for display; no operational handoff occurs ([`jev_demo.py:1023-1069`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1023-L1069), [`jev_demo.py:1200-1238`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1200-L1238)). |
| Choice order handled (F13) | n.a.. This fact is always n.a. for low-stakes Choices ([`jev_demo.py:977-984`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L977-L984), [`jev_demo.py:1131-1145`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1131-L1145)). |
| Independent labels (F16) | n.a.. The repository reports latency, not labeled accuracy against human outcomes ([`README.md:18`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L18); [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). |
| Held-out result (F17) | n.a.. No result requiring a held-out task set is reported ([`README.md:18`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L18); [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). |
| Fair baseline (F18) | n.a.. No project-task accuracy comparison against another method is reported ([`README.md:18`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L18); [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). |
| Typed answers read directly (F19) | yes. Helpers read `noul`, `score`, `choice`, probability and confidence fields ([`jev_demo.py:251-305`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L251-L305), [`jev_demo.py:1008-1011`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1008-L1011)). |
| No instructions in the state (F21) | yes. Fixed workflows send review/product or paragraph as state; judgment instructions stay in questions ([`jev_demo.py:922-984`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L922-L984), [`jev_demo.py:1126-1176`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1126-L1176)). |

</details>

## Scores

- Execution 2 of 3: one core design miss, inline thresholds, and an overlapping Choice taxonomy; F5 Thresholds in code and F8 Options cover every case.
- Fit 3 of 3: the fixed questions use matching primitives, shared-state batches, and confidence for ambiguity labels; F2 Right primitive, F4 Batching, F11 Confidence drives action.
- Coverage 1 of 3: it keeps the parallel-questions cookbook's single-call batching but omits its repeated single-call comparison and measured variance/cost/latency; F4 Batching and F7 Measured in the workflow.
- Evidence 0 of 3: tested-latency figures are asserted without captured live measurements; F7 Measured in the workflow and F15 Sample size adequate.

## Why this verdict

3, Use with a fix. The typed, batched calls and code-composed suggestions make this a working Jev display, but F5 and F8 cap it below 4, and the unsupported latency result makes Evidence 0. It is above 2 because Execution is 2, the primitive choices fit the decisions, and no high-stakes action ignores confidence. The boundary is that `[ESCALATE]` and editorial routing are strings shown or returned, not executed handoffs.

## Fixes (from reading the code; not tested against it)

1. F8: make topic options exclusive, or use independent Nouls when topics co-occur; confirm the resulting routing on real paragraphs. https://docs.typesafe.ai/primitives.md
2. F7 and F15: label review and topic examples, report sample size and precision/recall at the chosen cutoffs, and capture live task latency. https://docs.typesafe.ai/cookbooks/classification_using_confidence.md
3. F5: move inline cutoffs into named constants and set them from labeled examples. https://docs.typesafe.ai/confidence.md
4. F14: bound state and question tokens before the custom call; split long inputs to stay within model limits. https://docs.typesafe.ai/models.md
5. F12: pin a versioned model ID, record the returned model, and retune cutoffs when upgrading. https://docs.typesafe.ai/models.md
6. F20 and F22: put user-written questions in a marked state field and test steering inputs that reach the playground. https://docs.typesafe.ai/primitives/advanced.md https://docs.typesafe.ai/model-jaggedness/jev-1.13.md
7. F23: test reviews and paragraphs in supported non-English languages or add English translations. https://docs.typesafe.ai/concepts/state.md

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
