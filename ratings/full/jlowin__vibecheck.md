[← Summary](../jlowin__vibecheck.md)

# vibecheck: full rating

**Verdict 3, Use with a fix** · library · rated 2026-10-06 at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · read: full · rubric 2026-09-29.2 · claude-sonnet-5-5, medium effort

## Summary

vibecheck is a Python library that turns check, classify, label, score and assess calls into typed Noul, Choice and Score requests to Jev and returns plain Python values. It does well on batching, structured state, probability thresholds with an unsure band, and reading typed answers directly. Bare numeric Score levels, an unmeasured batching claim, no state size guard and a spliced example question hold it back.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** TypeSafeBackend sends questions through the TypeSafe SDK's `system_one`, sync and async ([`src/vibecheck/backends.py:106`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L106), [`src/vibecheck/backends.py:118`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L118)) |
| Right primitive (F2) | **no.** check is Noul, classify Choice, score Score, but bare `range(1, 6)` levels go as "1".."5" ([`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`src/vibecheck/_plans.py:364`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L364)). primitives/score |
| Measured in the workflow (F7) | **no.** One unlinked batching figure, no accuracy numbers, and tests use FakeBackend only ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). how-to-build-with-system-one |
| Size limits respected (F14) | **no.** Option and level counts are checked, but state size is not; a whole database row reaches Jev uncut ([`src/vibecheck/_plans.py:329`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L329)). models |
| Sample size adequate (F15) | **no.** The batching claim names one 5,000-token document and 100 questions, with no runs or files to check ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). how-to-build-with-system-one |
| Data as fields, not templates (F20) | **no.** `classify(f"What is {thing} most commonly known as?")` splices code values into question text ([`examples/classify/no_data.py:26`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/no_data.py#L26)). primitives/advanced |
| Untrusted text treated as data (F22) | **no.** Customer tickets and reviews go in the state unflagged, and no test tries steering ([`README.md:71`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L71), [`tests/test_api.py:86`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/tests/test_api.py#L86)). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No mention or test of other languages anywhere in the docs or tests ([`README.md:268`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L268)). models |

<details>
<summary><b>What passes (10) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each verb asks one property; label splits into one Noul per option; assess one question per field ([`src/vibecheck/_plans.py:208`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L208)) |
| Structured state (F3) | yes. Dicts, lists, dataclasses and Pydantic models go as JSON fields; strings pass as text ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)) |
| Batching (F4) | yes. `batch` and `assess` send many questions in one request; separate calls over one ticket are not merged ([`src/vibecheck/_batch.py:243`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_batch.py#L243)) |
| Thresholds in code (F5) | yes. Cut-offs are `threshold` arguments, default 0.5 or a (low, high) band, never in question text ([`src/vibecheck/_plans.py:153`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L153)) |
| No invented values (F6) | yes. Code computes the weighted score position; docs send arithmetic and counting to code ([`src/vibecheck/_plans.py:242`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L242), [`README.md:305`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L305)) |
| Options cover every case, no overlap (F8) | yes. Library fixes no options; examples use distinct ones with descriptions for overlaps, callers' lists don't count ([`examples/classify/descriptions.py:21`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/descriptions.py#L21)) |
| An "other" option where needed (F9) | yes. Docs warn and show the fix; README's first classify and assess Triage omit it ([`README.md:118`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L118), [`README.md:450`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L450)) |
| Evidence recorded evenly (F10) | n.a.. The library adds no evidence of its own; the caller's data is the state ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)) |
| Confidence drives action, low (F11) | yes. check and label gate on probability, band returns None for review; classify, score and group have no gate ([`src/vibecheck/_plans.py:161`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L161)) |
| Pinned model version (F12) | n.a.. No threshold was tuned in the repo; README advises pinning `jev-1.13.0` once tuned ([`README.md:508`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L508)) |
| Choice order handled, low (F13) | n.a.. Always n.a. |
| Independent labels (F16) | n.a.. No labels: the one claim compares batched with separate Jev answers ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)) |
| Held-out result (F17) | n.a.. Nothing was tuned on the reported figure ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)) |
| Fair baseline (F18) | n.a.. The one claim compares Jev with itself, not an LLM or rules alternative ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)) |
| Typed answers read directly (F19) | yes. Code decodes Noul probability, Choice probabilities and Score probabilities by type ([`src/vibecheck/backends.py:140`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L140)) |
| No instructions in the state (F21) | yes. Task and question text go in instructions; state is only the caller's data ([`src/vibecheck/_plans.py:263`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L263)) |

</details>

## Scores

- Execution 2 of 3: the questions are atomic, fielded, batched and gated, but one primitive choice is off, bare 1-to-5 Score levels (F2 no; F1, F3-F6, F8-F11 and F19 yes).
- Fit 2 of 3: each verb maps to the fitting primitive and probabilities gate check and label, with one mismatch, bare numeric Score levels sent without situations (F2, F11).
- Coverage 3 of 3: all four verbs plus filter, group, batch, assess, sync and async are built and tested against what the README promises (F0, F4, F19).
- Evidence 0 of 3: the README states a batching result, 100 questions matching 100 requests at about 1% of the tokens, with no measurement in the repo (F7, F15).

## Why this verdict

Verdict 3, Use with a fix. F2 is no because the README and an example send bare 1-to-5 Score levels, a failure that caps the verdict at 3, and Evidence is 0 while the README states a batching result. Execution is 2, so it is not sent to 2, and Fit is 2 and Execution 2 keep it below 4. Borderline calls: F11 is yes because check and label gate on probability while classify and score return the top result and expose probabilities on request, and F9 is yes because the docs name the gap and ship the fix.

## Fixes (from reading the code; not tested against it)

1. F2: describe Score levels as situations instead of bare numbers in [`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`README.md:430`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L430) and [`examples/score/numeric_levels.py:26`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/score/numeric_levels.py#L26), using the dict form. Source: [`primitives/score`](https://docs.typesafe.ai/primitives/score).
2. F7, F15: measure the batching claim at [`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414) on a stated sample and report the numbers, or drop the figure. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence).
3. F14: guard or report state size so a whole database row stays under 32k tokens per request. Source: [`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
4. Loop not closed: after measuring, tune the 0.5 default and the example cut-offs on labels, then re-measure. Source: [`confidence`](https://docs.typesafe.ai/confidence), [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).
5. F20, F22, F23 (listed fixes, no verdict effect): put values in fields instead of the f-string in [`examples/classify/no_data.py:26`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/no_data.py#L26), flag customer text in examples, and test non-English input. Source: [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`concepts/state`](https://docs.typesafe.ai/concepts/state).

<details>
<summary><b>Files read (34)</b></summary>

- .agents/skills/vibecheck/SKILL.md -- read
- AGENTS.md -- read
- README.md -- read
- examples/check/basic.py -- read
- examples/check/no_data.py -- read
- examples/check/probabilities.py -- read
- examples/check/three_way.py -- read
- examples/check/threshold.py -- read
- examples/classify/basic.py -- read
- examples/classify/descriptions.py -- read
- examples/classify/enums.py -- read
- examples/classify/functions.py -- read
- examples/classify/no_data.py -- read
- examples/classify/other.py -- read
- examples/classify/probabilities.py -- read
- examples/label/basic.py -- read
- examples/label/probabilities.py -- read
- examples/label/top_n.py -- read
- examples/score/basic.py -- read
- examples/score/described_levels.py -- read
- examples/score/numeric_levels.py -- read
- examples/score/probabilities.py -- read
- pyproject.toml -- read
- src/vibecheck/__init__.py -- read
- src/vibecheck/_async.py -- read
- src/vibecheck/_batch.py -- read
- src/vibecheck/_plans.py -- read
- src/vibecheck/_questions.py -- read
- src/vibecheck/_run.py -- read
- src/vibecheck/backends.py -- read
- src/vibecheck/sync.py -- read
- src/vibecheck/testing.py -- read
- tests/test_api.py -- read
- tests/test_typesafe_backend.py -- read

</details>
