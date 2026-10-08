[← Summary](../site__askjevs.site.md)

# Ask Jevs: full rating

**Verdict 2, Rework it** · workflow · rated 2026-10-06 [https://askjevs.site/](https://askjevs.site/), site-snapshot-2026-10-05 · read: full · rubric 2026-09-29.2 · claude-sonnet-5-5, medium effort

## Summary

Ask Jevs sends each visitor question through one Jev request that sorts it by kind and marks its alternatives, then a second request that picks, confirms or rates, and shows every Jev reply. It batches its independent questions, uses fitting primitives, reads typed answers directly and shows its work. It passes the visitor's raw question to Jev with no standard, offers overlapping or incomplete alternatives, mixes directions into the state, and gates nothing on probability.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The site's own /api/jevs and /api/ask backends send typed questions to POST /v1/systemone, model jev-1.13.0 (`responses/06.json:8`) |
| Atomic questions (F1) | **no.** The raw visitor question is the yes Noul, with no standard: "Is a hot dog a sandwich?" (`files/ask.js:10`). Jev docs: https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Thresholds in code (F5) | **unknown.** The server holds the cut-off, about 0.8 in the captures; fetch failed for limits.mjs, api/jevs.js and server.mjs, all 404 (`responses/11.json:8`) |
| Measured in the workflow (F7) | **no.** No accuracy, cost or latency figures; the page only prints per-ask milliseconds and tokens (`files/ask.js:137`). Jev docs: evals |
| Options cover every case, no overlap (F8) | **no.** Kind's choice and noul options overlap: "da Vinci or Raphael" scored choice 0.58, noul 0.41 (`responses/02.json`). Jev docs: primitives/advanced |
| An "other" option where needed (F9) | **no.** Visitor alternatives get no "none of these": "star or planet" picked planet at 1.00 (`responses/13.json:8`). https://docs.typesafe.ai/primitives/advanced.md |
| Confidence drives action, low (F11) | **no.** Kind routes at 0.47 and a coin-flip refund answer shows; the page never reads lowConfidence (`responses/05.json`). Jev docs: confidence |
| Pinned model version (F12) | **unknown.** Responses report jev-1.13.0, but no file would answer it: the server's request code is not served (`responses/01.json:8`) |
| Data as fields, not templates (F20) | **no.** The visitor's question sits in the yes and answer question text, not a state field (`responses/10.json`). Jev docs: primitives/advanced |
| No instructions in the state (F21) | **no.** state.rules holds directions for the word questions; the answer-step context says "Answer from general knowledge" (`responses/01.json`). Jev docs: concepts/state |
| Untrusted text treated as data (F22) | **no.** Pasted notes go in an unflagged context field and no injection test exists (`responses/06.json`). Jev docs: model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Any language can be typed and no non-English test or translation is shown (`files/index.html:56`). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (6) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Right primitive (F2) | yes. Noul for yes-or-no, Choice for alternatives and kind, Score for ratings on a five-level legend (`responses/08.json`) |
| Structured state (F3) | yes. State is an object with rules, question and a words list with w-IDs; the list is one joined string (`responses/01.json:8`) |
| Batching (F4) | yes. Kind, yes, when, note, scale and one question per word share one request; the second request needs the first (`responses/02.json:8`) |
| No invented values (F6) | yes. Jev judges or picks among supplied options; the date path was not captured, so its candidate years are unseen (`files/ask.js:81`) |
| Evidence recorded evenly (F10) | n.a.. One question text is judged with no per-answer evidence (`responses/01.json`) |
| Choice order handled (F13) | n.a.. Always n.a. for a low Choice (`files/ask.js:253`) |
| Size limits respected (F14) | yes. The question box stops at 400 characters, the pasted notes at 4,000, each choice at 80 (`files/index.html:60`, `files/ask.js:22`) |
| Sample size adequate (F15) | n.a.. The site claims no results |
| Independent labels (F16) | n.a.. The site claims no results |
| Held-out result (F17) | n.a.. The site claims no results |
| Fair baseline (F18) | n.a.. The site claims no results |
| Typed answers read directly (F19) | yes. The page reads the noul value, choice probabilities and score legend (`files/ask.js:86-89`) |

</details>

## Scores

- Execution 1 of 3: the main decision, the visitor's own question, goes to Jev as one raw Noul or Choice with no standard, so F1 fails there, though the word, kind and scale questions are atomic, typed and batched (F1, F8, F9, F11, F21).
- Fit 2 of 3: the primitives fit and one request carries every independent question, but the top answer routes at any probability where confidence should gate (F11).
- Coverage 3 of 3: the page promises to pick, confirm, rate or date a question and each path exists, with the answer, the probabilities and the Jev replies shown (`files/ask.js:81`, `files/ask.js:137`).
- Evidence n.a.: the site claims no results.

## Why this verdict

Rework it (2): F1 fails on the main decision, since the visitor's raw question, like the site's own "Is a hot dog a sandwich?", goes to Jev as one Noul or Choice with no standard, and that gives Execution 1. Without that, F8, F9, F11 and F21 would still cap it at 3. The kind, word and scale questions are atomic, typed and batched, and the page shows every reply, so the build is sound where the site controls the wording. Borderline: whether pass-through of the visitor's wording counts as the site's own F1 failure; a reading as a client would make it 3.

<details>
<summary><b>Files read (18)</b></summary>

- files/ask.js -- read
- files/index.html -- read
- files/api-recent.json -- read
- summary.md -- read
- responses/01.json -- read
- responses/02.json -- read
- responses/03.json -- read
- responses/04.json -- read
- responses/05.json -- read
- responses/06.json -- read
- responses/07.json -- read
- responses/08.json -- read
- responses/09.json -- read
- responses/10.json -- read
- responses/11.json -- read
- responses/12.json -- read
- responses/13.json -- read
- responses/14.json -- read

</details>
