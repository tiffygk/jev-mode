[← All ratings](README.md)

> **browser-use/jev-ultrafast** at [`1231850`](https://github.com/browser-use/jev-ultrafast/tree/1231850a0b) · library
> ### Verdict 2: Rework it
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ●○○
>
> - Each browser step posts one request: an operation Choice plus per-operation target Choices over an indexed element table, and a small LLM writes text only for TYPE_TEXT.
> - It does this well: one structured fan-out request, code-owned element IDs and freshness guards, and an independent outcome check.
> - It is held back by acting on the top answer at any probability and by never varying Choice option order.
>
> **Top fix:** Gate each action on probability or confidence: act above a cut-off held in code, otherwise WAIT, re-observe or stop for a person; tune the cut-off on labeled runs and pin `jev-1.13.0` once tuned (F11; [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)).

## What holds it back

- **Confidence drives action** (F11): Confidence and probabilities are validated and logged; the top choice executes at any probability ([`jev_ultrafast/agent.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/agent.py#L92)). [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)
- **Choice order handled** (F13): The operation and target Choices are asked once, in page order, with no reordering or shuffle ([`jev_ultrafast/model.py:92`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/jev_ultrafast/model.py#L92)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)
- **Held-out result** (F17): Prompts and guards were iterated on the Flights task, which then carries the headline timing ([`docs/performance.md:33`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L33)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)
- **Fair baseline** (F18): The baseline is the project's own earlier runtime with the same models, not an LLM-generating agent ([`docs/performance.md:9`](https://github.com/browser-use/jev-ultrafast/blob/1231850a0b/docs/performance.md#L9)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)

## Fixes (from reading the code; not tested against it)

1. Gate each action on probability or confidence: act above a cut-off held in code, otherwise WAIT, re-observe or stop for a person; tune the cut-off on labeled runs and pin `jev-1.13.0` once tuned (F11; [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)). Needs data to confirm the cut-off.
2. Average the operation and target Choices over option orders, or shuffle the element order each cycle, before any click, type or select that is hard to undo (F13; [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook)). Needs data to confirm the order effect.
3. Hold out tasks the guidance never saw and report results there (F17; [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)).

**Minor:** Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/browser-use__jev-ultrafast.md)

