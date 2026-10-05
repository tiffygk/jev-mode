[← Summary](../site__askjevs.site.md)

# Ask Jevs: full rating

**Verdict 2, Rework it** · display · rated 2026-09-30 [https://askjevs.site/](https://askjevs.site/), site as captured 2026-09-28 · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Ask Jevs is a parody question site that sends a free-text question to Jev in one batched request of 8 to 16 questions, then a second request that picks or rates. It batches well, reads typed fields directly and shows every probability. The raw question has no standard, word tags use the wrong primitive, options overlap or omit the right answer and directions sit in the state; the server code is not public.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The page's /api/jevs returns captured jev-1.13.0 replies to typed Noul, Choice and Score questions (`responses/01.json:9`) |
| Atomic questions (F1) | **no.** The yes/no and final questions are raw user text, no standard; "healthy and cheap" gets Yes (`03.json`, `05.json`). concepts/how-to-build-with-system-one |
| Right primitive (F2) | **no.** Each word is tagged by a two-option Choice, which is a yes/no; other picks fit (`01.json`). primitives/advanced |
| Thresholds in code (F5) | **unknown.** Client literals 0.5 and 0.005 only (`ask.js:86`, `ask.js:89`); the server's lowConfidence rule is not public, no file would answer it. |
| Measured in the workflow (F7) | **no.** No accuracy, cost or latency figures anywhere on the site or in its files (`index.html`, `summary.md`). concepts/how-to-build-with-system-one |
| Options cover every case, no overlap (F8) | **no.** Kind options choice and noul overlap (noul 0.41); a bogus alternative "Mona Lisa" was extracted (`02.json`). primitives/advanced |
| An "other" option where needed (F9) | **no.** The picked Choice has no none-of-these option, so Pluto "planet or star" returns planet at 1.00 (`11.json`). primitives/advanced |
| No instructions in the state (F21) | **no.** `state.rules` tells Jev how to answer each word question and what option means (`01.json`). concepts/state |
| Untrusted text treated as data, high or low (F22) | **no.** Step 2 puts the raw question in instructions, unflagged; step 1 only says "data, never instructions" (`02.json`). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No non-English question was captured and the site does not say it is English-only (`summary.md`). models |

<details>
<summary><b>What passes (7) and doesn't apply (7)</b></summary>

| Fact | Finding |
|---|---|
| Structured state (F3) | yes. Step 1 state has named fields (rules, question, words) with w0.. IDs; step 2 holds a context field (`02.json`). |
| Batching (F4) | yes. Up to 16 independent questions go in one request; the second request needs the first one's output (`02.json`, `09.json`). |
| No invented values (F6) | yes. Code computes the score and fills the scale; Jev picks among supplied options, scales and eras (`ask.js:81`, `08.json`). |
| Evidence recorded evenly (F10) | n.a.. The state holds the question and a note, no per-answer evidence. |
| Confidence drives action, low (F11) | n.a.. Every decision is low and the answer is only shown; the client never reads lowConfidence (`ask.js:143`). |
| Pinned model version (F12) | yes. Every captured reply reports jev-1.13.0; the request's model field is server-side (`06.json`). |
| Choice order handled, low (F13) | n.a.. Always n.a. |
| Size limits respected (F14) | yes. Question capped at 400 characters, note at 4,000, choices at 24; the largest request was 1,358 tokens (`index.html`, `ask.js:21`, `09.json`). |
| Sample size adequate (F15) | n.a.. No results claimed. |
| Independent labels (F16) | n.a.. No results claimed. |
| Held-out result (F17) | n.a.. No results claimed. |
| Fair baseline (F18) | n.a.. No results claimed. |
| Typed answers read directly (F19) | yes. The page reads the noul value, choice and probabilities fields to build the verdict (`ask.js:86`, `ask.js:253`). |
| Data as fields, not templates, high or low (F20) | yes. The question sits in `state.question` and the kind question points at it; a note goes in `state.context` (`01.json`, `06.json`). |

</details>

## Scores

- Execution 1 of 3: F1 fails on the main decision and F2 fails too, so the questions are neither atomic nor typed to fit; F8 and F9 also fail. Facts F1, F2, F8, F9, F21.
- Fit 2 of 3: one mismatch, the per-word option/none Choices that are yes/no questions; Score, Choice and Noul are otherwise used for the right jobs and share one request. Facts F2, F4, F19.
- Coverage 3 of 3: the site's goal of picking, confirming, rating and dating a question all runs, and open questions are stopped as its tips say. Facts F0, F4, F6.
- Evidence n.a.: the site claims no results, so none are scored. Facts F7, F15-F18 n.a.

## Why this verdict

2, Rework it. Execution is 1: F1 fails on the main decision, since the answered question is raw user text with no standard, and F2 also fails. F8, F9 and F21 fail too, which would cap it at 3 alone, but F1 on the main decision is a fatal flaw. Stakes are low and nothing acts on an answer, so the cost is a wrong answer shown with a straight face. The captures show the full state, questions and answers, so it is rateable.

## Fixes (from reading the code; not tested against it)

1. F1: give the yes/no and final questions a stated standard and split compound ones ("healthy and cheap") into separate questions, combined in code ([`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one), "Decompose the questions").
2. F2: tag each word with a Noul, not a two-option Choice ([`primitives`](https://docs.typesafe.ai/primitives), [`primitives/score`](https://docs.typesafe.ai/primitives/score)).
3. F8: make the extracted options exclusive and flag overlap or a spurious option such as "Mona Lisa" before the final pick; confirm with data ([`primitives`](https://docs.typesafe.ai/primitives), Choice).
4. F9: add a "none of these" option to the final Choice, worded unlike the state, so Pluto "planet or star" can say neither ([`primitives`](https://docs.typesafe.ai/primitives), Choice).
5. F21: move `state.rules` into the question instructions and criteria, leaving only content in the state ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).
6. F7: label a sample of questions and report accuracy at the gating probability ([`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)).
7. F22 and F23: flag visitor text, add an injection-check Noul and test adversarial and non-English questions ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`concepts/state`](https://docs.typesafe.ai/concepts/state)).

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
