[← All ratings](README.md)

> **altryne/Jevify** at [`11f36f8`](https://github.com/altryne/jevify/tree/11f36f8d548cf5020a20e5eb548f21c3d7181a17) · agent tool
> ### Verdict 3: Use with a fix
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - Jevify gives agents a Jev powered relevance scan and instructions for using Jev during their work.
> - Its scanner sends independent Scores over bounded source windows and returns source linked excerpts with audit samples.
> - The result still depends on the agent reopening evidence, and the repo has only small synthetic validation of behavior.

## What holds it back

- **Held-out result** (F17): Revised questions were rerun on tuning examples; fresh examples cover the same task ([`references/validation-2026-09-21.md:23-24`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L23-L24)). [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one).
- **Fair baseline** (F18): Own validation reports Jev runs without a matched agent or direct-reading baseline ([`references/validation-2026-09-21.md:20-27`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L20-L27); [`references/evaluation.md:9-20`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/evaluation.md#L9-L20)). [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one).
- **No instructions in the state** (F21): Runnable message pack places “Questions target user messages separately from assistant claims” in state context ([`assets/message-signals.json:5`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/message-signals.json#L5)). [State](https://docs.typesafe.ai/concepts/state).

**Minor:** Size limits respected (F14); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/altryne__jevify--gpt-6-sol.md)

