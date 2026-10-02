[← Summary](../altryne__jevify.md)

# Jevify: full rating

**Verdict 4, Use it** · agent tool · rated 2026-09-30 at [`11f36f8`](https://github.com/altryne/jevify/tree/11f36f8d54) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Jevify is an installable agent skill that teaches an agent to hand bulk semantic judgments to Jev, with a standard-library scanner that sends text chunks to hosted Jev as Score questions and returns a ranked reading shortlist to the agent.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The bundled client posts JSON requests to api.typesafe.ai /v1/systemone, and scan.py sends Score questions through it. ([`scripts/jev_client.py:141`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/jev_client.py#L141)) |
| Measured in the workflow (F7) | **no.** Only latency and token counts on 24 synthetic records, with no accuracy on any labeled set. ([`references/validation-2026-09-21.md:25`](https://github.com/altryne/jevify/blob/11f36f8d54/references/validation-2026-09-21.md#L25)). docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Untrusted text treated as data, high or low (F22) | **no.** A scope line tells Jev to treat item instructions as content, but no test runs it. ([`scripts/scan.py:80`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L80)). docs.typesafe.ai/cookbooks/classifying_rag_passages |
| Non-English handled (F23) | **no.** Unicode offsets are tested, but no judgment test uses non-English text and English-only is unstated. ([`scripts/test_scan.py:19`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/test_scan.py#L19)). docs.typesafe.ai/concepts/state |

<details>
<summary><b>What passes (13) and doesn't apply (7)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each chunk gets one Score on its usefulness as evidence for `query`, with the target path spelled out. ([`scripts/scan.py:78`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L78)) |
| Right primitive (F2) | yes. Evidence usefulness is a Score with four situations in words; refund and handler examples use Noul and Choice. ([`scripts/scan.py:16`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L16)) |
| Structured state (F3) | yes. State is an object holding `query` and an `items` array; questions point at `items[i].text`. ([`scripts/scan.py:73`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L73)) |
| Batching (F4) | yes. Up to 8 chunk questions share one request, and the client sends requests concurrently. ([`scripts/scan.py:92`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L92)) |
| Thresholds in code (F5) | n.a.. The scanner ranks by score and takes the top N; no cut-off acts, and thresholds appear only in prose. |
| No invented values (F6) | yes. Code counts, sizes and keeps source offsets; Jev only scores supplied text. ([`scripts/scan.py:24`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L24)) |
| Options cover every case, no overlap (F8) | yes. Department Choice has `not_for` boundaries between teams; span Choice offers not_stated and ambiguous. ([`assets/example-requests.json:11`](https://github.com/altryne/jevify/blob/11f36f8d54/assets/example-requests.json#L11)) |
| An "other" option where needed (F9) | yes. Department Choice carries other and insufficient_context; span Choice carries not_stated and ambiguous. ([`assets/example-requests.json:27`](https://github.com/altryne/jevify/blob/11f36f8d54/assets/example-requests.json#L27)) |
| Evidence recorded evenly (F10) | yes. State holds the query and neutral chunks with no conclusions or per-answer detail. ([`scripts/scan.py:73`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L73)) |
| Confidence drives action, low (F11) | n.a.. Every decision is low: the scanner only returns a ranked shortlist for the agent to read. |
| Pinned model version (F12) | yes. The client and every request pack pin `jev-1.13.0`, and docs say to pin when caching. ([`scripts/jev_client.py:33`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/jev_client.py#L33)) |
| Choice order handled, low (F13) | n.a.. Always n.a.; the scanner has no Choice. |
| Size limits respected (F14) | yes. The scanner caps each request at 24,000 bytes and the runner flags bodies over the documented token limits. ([`scripts/scan.py:15`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L15)) |
| Sample size adequate (F15) | n.a.. No accuracy result is claimed; the validation note calls its runs smoke tests. |
| Independent labels (F16) | n.a.. No results claimed, so no labels. |
| Held-out result (F17) | n.a.. No results claimed; the validation note says its rerun was tuned, not held-out. |
| Fair baseline (F18) | n.a.. No results claimed; the "faster and cheaper" line is stated as an assumption. |
| Typed answers read directly (F19) | yes. Code reads `answer["score"]`, checks type and 0-3 range, and treats anything else as unjudged. ([`scripts/scan.py:126`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L126)) |
| Data as fields, not templates, high or low (F20) | yes. Chunk text sits in `items[i].text`; the question holds only a path. ([`scripts/scan.py:78`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L78)) |
| No instructions in the state (F21) | yes. State is the query and chunk text; the scope guard lives in the question. ([`scripts/scan.py:79`](https://github.com/altryne/jevify/blob/11f36f8d54/scripts/scan.py#L79)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded and batched, and the Choice templates carry other options, from F1-F4, F6, F8-F10 and F19.
- Fit 3 of 3: Score fits the evidence ranking, the Noul and Choice templates fit their jobs, and the questions share requests; no action depends on confidence, from F2, F4 and F11.
- Coverage 3 of 3: the scanner, client, runner, question packs and workflow guidance deliver what the README lists, and its limits are stated, from F5 and F14.
- Evidence n.a.: the project claims no results of its own; its validation note calls the runs smoke tests and tuned reruns, from F7 and F15-F18.

## Why this verdict

No capping failure holds: F1-F6, F8-F10, F19 and F21 pass or are n.a., and Fit is 3, so the verdict is 4, not 3. It is not a 5 because nothing was measured for accuracy, so there is no held-out result and the loop closes only on the author's own synthetic cases. The F1 call is borderline: the single Score is one property, but the shipped example queries name several topics, and that would fail F1 on the main decision and send it to 2.

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
