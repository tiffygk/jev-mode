[← Summary](../browser-use__jev-ultrafast--gpt-6-sol.md)

# jev-ultrafast: full rating

**Verdict 2, Rework it** · library · rated 2026-10-06 at [`1231850`](https://github.com/browser-use/jev-ultrafast/tree/1231850a0bf1a0c0341fe408ef1668dbbfdfac46) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jev chooses a browser operation and its observed target in one request; a separate text model supplies field values. Dynamic typed choices, code-owned element references, stale-page guards, and independent result checks make the loop concrete. Confidence does not gate actions, and the reported successes cover a small set of tasks and sites.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The live policy posts operation and target Choice questions to System One ([`jev_ultrafast/model.py:119`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L119)). |
| Confidence drives action, high or very high (F11) | **no.** An arbitrary-site agent executes the top operation and target regardless of confidence ([`jev_ultrafast/agent.py:117`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/agent.py#L117)). https://docs.typesafe.ai/confidence |
| Choice order handled, very high (F13) | **no.** Operation and target Choices keep fixed DOM order; no shuffling or order check ([`jev_ultrafast/model.py:94`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L94)). https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook |
| Size limits respected (F14) | **no.** A caller-supplied goal and DOM labels can exceed limits despite text and action caps ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L92), [`jev_ultrafast/snapshot.js:100`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/snapshot.js#L100)). https://docs.typesafe.ai/models |
| Held-out result (F17) | **no.** Reported Flights timings reuse the task changed during development; other tasks are smoke checks ([`docs/performance.md:47`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L47)). https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery |
| Fair baseline (F18) | **no.** The matched comparator is an older Jev implementation, with no separate LLM or rules baseline ([`docs/performance.md:20`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L20)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Data as fields, not templates, very high (F20) | **no.** An arbitrary user goal enters question instructions; target labels are interpolated into option text ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L92)). https://docs.typesafe.ai/primitives/advanced |
| Untrusted text treated as data, very high (F22) | **no.** Arbitrary goals and web labels enter questions; no steering test covers their effect ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L92)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Arbitrary web goals are supported, but tests cover English tasks only ([`tests/test_agent.py:1`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/tests/test_agent.py#L1)). https://docs.typesafe.ai/models |

<details>
<summary><b>What passes (12) and doesn't apply (3)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Operation and each target head ask for one next choice ([`jev_ultrafast/model.py:91`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L91)). |
| Right primitive (F2) | yes. Named operations and observed targets are Choice questions ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L92)). |
| Structured state (F3) | yes. Page fields, indexed elements, and recent actions travel as named JSON fields ([`jev_ultrafast/model.py:109`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L109)). |
| Batching (F4) | yes. Speculative target heads share the operation request ([`jev_ultrafast/model.py:94`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L94)). |
| Thresholds in code (F5) | n.a.. No probability cutoff is used ([`jev_ultrafast/model.py:120`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L120)). |
| No invented values (F6) | yes. Jev selects observed operations and targets; a separate helper produces text ([`jev_ultrafast/model.py:129`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L129)). |
| Measured in the workflow (F7) | yes. Three matched pairs report task time, calls, and verified outcomes ([`docs/performance.md:9`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L9)). |
| Options cover every case, no overlap (F8) | yes. Offered targets map to distinct observed actions; unsupported progress has BLOCKED ([`jev_ultrafast/model.py:90`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L90)). |
| An "other" option where needed (F9) | n.a.. BLOCKED covers unsupported progress and target heads contain offered actions ([`jev_ultrafast/model.py:90`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L90)). |
| Evidence recorded evenly (F10) | yes. Every offered target includes its label, current value, and applicable control state ([`jev_ultrafast/model.py:97`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L97)). |
| Pinned model version (F12) | n.a.. No probability threshold was tuned ([`jev_ultrafast/model.py:108`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L108)). |
| Sample size adequate (F15) | yes. The three-pair speed result is explicitly limited to one task and disclaims broad reliability ([`docs/performance.md:18`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L18)). |
| Independent labels (F16) | yes. A separate page predicate checks route, date, and visible results after DONE ([`examples/flights.py:18`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/examples/flights.py#L18)). |
| Typed answers read directly (F19) | yes. Code validates the Choice fields and maps the selected target to an observed action ([`jev_ultrafast/model.py:120`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L120)). |
| No instructions in the state (F21) | yes. State contains page observations, element data, and action history; rules live in questions ([`jev_ultrafast/model.py:109`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L109)). |

</details>

## Scores

- Execution 2 of 3: Atomic typed questions, structured state, batching, and direct answer use work; ungated high-stakes action lowers it (F1-F6, F11, F19).
- Fit 2 of 3: Choice and speculative batching suit dynamic browser actions, but confidence does not gate automatic execution (F2, F4, F11).
- Coverage 3 of 3: The operation/target request and selected-head execution implement the cited fan-out pattern throughout the loop (F4, F19).
- Evidence 1 of 3: Timings and independent outcome checks are concrete, but the main task was used during development and lacks a non-Jev baseline (F7, F16-F18).

## Why this verdict

Verdict 2, Rework it: F11 is fatal because the exported agent automatically executes the top Choice on arbitrary sites without using confidence. Stale-page checks reduce execution errors but do not test whether Jev chose the right action. Fixed Choice order and untrusted goal/page text add risk at very high stakes. The measured speedup is credible for its narrow task, while broader accuracy remains unestablished.

<details>
<summary><b>Files read (30)</b></summary>

- `.env.example` -- read
- `AGENTS.md` -- read
- `README.md` -- read
- `docs/banner.svg` -- read
- `docs/design.md` -- read
- `docs/flights-measurement.json` -- read
- `docs/flights-prepared-measurement.json` -- read
- `docs/full-speed-measurement.json` -- read
- `docs/measurement.json` -- read
- `docs/performance-prepared.md` -- read
- `docs/performance.md` -- read
- `examples/flights.py` -- read
- `jev_ultrafast/__init__.py` -- read
- `jev_ultrafast/agent.py` -- read
- `jev_ultrafast/browser.py` -- read
- `jev_ultrafast/demo.py` -- read
- `jev_ultrafast/model.py` -- read
- `jev_ultrafast/snapshot.js` -- read
- `jev_ultrafast/static/app.js` -- read
- `jev_ultrafast/static/fixture.html` -- read
- `jev_ultrafast/static/index.html` -- read
- `jev_ultrafast/static/style.css` -- read
- `pyproject.toml` -- read
- `scripts/check_guards.py` -- read
- `scripts/measure_flights.py` -- read
- `scripts/record_flights.py` -- read
- `scripts/render_demo.py` -- read
- `scripts/render_fixture.py` -- read
- `scripts/smoke.py` -- read
- `tests/test_agent.py` -- read

</details>
