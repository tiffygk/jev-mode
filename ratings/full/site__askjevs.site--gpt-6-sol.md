[← Summary](../site__askjevs.site--gpt-6-sol.md)

# askjevs.site: full rating

**Verdict 3, Use with a fix** · display · rated 2026-10-06 [https://askjevs.site/](https://askjevs.site/), site-snapshot-2026-10-05 · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Ask Jevs turns visitor questions into Jev Choice, Noul, and Score answers through its site API and displays the results. It exposes each request, typed answer, and probability in an accessible visual trace. Its open question coverage and answer reliability are limited by the offered choices and unverified server logic.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Captured site API responses contain System One requests and Jev typed answers (`responses/06.json:8`). |
| Atomic questions (F1) | **no.** “Is coffee healthy and cheap?” asks two properties in one Noul (`responses/03.json:3`). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| No invented values (F6) | **unknown.** Date and arithmetic server logic is absent; no file would answer it (`files/ask.js:245`; `files/api-recent.json:1`). |
| Measured in the workflow (F7) | **no.** No project evaluation reports accuracy, cost or latency on labeled questions (`files/index.html:103`). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Options cover every case, no overlap (F8) | **no.** A tomato is both a fruit and a berry, yet those appear as rival options (`responses/09.json:8`). https://docs.typesafe.ai/primitives/advanced.md |
| An "other" option where needed (F9) | **no.** “Planet or star?” omits dwarf planet and offers no none option (`responses/11.json:8`). https://docs.typesafe.ai/primitives/advanced.md |
| Data as fields, not templates, low (F20) | **no.** Visitor question is copied into Noul and Choice instructions (`responses/03.json:8`; `responses/09.json:8`). https://docs.typesafe.ai/concepts/state.md |
| No instructions in the state (F21) | **no.** First-request state includes rules telling Jev how to classify words and treat input (`responses/02.json:8`). https://docs.typesafe.ai/concepts/state.md |
| Untrusted text treated as data, low (F22) | **no.** Visitor text reaches question instructions, with no visible adversarial test (`responses/03.json:8`). https://docs.typesafe.ai/model-jaggedness/jev-1.13.md |
| Non-English handled (F23) | **no.** Public question input has no language restriction or shown multilingual test (`files/index.html:56`; `files/index.html:103`). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (5) and doesn't apply (9)</b></summary>

| Fact | Finding |
|---|---|
| Right primitive (F2) | yes. Captures use Noul for yes/no, Choice for alternatives, and Score for difficulty (`responses/03.json:8`; `responses/09.json:8`; `responses/08.json:8`). |
| Structured state (F3) | yes. Requests use named JSON fields for rules, question, word list or context (`responses/02.json:8`; `responses/06.json:8`). |
| Batching (F4) | yes. Independent kind, yes, when, note, scale and word questions share the first request (`responses/02.json:8`). |
| Thresholds in code (F5) | n.a.. The display takes no action based on a probability cutoff (`files/ask.js:240`). |
| Evidence recorded evenly (F10) | n.a.. The judged input is one visitor question, with no per-answer evidence (`responses/10.json:8`). |
| Confidence drives action, low (F11) | n.a.. Answers are displayed to the asker, with no automatic action (`files/ask.js:240`). |
| Pinned model version (F12) | n.a.. No threshold is shown as tuned; captures report jev-1.13.0 (`responses/06.json:8`). |
| Choice order handled, low (F13) | n.a.. The rubric always excludes low-stakes Choice decisions (`files/ask.js:240`). |
| Size limits respected (F14) | yes. Form limits questions to 400 characters, context to 4,000, and choices to 24 of 80 (`files/index.html:56`; `files/index.html:78`; `files/ask.js:21`). |
| Sample size adequate (F15) | n.a.. The site makes no numerical accuracy claim (`files/index.html:103`). |
| Independent labels (F16) | n.a.. The site makes no evaluation claim requiring labels (`files/index.html:103`). |
| Held-out result (F17) | n.a.. No held-out result is reported (`files/index.html:103`). |
| Fair baseline (F18) | n.a.. No comparative result is reported (`files/index.html:103`). |
| Typed answers read directly (F19) | yes. Rendering reads answer.choice, answer.probabilities, answer.noul and answer.score (`files/ask.js:235`; `files/ask.js:253`). |

</details>

## Scores

- Execution 2 of 3: one compound Noul among otherwise typed, batched questions; overlapping and incomplete Choice options remain, F1 Atomic questions, F8 Options cover every case, F9 An "other" option.
- Fit 3 of 3: Jev chooses and scores with fitting primitives, parallel first-pass questions, and visible probabilities; F2 Right primitive, F4 Batching, F19 Typed answers read directly.
- Coverage 3 of 3: yes/no, choice, score and time questions are supported, while the site explains unsupported open questions; F2 Right primitive and F19 Typed answers read directly.
- Evidence n.a.: the site claims no measured performance result, F15 Sample size adequate.

## Why this verdict

Use with a fix (3). The site shows real typed Jev answers and asks independent first-pass questions together. A compound yes/no question and overlapping or incomplete Choice sets cap the verdict at 3. The current evidence does not show that the server’s date and confidence logic is fully guarded, and the answer examples do not establish accuracy.

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
