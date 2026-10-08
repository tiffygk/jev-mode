[← Summary](../altryne__jevify--gpt-6-sol.md)

# jevify: full rating

**Verdict 3, Use with a fix** · agent tool · rated 2026-10-06 at [`11f36f8`](https://github.com/altryne/jevify/tree/11f36f8d548cf5020a20e5eb548f21c3d7181a17) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jevify gives agents a Jev powered relevance scan and instructions for using Jev during their work. Its scanner sends independent Scores over bounded source windows and returns source linked excerpts with audit samples. The result still depends on the agent reopening evidence, and the repo has only small synthetic validation of behavior.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Client posts native questions to the TypeSafe System One endpoint ([`scripts/jev_client.py:141`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/jev_client.py#L141)). |
| Size limits respected (F14) | **no.** Custom packs can bypass dry-run and reach live `ask_many` without its estimated-size check ([`scripts/run_cases.py:100-116`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/run_cases.py#L100-L116)). [Models](https://docs.typesafe.ai/models). |
| Held-out result (F17) | **no.** Revised questions were rerun on tuning examples; fresh examples cover the same task ([`references/validation-2026-09-21.md:23-24`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L23-L24)). [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one). |
| Fair baseline (F18) | **no.** Own validation reports Jev runs without a matched agent or direct-reading baseline ([`references/validation-2026-09-21.md:20-27`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L20-L27); [`references/evaluation.md:9-20`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/evaluation.md#L9-L20)). [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one). |
| No instructions in the state (F21) | **no.** Runnable message pack places “Questions target user messages separately from assistant claims” in state context ([`assets/message-signals.json:5`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/message-signals.json#L5)). [State](https://docs.typesafe.ai/concepts/state). |
| Non-English handled (F23) | **no.** The scanner accepts arbitrary UTF-8 documents, but recorded checks use English synthetic text only ([`scripts/scan.py:34-64`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L34-L64); [`references/validation-2026-09-21.md:20-25`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L20-L25)). [State](https://docs.typesafe.ai/concepts/state). |

<details>
<summary><b>What passes (14) and doesn't apply (4)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Scanner asks one evidence-usefulness judgment per window ([`scripts/scan.py:74-82`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L74-L82)). |
| Right primitive (F2) | yes. Relevance uses described Score levels; examples use Choice and Noul for bounded selections and conditions ([`scripts/scan.py:16-21`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L16-L21); [`assets/example-requests.json:10-44`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L10-L44)). |
| Structured state (F3) | yes. Query and indexed text items are named fields; unit IDs key the corresponding questions ([`scripts/scan.py:52-58`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L52-L58); [`scripts/scan.py:73-82`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L73-L82)). |
| Batching (F4) | yes. Scanner groups up to eight independent item questions over shared query and state ([`scripts/scan.py:92-105`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L92-L105)). |
| Thresholds in code (F5) | n.a.. Scanner ranks results without a probability cut-off ([`scripts/scan.py:149-152`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L149-L152)). |
| No invented values (F6) | yes. Scanner retrieves original text by source offsets; Jev only scores usefulness ([`scripts/scan.py:52-58`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L52-L58); [`scripts/scan.py:136-152`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L136-L152)). |
| Measured in the workflow (F7) | yes. Synthetic scanner run reports 24 records, 0.40 seconds and 5,363 input tokens ([`references/validation-2026-09-21.md:25`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L25)). |
| Options cover every case, no overlap (F8) | yes. Example Choices distinguish primary team or supplied source spans, with other and ambiguity options ([`assets/example-requests.json:11-29`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L11-L29); [`assets/example-requests.json:104-115`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L104-L115)). |
| An other option where needed (F9) | yes. Team Choice has other and insufficient-context; source selection has not-stated and ambiguous ([`assets/example-requests.json:26-29`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L26-L29); [`assets/example-requests.json:111-115`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L111-L115)). |
| Evidence recorded evenly (F10) | yes. Synthetic ticket and candidate examples supply source facts without an answer-labeled evidence field ([`assets/example-requests.json:4-10`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L4-L10); [`assets/example-requests.json:52-66`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L52-L66)). |
| Confidence drives action, low (F11) | n.a.. Scanner returns ranked excerpts and audit samples to the agent ([`scripts/scan.py:231-244`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L231-L244)). |
| Pinned model version (F12) | n.a.. No scanner probability threshold was tuned ([`scripts/scan.py:149-152`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L149-L152)). |
| Choice order handled, low (F13) | n.a.. Rule always excludes low-stakes Choice ([`assets/example-requests.json:11-29`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/assets/example-requests.json#L11-L29)). |
| Sample size adequate (F15) | yes. Validation calls author-written examples smoke tests and makes no accuracy-rate claim ([`references/validation-2026-09-21.md:24`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L24)). |
| Independent labels (F16) | yes. Validation discloses its examples as author-written rather than independent labels ([`references/validation-2026-09-21.md:24`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/references/validation-2026-09-21.md#L24)). |
| Typed answers read directly (F19) | yes. Scanner validates typed Score fields and reads scores and confidence directly ([`scripts/scan.py:117-127`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L117-L127); [`scripts/scan.py:149-166`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L149-L166)). |
| Data as fields, not templates (F20) | yes. Query and source text stay in state; question text contains only an indexed state path ([`scripts/scan.py:73-82`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L73-L82)). |
| Untrusted text treated as data (F22) | yes. Scanner instructions explicitly treat item instructions as source content ([`scripts/scan.py:77-80`](https://github.com/altryne/jevify/blob/11f36f8d548cf5020a20e5eb548f21c3d7181a17/scripts/scan.py#L77-L80)). |

</details>

## Scores

- Execution 3 of 3: scanner questions are atomic, typed, fielded and batched; example Choices cover uncertainty, F1-F6 and F8-F11.
- Fit 3 of 3: Score ranks evidence, independent questions share state, and the agent receives sources for verification, F2, F4 and F11.
- Coverage 3 of 3: runnable scanning plus question packs, agent guidance and product design cover the stated agent assistance goal, F1-F4 and F19.
- Evidence 1 of 3: synthetic live runs report time and token use, while accuracy remains smoke tested without a matched baseline, F7 and F15-F18.

## Why this verdict

The scanner uses Jev well for bounded relevance judgments and preserves pointers for agent verification. A runnable message pack puts a judgment instruction in state, so F21 caps the verdict at 3 instead of 4. Synthetic validation documents execution and a question rewrite, but not held-out task quality against a matched baseline.

<details>
<summary><b>Files read (24)</b></summary>

- README.md -- read
- SKILL.md -- read
- assets/example-requests.json -- read
- assets/hero.svg -- read
- assets/message-signals.json -- read
- assets/question-cases.json -- read
- evals/evals.json -- read
- references/agent-workflows.md -- read
- references/community-discoveries.md -- read
- references/corpus-review.md -- read
- references/evaluation.md -- read
- references/field-notes.md -- read
- references/patterns.md -- read
- references/product-evidence.md -- read
- references/question-design.md -- read
- references/research-protocol.md -- read
- references/running-jev.md -- read
- references/validation-2026-09-21.md -- read
- references/worked-question-pack.md -- read
- scripts/jev_client.py -- read
- scripts/run_cases.py -- read
- scripts/scan.py -- read
- scripts/test_jev_client.py -- read
- scripts/test_scan.py -- read

</details>
