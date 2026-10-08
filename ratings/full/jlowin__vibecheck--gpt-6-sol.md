[← Summary](../jlowin__vibecheck--gpt-6-sol.md)

# vibecheck: full rating

**Verdict 2, Rework it** · library · rated 2026-10-06 at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

vibecheck is a Python library that sends caller questions and data to Jev as typed Noul, Choice and Score requests. It makes async and sync calls, batching, schema assessment and probability-aware checks accessible through a small API. Broad example wording, bare numeric Score levels, forced Choices and unverified performance claims limit the guidance users can copy.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Default backend sends typed questions and state through the TypeSafe SDK's System One method ([`src/vibecheck/backends.py:106`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L106)). |
| Atomic questions (F1) | **no.** The lead example asks whether unspecified “vibes” are good, with no standard ([`README.md:16`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L16)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Right primitive (F2) | **no.** Bare numbered satisfaction levels reach Score without described situations ([`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180)). https://docs.typesafe.ai/primitives/score |
| Measured in the workflow (F7) | **no.** The README’s 100-question token and answer claim has no task evaluation in retained files ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Options cover every case, no overlap (F8) | **no.** Basic ticket routing omits non-team messages, and returns and billing can overlap ([`examples/classify/basic.py:27`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/basic.py#L27)). https://docs.typesafe.ai/primitives/advanced |
| An other option where needed (F9) | **no.** The README’s first team classifier forces unrelated tickets into three teams ([`README.md:115`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L115)). https://docs.typesafe.ai/primitives/advanced |
| Confidence drives action, low (F11) | **no.** A callable handler can be selected and invoked from top Choice without a confidence gate ([`README.md:234`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L234)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Size limits respected (F14) | **no.** Caller data and arbitrary batch questions reach the backend without a token guard ([`src/vibecheck/_batch.py:243`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_batch.py#L243)). https://docs.typesafe.ai/models |
| Sample size adequate (F15) | **no.** “Same answers” for 100 questions lacks a sample of documents or repeated runs ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Held-out result (F17) | **no.** The performance claim has no separate held-out run reported ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Untrusted text treated as data, low (F22) | **no.** Customer text reaches state without source marking or an injection test ([`README.md:73`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L73)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** The library accepts arbitrary text, while examples and tests cover English only ([`README.md:268`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L268)). https://docs.typesafe.ai/concepts/state |

<details>
<summary><b>What passes (8) and doesn't apply (4)</b></summary>

| Fact | Finding |
|---|---|
| Structured state (F3) | yes. One text stays text; structured data keeps named fields ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)). |
| Batching (F4) | yes. Batch combines independent questions over shared state in one request ([`src/vibecheck/_batch.py:226`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_batch.py#L226)). |
| Thresholds in code (F5) | yes. The library sets and validates numeric cutoffs in code ([`src/vibecheck/_plans.py:153`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L153)). |
| No invented values (F6) | yes. Numeric results derive from supplied levels and probabilities; arithmetic is in code ([`src/vibecheck/_plans.py:234`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L234)). |
| Evidence recorded evenly (F10) | n.a.. The library accepts a single caller object and assembles no competing evidence ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)). |
| Pinned model version (F12) | n.a.. No threshold is reported as tuned against task data ([`README.md:508`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L508)). |
| Choice order handled, low (F13) | n.a.. The low-stakes Choice rule is always n.a. ([`src/vibecheck/_plans.py:172`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L172)). |
| Independent labels (F16) | n.a.. The token and answer-equivalence claim does not use ground-truth labels ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). |
| Fair baseline (F18) | yes. The batching comparison uses the same questions sent separately as its baseline ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). |
| Typed answers read directly (F19) | yes. The backend maps Noul, Choice and Score response probabilities into typed answers ([`src/vibecheck/backends.py:140`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L140)). |
| Data as fields, not templates, low (F20) | yes. Caller data is sent as state, apart from question instructions ([`src/vibecheck/_run.py:81`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L81)). |
| No instructions in the state (F21) | yes. The library places question instructions in typed questions and data in state ([`src/vibecheck/backends.py:124`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L124)). |

</details>

## Scores

- Execution 1 of 3: two shipped question patterns miss atomicity or described Score levels, despite sound batching and typed answers (F1, F2, F4, F19).
- Fit 1 of 3: broad wording, bare numeric Score levels and ungated top Choice choices are multiple mismatches (F1, F2, F11).
- Coverage 3 of 3: the package implements its advertised decision verbs, bulk helpers, batches and schema assessment (F3, F4, F5, F19).
- Evidence 0 of 3: the README gives a quantified comparison without a reproducible measurement or held-out result (F7, F15, F17).

## Why this verdict

Execution is 1 because the shipped examples include both an unspecified broad question and an undescribed Score scale; the verdict rule sends Execution 1 to 2. The backend integration and batching work, but they cannot lift that cap. The README's numeric performance claim lacks a reproducible evaluation, so it does not support a higher evidence rating.

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
