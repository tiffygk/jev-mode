[← Summary](../jlowin__vibecheck.md)

# vibecheck: full rating

**Verdict 3, Use with a fix** · library · rated 2026-09-30 at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

vibecheck is a Python package that turns one function call (`check`, `classify`, `label`, `score`, `assess`, `filter`, `group`) into typed Jev questions and returns a plain Python value. It writes the question wording itself, keeps every probability available, offers a three-way threshold band for unsure answers, and ships a fake backend for tests. It does not use the answer's own confidence field or pin a model by default, ships no calibration tooling, and its README claims accuracy results with no data behind them.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** TypeSafeBackend sends the caller's state and questions to the System One API through the SDK ([`src/vibecheck/backends.py:106`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L106)) |
| Right primitive (F2) | **no.** Verbs map to Noul, Choice and Score, but bare-number levels send "1".."5" as level text, also in README examples ([`src/vibecheck/_plans.py:364`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L364), [`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`README.md:430`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L430)). [`primitives/score`](https://docs.typesafe.ai/primitives/score) |
| Measured in the workflow (F7) | **no.** README claims 100 questions matched 100 requests at about 1% of tokens; no test or data is shipped ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) |
| Size limits respected (F14) | **no.** Option and level counts are checked; nothing guards state or question token size ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)). [`models`](https://docs.typesafe.ai/models) |
| Sample size adequate (F15) | **no.** The one results claim covers one 5,000-token document, with no counts or runs shown ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`models`](https://docs.typesafe.ai/models) |
| Fair baseline (F18) | **no.** The 100-separate-requests comparison is stated but nothing in the repo reproduces it ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) |
| Untrusted text treated as data (F22) | **no.** Customer tickets and reviews go in the state with no source flag or injection test ([`tests/test_api.py:1`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/tests/test_api.py#L1)). [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13) |
| Non-English handled (F23) | **no.** All examples and tests are English, with no translation or multilingual test ([`tests/test_api.py:1`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/tests/test_api.py#L1)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (10) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each call asks one property; label splits into one yes/no per option ([`src/vibecheck/_plans.py:208`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L208)) |
| Structured state (F3) | yes. Strings pass as-is; dicts, lists, dataclasses and Pydantic models go as JSON with their field names ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)) |
| Batching (F4) | yes. A batch, `assess` and `label` send many questions about one state in one request ([`src/vibecheck/_batch.py:243`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_batch.py#L243)) |
| Thresholds in code (F5) | yes. Cut-offs are validated call arguments, a number or a low-high band, never question text ([`src/vibecheck/_plans.py:306`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L306)) |
| No invented values (F6) | yes. Code computes the score position and counts; README tells callers to keep arithmetic in code ([`src/vibecheck/_plans.py:242`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L242), [`README.md:305`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L305)) |
| Options cover every case, no overlap (F8) | yes. Duplicate labels are rejected, and the shipped examples use described, non-overlapping options ([`src/vibecheck/_plans.py:339`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L339)) |
| An "other" option where needed (F9) | yes. README tells callers to add "other" when options may not cover every case ([`README.md:118`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L118)) |
| Evidence recorded evenly (F10) | n.a.. The caller supplies the state and the library adds no evidence lines ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22)) |
| Confidence drives action, low (F11) | n.a.. Every decision is low and its answer is only returned to the calling code ([`src/vibecheck/_plans.py:161`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L161)) |
| Pinned model version (F12) | n.a.. The library tunes no threshold; README advises pinning `jev-1.13.0` after tuning ([`README.md:508`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L508)) |
| Choice order handled, low (F13) | n.a.. No decision is high or very high, so Choice order is not scored ([`src/vibecheck/_plans.py:181`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L181)) |
| Independent labels (F16) | n.a.. The claim compares batching with separate requests and uses no labels ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)) |
| Held-out result (F17) | n.a.. No threshold or wording was tuned against a reported number ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)) |
| Typed answers read directly (F19) | yes. The backend reads the Noul probability, Choice probabilities and Score probabilities fields ([`src/vibecheck/backends.py:143`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/backends.py#L143)) |
| Data as fields, not templates (F20) | yes. Data goes in the state argument and the question stays separate, with one stateless f-string example ([`src/vibecheck/_run.py:22`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_run.py#L22), [`examples/classify/no_data.py:25`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/no_data.py#L25)) |
| No instructions in the state (F21) | yes. The state is the caller's data; task, label and description go in the instructions ([`src/vibecheck/_plans.py:263`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L263)) |

</details>

## Scores

- Execution 2 of 3: its questions, state, batching and cut-offs are built well, but one of F1-F6 fails, the bare-number Score levels the docs and examples still offer (F2).
- Fit 2 of 3: each verb uses the fitting primitive, probabilities gate `check` and `label`, and batching shares a state, with one mismatch in numeric Score levels (F2).
- Coverage 3 of 3: every verb, threshold, band, batch, schema and test helper the README promises is implemented and tested against a fake backend (F0, F4, F19).
- Evidence 0 of 3: the batching claim of 100 questions matching 100 requests at 1% of tokens has no measurement shown (F7, F15, F18).

## Why this verdict

3, Use with a fix, because nothing sends it to 2: Execution is 2 and no fatal flaw applies. Two capping failures hold it below 4: F2, where bare-number Score levels are offered in the README batch example and `examples/score/numeric_levels.py`, and Evidence 0, because the README's batching claim has no measurement behind it. The library's core (typed verbs, structured state, thresholds and bands, batching, direct reading of typed answers) is sound, so both fixes are small. The F2 call is the borderline one, since the README says described levels give better answers and the library never forces numbers.

## Fixes (from reading the code; not tested against it)

1. **F2 wrong primitive: bare-number Score levels.** Switch the README batch example and `examples/score/numeric_levels.py` to described levels, written as situations with no numbers in the level text. Source: [`primitives/score`](https://docs.typesafe.ai/primitives/score), [`primitives`](https://docs.typesafe.ai/primitives).
2. **F7 nothing measured, with F15 and F18.** Publish the 100-question batching test as a script with its document and counts, or drop the number; report the sample and compare against the separate-request baseline. Confirm with data. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence), [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook).
3. **F22 untrusted text.** Add a README note and a steering-input test for customer text passed as state, with an injection-check Noul before routing. Source: [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages).
4. **F14 and F23, fix-only.** Add a guard for state plus questions above 32k and 64k tokens, and test non-English input. Source: [`models`](https://docs.typesafe.ai/models), [`concepts/state`](https://docs.typesafe.ai/concepts/state).

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
