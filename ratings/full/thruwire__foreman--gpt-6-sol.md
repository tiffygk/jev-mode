[← Summary](../thruwire__foreman--gpt-6-sol.md)

# foreman: full rating

**Verdict 2, Rework it** · library · rated 2026-10-06 at [`e5d1aa4`](https://github.com/thruwire/foreman/tree/e5d1aa45183382390e388512dcbfebd747ec89ba) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Foreman uses hosted Jev to route supervision responsibilities and score coding-worker progress, verification, completion and escalation. It batches typed Noul checks, keeps intervention rules in Python, and provides runtime and hook paths. Broad completion questions and absent task-specific calibration leave autonomous interventions insufficiently grounded.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Async SDK calls score routed checks and conditional responsibilities ([`src/foreman/foreman/jev.py:123`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L123); [`src/foreman/routing.py:469`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/routing.py#L469)). |
| Atomic questions (F1) | **no.** Free-form jobs reach broad `requirements_satisfied` and `ready_to_finish` judgments without a stated criterion ([`src/foreman/responsibilities/definitions/core.completion.toml:11`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L11)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Structured state (F3) | **no.** Questions about heterogeneous worker and repository fields never identify specific state paths ([`src/foreman/responsibilities/definitions/core.completion.toml:5`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L5); [`src/foreman/foreman/jev.py:124`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L124)). https://docs.typesafe.ai/concepts/state |
| Measured in the workflow (F7) | **no.** The repository says Jev accuracy is unproven and supplies no task accuracy, cost or latency numbers ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Evidence recorded evenly (F10) | **no.** Prior model conclusions enter later assessment state alongside raw evidence ([`README.md:153`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L153); [`src/foreman/runtime.py:412`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/runtime.py#L412)). https://docs.typesafe.ai/concepts/state |
| Pinned model version (F12) | **no.** Tuned-looking TOML thresholds run against the moving `jev-latest` alias ([`src/foreman/foreman/jev.py:68`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L68); [`src/foreman/responsibilities/definitions/core.completion.toml:20`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L20)). https://docs.typesafe.ai/models |
| Size limits respected (F14) | **no.** Per-field caps lack a guard for combined state and question token limits ([`src/foreman/config.py:75`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/config.py#L75); [`src/foreman/foreman/jev.py:123`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L123)). https://docs.typesafe.ai/models |
| No instructions in the state (F21) | **no.** Repository AGENTS instructions are included as a state field during checks ([`README.md:151`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L151); [`tests/test_foreman.py:126`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/tests/test_foreman.py#L126)). https://docs.typesafe.ai/concepts/state |
| Untrusted text treated as data (F22) | **no.** Job, tool output and repository instructions enter state without a steering test or source flag ([`src/foreman/hooks.py:520`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/hooks.py#L520); [`README.md:148`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L148)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Free-form jobs admit other languages, but the offline tests supply no non-English assessment cases ([`README.md:5`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L5); [`tests/test_foreman.py:117`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/tests/test_foreman.py#L117)). https://docs.typesafe.ai/concepts/state |

<details>
<summary><b>What passes (7) and doesn't apply (7)</b></summary>

| Fact | Finding |
|---|---|
| Right primitive (F2) | yes. Built-in yes/no checks and routes use Noul probabilities ([`src/foreman/foreman/jev.py:119`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L119); [`src/foreman/routing.py:458`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/routing.py#L458)). |
| Batching (F4) | yes. Checks sharing evidence are grouped into one parallel request; distinct evidence selections have separate states ([`src/foreman/foreman/jev.py:113`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L113)). |
| Thresholds in code (F5) | yes. TOML minimums are read by Python directive logic ([`src/foreman/responsibilities/definitions/core.completion.toml:20`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L20); [`src/foreman/responsibilities/builtin.py:265`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/builtin.py#L265)). |
| No invented values (F6) | yes. Jev judges semantic conditions; Python handles thresholds, counts and lifecycle bounds ([`src/foreman/responsibilities/builtin.py:265`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/builtin.py#L265); [`src/foreman/policy.py:44`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/policy.py#L44)). |
| Options cover every case, no overlap (F8) | n.a.. No Choice questions ([`src/foreman/foreman/jev.py:119`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L119)). |
| An other option where needed (F9) | n.a.. No Choice questions ([`src/foreman/foreman/jev.py:119`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L119)). |
| Confidence drives action (F11) | yes. Routing and interventions require explicit probability thresholds; the hook veto follows selected directives ([`src/foreman/routing.py:414`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/routing.py#L414); [`src/foreman/responsibilities/builtin.py:127`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/builtin.py#L127); [`src/foreman/hooks.py:570`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/hooks.py#L570)). |
| Choice order handled (F13) | n.a.. No Choice decisions ([`src/foreman/foreman/jev.py:119`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L119)). |
| Sample size adequate (F15) | n.a.. No results claimed ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). |
| Independent labels (F16) | n.a.. No results claimed ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). |
| Held-out result (F17) | n.a.. No results claimed ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). |
| Fair baseline (F18) | n.a.. No results claimed ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). |
| Typed answers read directly (F19) | yes. SDK Noul fields are parsed as numeric probabilities ([`src/foreman/foreman/jev.py:42`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L42); [`src/foreman/routing.py:317`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/routing.py#L317)). |
| Data as fields, not templates (F20) | yes. Job and observation travel in JSON state; check text comes from static TOML ([`src/foreman/routing.py:470`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/routing.py#L470); [`src/foreman/foreman/jev.py:119`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L119)). |

</details>

## Scores

- Execution 1 of 3: the main completion judgment is broad and questions do not identify state paths, F1 and F3.
- Fit 3 of 3: Noul, batched requests and probability gates suit the stated supervision decisions, F2, F4 and F11.
- Coverage 3 of 3: the shipped code implements its stated routing, monitoring, intervention and verification paths, F0 and F4.
- Evidence n.a.: the repository claims no measured Jev outcome, F7 and F15-F18.

## Why this verdict

Verdict 2, Rework it: the main completion decision relies on broad questions over arbitrary software jobs (F1), giving Execution 1; this alone triggers verdict 2. Named state fields do not appear as explicit paths in those questions (F3), and the repository reports no measured Jev accuracy (F7). The rule-based arbiter and confidence thresholds are strong implementation choices, but they cannot establish whether the semantic judgments are reliable enough for tool vetoes and job completion. The previous verdict used an extract with no recorded commit and is context only.

<details>
<summary><b>Files read (61)</b></summary>

- .env.example -- read
- CONTRIBUTING.md -- read
- README.md -- read
- docs/extensions.md -- read
- docs/hooks.md -- read
- docs/routing.md -- read
- docs/runtime.md -- read
- docs/why-jev.md -- read
- docs/workers.md -- read
- pyproject.toml -- read
- src/foreman/__init__.py -- read
- src/foreman/__main__.py -- read
- src/foreman/cli.py -- read
- src/foreman/config.py -- read
- src/foreman/extensions.py -- read
- src/foreman/factory.py -- read
- src/foreman/foreman/__init__.py -- read
- src/foreman/foreman/jev.py -- read
- src/foreman/hook_adapters.py -- read
- src/foreman/hooks.py -- read
- src/foreman/models/assessment.py -- read
- src/foreman/models/events.py -- read
- src/foreman/models/result.py -- read
- src/foreman/policy.py -- read
- src/foreman/responsibilities/__init__.py -- read
- src/foreman/responsibilities/base.py -- read
- src/foreman/responsibilities/builtin.py -- read
- src/foreman/responsibilities/configuration.py -- read
- src/foreman/responsibilities/definitions/core.completion.toml -- read
- src/foreman/responsibilities/definitions/core.human-escalation.toml -- read
- src/foreman/responsibilities/definitions/core.verification.toml -- read
- src/foreman/responsibilities/definitions/core.worker-health.toml -- read
- src/foreman/responsibilities/definitions/quality.documentation.toml -- read
- src/foreman/responsibilities/definitions/repository.instructions.toml -- read
- src/foreman/routing.py -- read
- src/foreman/runtime.py -- read
- src/foreman/steering.py -- read
- src/foreman/terminal.py -- read
- src/foreman/workers/__init__.py -- read
- src/foreman/workers/base.py -- read
- src/foreman/workers/codex.py -- read
- src/foreman/workers/codex_app_server.py -- read
- src/foreman/workers/hermes.py -- read
- src/foreman/workers/opencode.py -- read
- src/foreman/workers/simulation.py -- read
- tests/test_config.py -- read
- tests/test_evidence.py -- read
- tests/test_extensions.py -- read
- tests/test_foreman.py -- read
- tests/test_hermes.py -- read
- tests/test_hooks.py -- read
- tests/test_integration.py -- read
- tests/test_models.py -- read
- tests/test_opencode.py -- read
- tests/test_persistence.py -- read
- tests/test_policy.py -- read
- tests/test_responsibilities.py -- read
- tests/test_responsibility_config.py -- read
- tests/test_routing.py -- read
- tests/test_runtime.py -- read
- tests/test_worker.py -- read

</details>
