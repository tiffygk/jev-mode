[← All ratings](README.md)

> **Ask Jevs** [https://askjevs.site/](https://askjevs.site/), site as captured 2026-09-28 · display
> ### Verdict 2: Rework it
> Execution ●○○ · Fit ●●○ · Coverage ●●● · Evidence n.a.
>
> - Ask Jevs is a parody question site that sends a free-text question to Jev in one batched request of 8 to 16 questions, then a second request that picks or rates.
> - It batches well, reads typed fields directly and shows every probability.
> - The raw question has no standard, word tags use the wrong primitive, options overlap or omit the right answer and directions sit in the state; the server code is not public.
>
> **Top fix:** Give the yes/no and final questions a stated standard and split compound ones ("healthy and cheap") into separate questions, combined in code ([`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one), "Decompose the questions").

## What holds it back

- **Atomic questions** (F1): The yes/no and final questions are raw user text, no standard; "healthy and cheap" gets Yes (`03.json`, `05.json`). concepts/how-to-build-with-system-one
- **Right primitive** (F2): Each word is tagged by a two-option Choice, which is a yes/no; other picks fit (`01.json`). primitives/advanced
- **Thresholds in code** (F5): Client literals 0.5 and 0.005 only (`ask.js:86`, `ask.js:89`); the server's lowConfidence rule is not public, no file would answer it.
- **Measured in the workflow** (F7): No accuracy, cost or latency figures anywhere on the site or in its files (`index.html`, `summary.md`). concepts/how-to-build-with-system-one
- **Options cover every case, no overlap** (F8): Kind options choice and noul overlap (noul 0.41); a bogus alternative "Mona Lisa" was extracted (`02.json`). primitives/advanced
- **An "other" option where needed** (F9): The picked Choice has no none-of-these option, so Pluto "planet or star" returns planet at 1.00 (`11.json`). primitives/advanced
- **No instructions in the state** (F21): `state.rules` tells Jev how to answer each word question and what option means (`01.json`). concepts/state

## Fixes (from reading the code; not tested against it)

1. F1: give the yes/no and final questions a stated standard and split compound ones ("healthy and cheap") into separate questions, combined in code ([`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one), "Decompose the questions").
2. F2: tag each word with a Noul, not a two-option Choice ([`primitives`](https://docs.typesafe.ai/primitives), [`primitives/score`](https://docs.typesafe.ai/primitives/score)).
3. F8: make the extracted options exclusive and flag overlap or a spurious option such as "Mona Lisa" before the final pick; confirm with data ([`primitives`](https://docs.typesafe.ai/primitives), Choice).

**Minor:** Untrusted text treated as data, high or low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/site__askjevs.site.md)

