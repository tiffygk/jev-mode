[← All ratings](README.md)

> **umatter/jevtools** at [`6ab3541`](https://github.com/umatter/jevtools/tree/6ab35414c8) · library
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ●○○
>
> - jevtools is a Python library that lets Jev pick a tool and every argument for an app's own assistant: code builds candidate pools, Jev elects one per slot in a single fan-out request, and a risk-tiered policy turns the composed confidence into execute, confirm, clarify or refuse.
> - It does this well: every value is chosen from nominated candidates, thresholds are explicit and tiered, injected text is channel-blocked, and live Jev was measured on a held-out benchmark with negative controls.
> - Its defaults are priors, not tuned on any user's traffic, and the library claims no calibrated confidence until a user fits a calibrator.
>
> **Top fix:** Ask the very high identity Choice (recipient, share target, invitee) in at least two option orders and act only when they agree, or enable `probes.reverse` for the external tier by default.

## What holds it back

- **Evidence recorded evenly** (F10): Code names up to three matching records in some tool options only, a conclusion the bench shows shifts answers ([`src/jevtools/templates.py:224-230`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L224-L230)). [`concepts/state`](https://docs.typesafe.ai/concepts/state)
- **Choice order handled** (F13): Identity Choices use one canonical order; reversed-order probes run only for critical tools, which never auto-execute ([`src/jevtools/policy.py:167-168`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L167-L168), [`src/jevtools/candidates.py:454-466`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L454-L466)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)
- **Held-out result** (F17): Defaults were chosen on the held-out runs, then the same set gives the 93% headline ([`docs/BENCH.md:240`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L240), [`docs/BENCH.md:264`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L264), [`docs/BENCH.md:307-324`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L307-L324)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)
- **Fair baseline** (F18): Only the oracle ceiling and a lexical simulator are run; "far below LLM tool callers" is asserted, not measured ([`docs/BENCH.md:547-549`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L547-L549)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)

## Fixes (from reading the code; not tested against it)

1. F13: ask the very high identity Choice (recipient, share target, invitee) in at least two option orders and act only when they agree, or enable `probes.reverse` for the external tier by default. A fix to confirm with data (rerun the held-out bench). Docs: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
2. F20: pass the mention, the item and the more-list as JSON fields in the question object, the way the verify and accept questions already do, instead of splicing them into `T_MENTION`, `T_ITEM` and `T_MORE` ([`src/jevtools/templates.py:43-45`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L43-L45)). Docs: https://docs.typesafe.ai/primitives/advanced.md
3. F10: give every tool option the same kind of evidence, or drop record hints from option text and keep them in the state as facts. A fix to confirm with data: remove the hints and rerun the held-out bench. Docs: https://docs.typesafe.ai/concepts/state.md

**Minor:** Data as fields, not templates (F20); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/umatter__jevtools.md)

