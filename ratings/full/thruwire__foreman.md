[← Summary](../thruwire__foreman.md)

# foreman: full rating

**Verdict 2, Rework it** · workflow · rated 2026-09-30 at [`e5d1aa4`](https://github.com/thruwire/foreman/tree/e5d1aa4518) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Foreman supervises a coding agent by sending ten yes/no Noul checks about its repository and output to Jev each cycle, then lets Python rules steer, stop, verify or finish. It batches the checks, keeps every threshold in config and arbitrates actions in code. The finish gate leans on broad questions, the state includes Jev's own previous scores, and nothing is measured.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Ten Noul checks go to `client.system_one` each cycle, and routing scores conditional responsibilities ([`src/foreman/foreman/jev.py:123`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L123), [`src/foreman/routing.py:469`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/routing.py#L469)) |
| Atomic questions (F1) | **no.** Finish checks are broad or compound: "Given all evidence, is the job ready", tests coverage plus passing ([`src/foreman/responsibilities/definitions/core.completion.toml:18`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.completion.toml#L18), [`src/foreman/responsibilities/definitions/core.verification.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.verification.toml#L6)). concepts/how-to-build-with-system-one |
| Measured in the workflow (F7) | **no.** No accuracy, latency or cost numbers appear; the README calls accuracy unproven ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa4518/README.md#L479)). TypeSafe launch post (build your own evals) |
| Evidence recorded evenly (F10) | **no.** The default `history` provider puts Jev's own previous scores and the previous intervention into the next state ([`src/foreman/evidence.py:37`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/evidence.py#L37)). concepts/state |
| Size limits respected (F14) | **no.** Each field has a character cap, but no total guard and no reported maximum against 64k tokens ([`src/foreman/config.py:75`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/config.py#L75)). models |
| Untrusted text treated as data, low (F22) | **no.** Worker output, diffs and AGENTS.md go in unflagged, and no test injects hostile text ([`src/foreman/observation.py:64`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/observation.py#L64)). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No translation or non-English test exists in the files read. concepts/state |

<details>
<summary><b>What passes (9) and doesn't apply (8)</b></summary>

| Fact | Finding |
|---|---|
| Right primitive (F2) | yes. Every check is a yes/no statement asked as Noul and read as a probability ([`src/foreman/foreman/jev.py:120`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L120)). |
| Structured state (F3) | yes. A dict of named fields (`git_diff`, `agents_md_instructions`, `worker_history` with worker IDs); only the AGENTS.md question names a path ([`src/foreman/observation.py:64`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/observation.py#L64)). |
| Batching (F4) | yes. All active checks sharing an evidence list go in one `system_one` request, and routing scores all candidates in one request ([`src/foreman/foreman/jev.py:114`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L114), [`src/foreman/routing.py:469`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/routing.py#L469)). |
| Thresholds in code (F5) | yes. Every cut-off is a `min_threshold` or `routing_threshold` in packaged TOML, read by directive code ([`src/foreman/responsibilities/definitions/core.worker-health.toml:13`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.worker-health.toml#L13)). |
| No invented values (F6) | yes. Code parses pytest counts, elapsed time and git diffs; Jev only judges yes/no statements ([`src/foreman/observation.py:397`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/observation.py#L397)). |
| Options cover every case, no overlap (F8) | n.a.. No Choice question is used. |
| An "other" option where needed (F9) | n.a.. No Choice question is used. |
| Confidence drives action, low (F11) | yes. Each directive fires only when its probability clears a configured minimum ([`src/foreman/responsibilities/builtin.py:126`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/builtin.py#L126), [`src/foreman/responsibilities/builtin.py:160`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/builtin.py#L160), [`src/foreman/responsibilities/builtin.py:212`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/builtin.py#L212), [`src/foreman/responsibilities/builtin.py:266`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/builtin.py#L266)). |
| Pinned model version (F12) | n.a.. Thresholds are untuned defaults, so the `jev-latest` alias costs nothing here ([`src/foreman/foreman/jev.py:68`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L68), [`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa4518/README.md#L479)). |
| Choice order handled, low (F13) | n.a.. Always n.a. |
| Sample size adequate (F15) | n.a.. No results are claimed. |
| Independent labels (F16) | n.a.. No results are claimed. |
| Held-out result (F17) | n.a.. No results are claimed. |
| Fair baseline (F18) | n.a.. No results are claimed. |
| Typed answers read directly (F19) | yes. Code reads the `noul` probability and validates it as finite and within 0 to 1 ([`src/foreman/foreman/jev.py:47`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L47)). |
| Data as fields, not templates, low (F20) | yes. Question text is static and the evidence travels as state fields ([`src/foreman/foreman/jev.py:120`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/foreman/jev.py#L120)). |
| No instructions in the state (F21) | yes. The state holds evidence, including the repository's AGENTS.md text as content to compare; directions sit in the question ([`src/foreman/responsibilities/definitions/repository.instructions.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/repository.instructions.toml#L6)). |

</details>

## Scores

- Execution 1 of 3: the main decision, finishing the job, rests on a catch-all question and a two-part question, F1 no, and the state feeds Jev's earlier scores back in, F10 no; F2-F6, F11 and F19 hold.
- Fit 3 of 3: Noul fits every yes/no check, confidence gates every action through configured thresholds, and shared-state questions go in one request (F2, F4, F5, F11).
- Coverage 3 of 3: every check the README lists runs and drives a directive, plus routing, steering, retry and verification; the stated goal is met.
- Evidence n.a.: it claims no results and calls Jev's accuracy unproven (F7 no, F15-F18 n.a.).

## Why this verdict

Verdict 2: F1 fails on the main decision, the finish gate, because `ready_to_finish` asks "given all evidence" with no standard and `tests_sufficient` joins coverage with passing, which puts Execution at 1. The design is otherwise sound: Noul fits, thresholds live in config, questions are batched and Python arbitrates every action. Without that F1 failure it would still sit at 3, since F10 also fails: the default `history` provider returns Jev's own earlier scores to it. The main-decision call is borderline, because the worker-health checks are close to atomic and could count as the main decision instead.

## Fixes (from reading the code; not tested against it)

1. Split the broad finish checks (F1): replace `ready_to_finish` with specific yes/no statements against the job's own requirements, and split `tests_sufficient` into coverage and passing, then combine them in code ([`src/foreman/responsibilities/definitions/core.completion.toml:18`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.completion.toml#L18), [`src/foreman/responsibilities/definitions/core.verification.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.verification.toml#L6)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) ("Decompose the questions").
2. Drop `previous_result` and `previous_intervention` from the default evidence (F10), or give them to no check that gates an action ([`src/foreman/evidence.py:37`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/evidence.py#L37)). [`concepts/state`](https://docs.typesafe.ai/concepts/state). Confirm with data: remove the history field and rerun on the same recorded observations.
3. Measure it (F7, no results claimed so Evidence stays n.a.): label a sample of finished and stuck runs, then report precision and recall at the 0.75 and 0.80 thresholds, and calibrate them (`closes_loop: none`). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence); [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery); [`confidence`](https://docs.typesafe.ai/confidence).
4. Add a total size guard on the observation (F14): the per-field caps can add up past 32k tokens ([`src/foreman/config.py:75`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/config.py#L75)). [`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13).
5. Flag worker output, diffs and AGENTS.md text as untrusted and test an injection case (F22, low stakes so no cap); test non-English repositories (F23). [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13); [`concepts/state`](https://docs.typesafe.ai/concepts/state).

<details>
<summary><b>Files read (63)</b></summary>

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
- src/foreman/observation.py -- read (fetched separately)
- src/foreman/evidence.py -- read (fetched separately)

</details>
