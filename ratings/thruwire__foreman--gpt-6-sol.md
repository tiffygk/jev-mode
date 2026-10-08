[← All ratings](README.md)

> **thruwire/foreman** at [`e5d1aa4`](https://github.com/thruwire/foreman/tree/e5d1aa45183382390e388512dcbfebd747ec89ba) · library
> ### Verdict 2: Rework it
> Execution ●○○ · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - Foreman uses hosted Jev to route supervision responsibilities and score coding-worker progress, verification, completion and escalation.
> - It batches typed Noul checks, keeps intervention rules in Python, and provides runtime and hook paths.
> - Broad completion questions and absent task-specific calibration leave autonomous interventions insufficiently grounded.

## What holds it back

- **Atomic questions** (F1): Free-form jobs reach broad `requirements_satisfied` and `ready_to_finish` judgments without a stated criterion ([`src/foreman/responsibilities/definitions/core.completion.toml:11`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L11)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Structured state** (F3): Questions about heterogeneous worker and repository fields never identify specific state paths ([`src/foreman/responsibilities/definitions/core.completion.toml:5`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/responsibilities/definitions/core.completion.toml#L5); [`src/foreman/foreman/jev.py:124`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/foreman/jev.py#L124)). https://docs.typesafe.ai/concepts/state
- **Measured in the workflow** (F7): The repository says Jev accuracy is unproven and supplies no task accuracy, cost or latency numbers ([`README.md:479`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L479)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Evidence recorded evenly** (F10): Prior model conclusions enter later assessment state alongside raw evidence ([`README.md:153`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L153); [`src/foreman/runtime.py:412`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/src/foreman/runtime.py#L412)). https://docs.typesafe.ai/concepts/state
- **No instructions in the state** (F21): Repository AGENTS instructions are included as a state field during checks ([`README.md:151`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/README.md#L151); [`tests/test_foreman.py:126`](https://github.com/thruwire/foreman/blob/e5d1aa45183382390e388512dcbfebd747ec89ba/tests/test_foreman.py#L126)). https://docs.typesafe.ai/concepts/state

**Minor:** Pinned model version (F12); Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/thruwire__foreman--gpt-6-sol.md)

