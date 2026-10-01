[← All ratings](README.md)

> **thruwire/foreman** at [`e5d1aa4`](https://github.com/thruwire/foreman/tree/e5d1aa4518) · workflow
> ### Verdict 2: Rework it
> Execution ●○○ · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - Foreman supervises a coding agent by sending ten yes/no Noul checks about its repository and output to Jev each cycle, then lets Python rules steer, stop, verify or finish.
> - It batches the checks, keeps every threshold in config and arbitrates actions in code.
> - The finish gate leans on broad questions, the state includes Jev's own previous scores, and nothing is measured.
>
> **Top fix:** Split the broad finish checks (F1): replace `ready_to_finish` with specific yes/no statements against the job's own requirements, and split `tests_sufficient` into coverage and passing, then combine them in code ([`src/foreman/responsibilities/definitions/core.completion.toml:18`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.completion.toml#L18), [`src/foreman/responsibilities/definitions/core.verification.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.verification.toml#L6)).

## What holds it back

- **Atomic questions** (F1): Finish checks are broad or compound: "Given all evidence, is the job ready", tests coverage plus passing ([`src/foreman/responsibilities/definitions/core.completion.toml:18`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.completion.toml#L18), [`src/foreman/responsibilities/definitions/core.verification.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.verification.toml#L6)). concepts/how-to-build-with-system-one
- **Measured in the workflow** (F7): No accuracy, latency or cost numbers appear; the README calls accuracy unproven ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa4518/README.md#L479)). TypeSafe launch post (build your own evals)
- **Evidence recorded evenly** (F10): The default `history` provider puts Jev's own previous scores and the previous intervention into the next state ([`src/foreman/evidence.py:37`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/evidence.py#L37)). concepts/state

## Fixes (from reading the code; not tested against it)

1. Split the broad finish checks (F1): replace `ready_to_finish` with specific yes/no statements against the job's own requirements, and split `tests_sufficient` into coverage and passing, then combine them in code ([`src/foreman/responsibilities/definitions/core.completion.toml:18`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.completion.toml#L18), [`src/foreman/responsibilities/definitions/core.verification.toml:6`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/responsibilities/definitions/core.verification.toml#L6)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) ("Decompose the questions").
2. Drop `previous_result` and `previous_intervention` from the default evidence (F10), or give them to no check that gates an action ([`src/foreman/evidence.py:37`](https://github.com/thruwire/foreman/blob/e5d1aa4518/src/foreman/evidence.py#L37)). [`concepts/state`](https://docs.typesafe.ai/concepts/state). Confirm with data: remove the history field and rerun on the same recorded observations.
3. Measure it (F7, no results claimed so Evidence stays n.a.): label a sample of finished and stuck runs, then report precision and recall at the 0.75 and 0.80 thresholds, and calibrate them (`closes_loop: none`). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence); [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery); [`confidence`](https://docs.typesafe.ai/confidence).

**Minor:** Size limits respected (F14); Untrusted text treated as data, low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/thruwire__foreman.md)

