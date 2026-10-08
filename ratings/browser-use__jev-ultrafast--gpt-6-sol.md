[← All ratings](README.md)

> **browser-use/jev-ultrafast** at [`1231850`](https://github.com/browser-use/jev-ultrafast/tree/1231850a0bf1a0c0341fe408ef1668dbbfdfac46) · library
> ### Verdict 2: Rework it
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ●○○
>
> - Jev chooses a browser operation and its observed target in one request; a separate text model supplies field values.
> - Dynamic typed choices, code-owned element references, stale-page guards, and independent result checks make the loop concrete.
> - Confidence does not gate actions, and the reported successes cover a small set of tasks and sites.

## What holds it back

- **Confidence drives action, high or very high** (F11): An arbitrary-site agent executes the top operation and target regardless of confidence ([`jev_ultrafast/agent.py:117`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/agent.py#L117)). https://docs.typesafe.ai/confidence
- **Choice order handled, very high** (F13): Operation and target Choices keep fixed DOM order; no shuffling or order check ([`jev_ultrafast/model.py:94`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py#L94)). https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook
- **Held-out result** (F17): Reported Flights timings reuse the task changed during development; other tasks are smoke checks ([`docs/performance.md:47`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L47)). https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery
- **Fair baseline** (F18): The matched comparator is an older Jev implementation, with no separate LLM or rules baseline ([`docs/performance.md:20`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/docs/performance.md#L20)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Size limits respected (F14); Data as fields, not templates, very high (F20); Untrusted text treated as data, very high (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/browser-use__jev-ultrafast--gpt-6-sol.md)

