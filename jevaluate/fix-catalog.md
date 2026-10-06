# Jevaluate fix catalog

Each design fix answers one failed fact. Cite the fact, give the remedy, and point to the public source that shows it. Docs: `https://docs.typesafe.ai/<page>.md`. A fix that can only be confirmed with data is marked **(confirm with data)**.

| Failed fact | Remedy | Source |
|---|---|---|
| F0 no traced call to hosted Jev | Call Jev through the SDK or `api.typesafe.ai` (or a gateway's `typesafe/jev-...` ID) and let its typed answers drive the decision; or, for a model that imitates Jev, say plainly in the README that it doesn't call Jev | `introduction/quickstart`, `sdk` |
| F1 compound or broad question | Split it into atomic questions, one property each; combine the answers in code | `concepts/how-to-build-with-system-one` ("Decompose the questions") |
| F2 wrong primitive | Noul for yes/no, Choice for named options, Score for a described scale; describe Score levels as situations, not numbers | `primitives`, `primitives/score` |
| F3 unstructured state | Put the input into JSON fields with IDs; point questions at backticked paths | `concepts/state`, `concepts/how-to-build-with-system-one` |
| F4 one question per request | Batch independent questions into one request; for datasets, put the criteria in the state and send each row as a question | `patterns/fan-out`, `cookbooks/parallel_questions` |
| F5 thresholds in prose or missing | Move them into named constants in code; set them from labeled data | `confidence`, `patterns/confidence-routing` |
| F6 Jev counts, computes or produces values | Do the arithmetic and dates in code; let Jev pick among candidates that code supplies | `cookbooks/pre_parsed_value_extraction_cookbook`, `cookbooks/date_extraction_cookbook` |
| F7 nothing measured | Add an evaluation: label a sample (LLM panel or people), report precision and recall at the chosen threshold | `cookbooks/classification_using_confidence`; TypeSafe's workflow evals |
| F8 options overlap or leave cases out | Make the options exclusive and exhaustive, or switch to independent Nouls when answers can co-occur **(confirm with data)** | `primitives` (Choice) |
| F9 no fallback, or an "unclear" option that echoes the state | Add "other" or "unclear" where inputs can fall outside the options; word it differently from the state | `primitives` (Choice) |
| F10 unbalanced evidence, or conclusions in the state | Record the evidence for each answer about equally; state facts and unknowns, not conclusions **(confirm with data: remove one field at a time and rerun)** | `concepts/state` |
| F11 confidence ignored | Gate each action on confidence: act, send for review, or escalate | `confidence`, `patterns/confidence-routing` |
| F12 model not pinned | Pin the versioned ID from the models page; log the `model` field each response returns; retune thresholds after upgrading | `models` |
| F13 Choice order unhandled | Average high-stakes Choices over option orders, or randomize the order per item | `cookbooks/consistency_choice_cookbook` |
| F14 size limits exceeded | Filter the state to relevant fields; split long inputs; keep state plus the longest question under 32k tokens | `models`, `model-jaggedness/jev-1.13` |
| F19 free-text answers string-matched | Ask a typed question (Noul, Choice or Score) and read its typed field and probabilities; never parse prose | `primitives` |
| Measured once, loop not closed (`closes_loop: none`) | After evaluating, calibrate (tune thresholds or weights on labels) and/or revise (rewrite the questions or state for the misses), then re-measure | `confidence`; `cookbooks/autoresearch_feature_discovery` |
| F20 values spliced into question strings (caps the verdict only at `very high` stakes) | Pass schemas, rows and values as JSON fields in the question or the state; put a user's own question in a state field marked as user input and point the question at it | `primitives/advanced` |
| F21 content and judgments mixed | Move the source content into the state and keep only the judgment in the question | `concepts/state` |
| F22 untrusted text not treated as data (caps the verdict only at `very high` stakes) | Flag steering text; add an injection-check Noul; test adversarial inputs before deploying | `model-jaggedness/jev-1.13`; `cookbooks/classifying_rag_passages` |
| F23 non-English content untested | Test on your language, or add an English translation beside the original | `concepts/state` |
| A Choice with a very large or deep option list | Walk a taxonomy, one Choice per level (the cap is 255 options) | `primitives/advanced`; `cookbooks/hierarchical_classification` |
| F15 sample too small for the claim | Report the sample size; zero errors in n supports a rate of at most about 3/n | `cookbooks/classification_using_confidence` |
| F16 builder's own labels | Label with an LLM panel or blind reviewers, or disclose that the builder labeled | `cookbooks/classification_using_confidence` |
| F17 tuned and tested on the same data | Hold out a test set the thresholds and wording never saw | `cookbooks/classification_using_confidence` |
| F18 unfair baseline | Compare on the same data against a reasonable LLM or rules alternative | `cookbooks/consistency_choice_cookbook` |
| G1 a guide's rule contradicts the page it cites | Rewrite the rule to match the page, and quote the page beside it | The page the rule cites |
| G2 a guide's example would fail F1-F6 | Fix the example the way the matching F1-F6 row says; readers copy examples before rules | `concepts/how-to-build-with-system-one` |

When a project has several failed facts, lead with the fix that unblocks the most others. Usually that's F1 (decompose), then F5 (thresholds in code), then F7 (measure).
