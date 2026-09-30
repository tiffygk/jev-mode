# Jev rules

The single source of rules for building with Jev, each citing its public source. Other files (the rubric, the fix catalog, and other skills) point here instead of keeping their own copies. Docs: `https://docs.typesafe.ai/<page>.md`. When a source is re-read in full, add its new rules and update its date.

## Sources and when they were last checked
| Source | Last checked | How it was read |
|---|---|---|
| `concepts/state` | 2026-09-27 | full prose |
| `primitives/advanced` | 2026-09-27 | full prose |
| `model-jaggedness/jev-1.13` | 2026-09-27 | sections: literal reading, indirection, large state, adversarial content |
| `concepts/how-to-build-with-system-one` | 2026-09-24 | design section |
| `models` | 2026-09-24 | full |
| Cookbooks (18) | 2026-09-24 | script extracts, not full reads |
| Launch post, evals.typesafe.ai | 2026-09-24 | sentences on training, calibration and evals |

## State
- S1 **An object with descriptive field names** is the default; **a plain string is fine** when the use case is one piece of text. An array suits a sequence of messages or records. (`concepts/state`)
- S2 **Group related information** in one state when the decision compares its parts. (`concepts/state`)
- S3 **Content in the state; judgments in the questions.** No instructions buried in the state, no source text stuffed into questions. (`concepts/state`: "Separate content from questions")
- S4 **Send only what the questions need.** Irrelevant detail lowers accuracy and hides which input caused a wrong answer. Filter in code, or with a relevance Noul. (`model-jaggedness/jev-1.13`; classifying RAG passages cookbook)
- S5 **An ID on every item,** with questions pointing at backticked paths (`` `people[0].cap.text` ``). (How to build; line-by-line search cookbook)
- S6 **Text only, and English is where accuracy is best.** Images, audio and video must be described in text first. Test non-English content, or add a translation beside it. (`concepts/state`, `models`)
- S7 **State is data, not instructions,** and Jev doesn't treat it as hostile. Flag or test untrusted text (user input, web pages, text inside images) that could steer an answer. (`model-jaggedness/jev-1.13`)
- S8 **Observations, not conclusions:** state facts and unknowns; never write the answer into the state. (case-study finding; related to S3)
- S9 **Record the evidence for each answer evenly;** uneven detail acts as a hidden weight. (case-study finding)
- S10 **Size:** state plus all questions ≤ 64k tokens; state plus the longest question ≤ 32k. (`models`)

## Questions
- Q1 **Atomic:** one property per question; break broad judgments down. ("Decompose the questions," which How to build calls "probably the most important concept")
- Q2 **Structure over templates:** instructions and criteria can be JSON objects or arrays. Pass schemas, taxonomies and database rows as JSON; don't splice values from code into strings. (`primitives/advanced`; How to build)
- Q3 **Choice options are exclusive and cover every case;** describe the boundaries between close options (what each option covers, and what it isn't for). (`primitives/advanced`)
- Q4 **Deep or large option sets:** walk a taxonomy with one Choice per level (a Choice caps at 255 options). (`primitives/advanced`; hierarchical classification cookbook)
- Q5 **Say exactly what you mean:** Jev reads scoping words, negations and implied conditions at face value. Avoid double negatives and questions that need several hops. (`model-jaggedness/jev-1.13`)
- Q6 **Pair a Choice with an "is there an answer at all?" Noul** when none of the options may apply. (line-by-line search and skill suggestion cookbooks)

- Q7 **Describe Score levels as situations,** with no numbers in the level text; each level is judged on its own and never sees its number or its neighbors. (`primitives/score`)
- Q8 **Phrase Nouls so "yes" means the thing you're checking for,** with criteria pointing the same way as the instruction. (consistency Noul cookbook)
- Q9 **Companion Nouls can explain why a Score is ambiguous** (for example, same name, same maker, same style). (entity alignment cookbook)
- Q10 **Don't word an option the way the state is worded;** an option that echoes a state line pulls probability toward itself. (measured case study, 2026-09-27)
- Q11 **Decide whether you want a committed guess.** "What is…" invites caution, "make your best guess…" invites commitment, and the choice moves base rates a lot. Keep the wording fixed once thresholds are tuned. (measured case study, 2026-09-27)
- Q12 **When close options compete in a taxonomy, keep several paths** (beam search) instead of committing greedily to one. (hierarchical classification cookbook)

## Execution and decisions
- E1 **Ask many independent questions in one request;** for datasets, put the criteria in the state and send each row as a question. (How to build; parallel questions cookbook)
- E2 **Thresholds live in code** and scale with the cost of a wrong action; route on confidence. (`confidence`)
- E3 **Pin the versioned model** from the models page when thresholds are tuned; log the `model` field each response returns. (`models`)
- E4 **Average high-stakes Choices over option orders;** Choice is the least stable question type. (consistency Choice cookbook: answers flip between runs; own testing, 2026-09-28: reversing a Choice's options moved the top answer from 0.67 to 0.85)
- E5 **Counting, arithmetic and dates happen in code;** Jev picks among candidates that code supplies. (`model-jaggedness/jev-1.13`; date and pre-parsed extraction cookbooks)
- E6 **Keep an uncertain middle band** (for example 0.30 to 0.70) that goes to review instead of one cutoff; answers drift slightly between runs. (consistency Noul cookbook)
- E7 **Derive thresholds from the probabilities you actually observe** on your data, not from round numbers. (structure recovery cookbook)
- E8 **A combined answer is only as confident as its weakest part.** (date extraction and function calling cookbooks)
- E9 **When unsure of a fine label, fall back to the coarser one** instead of guessing. (classification using confidence cookbook)
- E10 **Use a second request only when it needs the first one's output** (for example, shortlist, then recheck the top few). (structure recovery and skill suggestion cookbooks)
- E11 **Cascade:** a cheap model first, Jev to verify each field, and the strong model only where Jev flags a problem. (SDE cascade cookbook)
- E12 **Retrieve, then re-rank:** fast search for a shortlist, then Jev to score each candidate. (re-ranking cookbook)
- E13 **Throughput is limited by tokens, not requests** (published: 250,000 tokens a second, 1,200 requests a minute; limits can change). Keep concurrency modest (6 to 8 workers) and batch by total tokens. (`models`; entity alignment cookbook)
- E14 **Cache calls during development** so reruns cost nothing. (every cookbook)
- E15 **For the inverted request, check each new dataset** against the standard method on a small sample. A row's position among the questions doesn't affect its answer. (Recommended practice; no rating fact checks it.)

## Evaluation
- V1 **Pick the goal first** (precision, recall, F1 or F-beta, precision or recall at k) from what a false yes and a miss each cost; it sets the threshold, the audit and the order of diagnosis.
- V2 **Build your own evals on your own task;** don't rely on public benchmarks. (TypeSafe launch post)
- V3 **Labels:** a panel of strong LLMs is silver, not gold. TypeSafe's workflow evals average two frontier models run through the adapter. Add a small human audit set, and report agreement among panelists. (evals.typesafe.ai; `system-one-adapter-python`)
- V4 **Tune on dev, report on held-out,** and cap the variants tried per round. Keep a revision only if held-out error falls. (autoresearch cookbook)
- V5 **Audit what was returned and what wasn't:** the top, the boundary, near misses, and a random slice from the deep bottom, reviewed blind. Zero misses in n means the miss rate can still be up to about 3/n.
- V6 **Report error bars:** Wilson intervals for rates; count labels rather than taking a percentage of the data.
- V7 **Find what drives an answer by taking the state apart:** remove or flip one field at a time and rerun; anything within the run-to-run noise counts as no effect. (measured case study, 2026-09-27)
- V8 **Screen draft questions before running them** with Nouls about the question itself: answerable from the state? one meaning? applies to most items? varies across them? (autoresearch cookbook, next steps)
