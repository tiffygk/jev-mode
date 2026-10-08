[← All ratings](README.md)

> **askjevs.site** [https://askjevs.site/](https://askjevs.site/), site-snapshot-2026-10-05 · display
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - Ask Jevs turns visitor questions into Jev Choice, Noul, and Score answers through its site API and displays the results.
> - It exposes each request, typed answer, and probability in an accessible visual trace.
> - Its open question coverage and answer reliability are limited by the offered choices and unverified server logic.

## What holds it back

- **Atomic questions** (F1): “Is coffee healthy and cheap?” asks two properties in one Noul (`responses/03.json:3`). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **No invented values** (F6): Date and arithmetic server logic is absent; no file would answer it (`files/ask.js:245`; `files/api-recent.json:1`).
- **Measured in the workflow** (F7): No project evaluation reports accuracy, cost or latency on labeled questions (`files/index.html:103`). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Options cover every case, no overlap** (F8): A tomato is both a fruit and a berry, yet those appear as rival options (`responses/09.json:8`). https://docs.typesafe.ai/primitives/advanced.md
- **An "other" option where needed** (F9): “Planet or star?” omits dwarf planet and offers no none option (`responses/11.json:8`). https://docs.typesafe.ai/primitives/advanced.md
- **No instructions in the state** (F21): First-request state includes rules telling Jev how to classify words and treat input (`responses/02.json:8`). https://docs.typesafe.ai/concepts/state.md

**Minor:** Data as fields, not templates, low (F20); Untrusted text treated as data, low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/site__askjevs.site--gpt-6-sol.md)

