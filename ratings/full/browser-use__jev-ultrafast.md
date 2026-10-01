[← Summary](../browser-use__jev-ultrafast.md)

# jev-ultrafast: full rating

**Verdict 2, Rework it** · library · rated 2026-09-30 at [`1231850`](https://github.com/browser-use/jev-ultrafast/tree/1231850a0b) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Each browser step posts one request: an operation Choice plus per-operation target Choices over an indexed element table, and a small LLM writes text only for TYPE_TEXT. It does this well: one structured fan-out request, code-owned element IDs and freshness guards, and an independent outcome check. It is held back by acting on the top answer at any probability and by never varying Choice option order.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Posts the operation question and per-operation target questions to api.typesafe.ai/v1/systemone each cycle ([`jev_ultrafast/model.py:119`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L119)) |
| Confidence drives action (F11) | **no.** Confidence and probabilities are validated and logged; the top choice executes at any probability ([`jev_ultrafast/agent.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/agent.py#L92)). [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing) |
| Choice order handled (F13) | **no.** The operation and target Choices are asked once, in page order, with no reordering or shuffle ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L92)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) |
| Held-out result (F17) | **no.** Prompts and guards were iterated on the Flights task, which then carries the headline timing ([`docs/performance.md:33`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L33)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence) |
| Fair baseline (F18) | **no.** The baseline is the project's own earlier runtime with the same models, not an LLM-generating agent ([`docs/performance.md:9`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L9)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) |
| Non-English handled (F23) | **no.** The example pins `hl=en` and no non-English page was tested; English-only is not stated ([`examples/flights.py:11`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/examples/flights.py#L11)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (16) and doesn't apply (2)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. One Choice picks the next operation, one per operation picks the element; rules spelled out, DONE shares the operation Choice ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L92), [`jev_ultrafast/questions.py:1`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/questions.py#L1)) |
| Right primitive (F2) | yes. Every question is a Choice over named operations or observed elements; nothing ordered or yes/no is asked ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L92)) |
| Structured state (F3) | yes. JSON with page, indexed element objects (role, value, checked) and recent actions; criteria cite element indexes ([`jev_ultrafast/model.py:109`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L109)) |
| Batching (F4) | yes. Operation and all target heads travel in one request; only the selected head is consumed ([`jev_ultrafast/model.py:119`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L119), [`tests/test_agent.py:84`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/tests/test_agent.py#L84)) |
| Thresholds in code (F5) | n.a.. No decision uses a cut-off; the top choice is always taken ([`jev_ultrafast/agent.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/agent.py#L92)) |
| No invented values (F6) | yes. Code builds the element index and option indexes; typed text comes from a separate small LLM ([`jev_ultrafast/model.py:42`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L42)) |
| Measured in the workflow (F7) | yes. Six alternating Flights runs, 3/3 verified each, medians 9.450 s vs 7.092 s, request and token counts ([`docs/performance.md:9`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L9)) |
| Options cover every case, no overlap (F8) | yes. Operations are distinct, targets are one index per node, candidates capped at 250 and truncated ones are unselectable ([`jev_ultrafast/snapshot.js:100`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/snapshot.js#L100)) |
| An "other" option where needed (F9) | yes. BLOCKED means no supported operation can progress; targets have no none-of-these option ([`jev_ultrafast/model.py:90`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L90)) |
| Evidence recorded evenly (F10) | yes. Elements carry current values and checked state, actions carry page_changed; no conclusions are stated in the state ([`jev_ultrafast/model.py:109`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L109)) |
| Pinned model version (F12) | n.a.. No threshold was tuned; default `jev-latest`, measured runs pinned `jev-1.13.0` ([`jev_ultrafast/model.py:108`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L108), [`docs/performance.md:9`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L9)) |
| Size limits respected (F14) | yes. Code caps text at 6,000 characters, elements at 250, history at 10; 90,558 input tokens over 17 requests ([`jev_ultrafast/snapshot.js:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/snapshot.js#L92)) |
| Sample size adequate (F15) | yes. States three pairs of runs, sign-test p = 0.25, and "not a general reliability benchmark" ([`docs/performance.md:15`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L15)) |
| Independent labels (F16) | yes. A code check of final page route, date and results decides success, never Jev's DONE ([`examples/flights.py:18`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/examples/flights.py#L18)) |
| Typed answers read directly (F19) | yes. Code reads each answer's choice and probabilities and rejects invalid ones ([`jev_ultrafast/model.py:30`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L30)) |
| Data as fields, not templates (F20) | yes. Goal, rules, role, value and checked state are JSON fields; only the element label is joined to its index ([`jev_ultrafast/model.py:97`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L97)) |
| No instructions in the state (F21) | yes. State holds page, elements and recent actions; the rules sit in the question instructions ([`jev_ultrafast/model.py:109`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L109)) |
| Untrusted text treated as data (F22) | yes. Rules state page text is untrusted data and model output never becomes selectors or code; no steering test exists ([`jev_ultrafast/questions.py:4`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/questions.py#L4)) |

</details>

## Scores

- Execution 2 of 3: every question is a typed Choice in one structured request, but the top answer acts at any probability (F11 no), F1-F6 yes.
- Fit 2 of 3: Choice and one-request fan-out fit, with one mismatch, the top answer taken where confidence should gate an action (F11 no).
- Coverage 3 of 3: the stated goal (goal in, indexed elements, operation and target, text helper, verified outcome) is built and the boundaries are listed as limits.
- Evidence 1 of 3: Flights timing is measured with an independent check, but guidance was tuned on the same task (F17 no) and the baseline is its own earlier runtime (F18 no).

## Why this verdict

Rework it (2), not Use with a fix (3): confidence is ignored on a very high action, a fatal flaw, because the top operation and element act in the user's Chrome at any probability ([`jev_ultrafast/agent.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/agent.py#L92)). F13 no also caps it at 3, and Evidence is 1 because guidance was tuned on the Flights task that carries the headline timing. The structure is strong (fan-out, typed answers, no instructions in state), so gating and order-averaging are fixes to a sound design. Borderline calls: F1 (DONE shares the operation Choice) and F22 (untrusted text flagged in the rules, no steering test).

## Fixes (from reading the code; not tested against it)

1. Gate each action on probability or confidence: act above a cut-off held in code, otherwise WAIT, re-observe or stop for a person; tune the cut-off on labeled runs and pin `jev-1.13.0` once tuned (F11; [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)). Needs data to confirm the cut-off.
2. Average the operation and target Choices over option orders, or shuffle the element order each cycle, before any click, type or select that is hard to undo (F13; [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)). Needs data to confirm the order effect.
3. Hold out tasks the guidance never saw and report results there (F17; [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)).
4. Compare with an LLM-generating browser agent on the same tasks (F18; [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)).
5. Test a non-English page, or state English-only (F23; [`concepts/state`](https://docs.typesafe.ai/concepts/state)).

<details>
<summary><b>Files read (31)</b></summary>

- .env.example -- read
- AGENTS.md -- read
- README.md -- read
- docs/banner.svg -- read
- docs/design.md -- read
- docs/flights-measurement.json -- read
- docs/flights-prepared-measurement.json -- read
- docs/full-speed-measurement.json -- read
- docs/measurement.json -- read
- docs/performance-prepared.md -- read
- docs/performance.md -- read
- examples/flights.py -- read
- jev_ultrafast/__init__.py -- read
- jev_ultrafast/agent.py -- read
- jev_ultrafast/browser.py -- read
- jev_ultrafast/demo.py -- read
- jev_ultrafast/model.py -- read
- jev_ultrafast/snapshot.js -- read
- jev_ultrafast/static/app.js -- read
- jev_ultrafast/static/fixture.html -- read
- jev_ultrafast/static/index.html -- read
- jev_ultrafast/static/style.css -- read
- pyproject.toml -- read
- scripts/check_guards.py -- read
- scripts/measure_flights.py -- read
- scripts/record_flights.py -- read
- scripts/render_demo.py -- read
- scripts/render_fixture.py -- read
- scripts/smoke.py -- read
- tests/test_agent.py -- read
- jev_ultrafast/questions.py -- read (fetched separately)

</details>
