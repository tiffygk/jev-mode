# Jevaluate rubric

Facts first, scores second. The rules behind each fact, with their sources, are in `jev-rules.md`. Two raters who find the same facts must reach the same scores; that's what the anchors are for. When two ratings of the same project disagree on a score, rewrite that anchor more concretely.

## Facts (yes / no / n.a., each with evidence)

**Core principles**
- F1 **Atomic questions:** each question asks about one property. It fails if a question joins two judgments ("relevant *and* recent") or asks something broad ("is this good?", "analyze this").
- F2 **The right primitive:** Noul for yes/no, Choice for one of several named options, Score for an ordered scale described in words. It fails if, for example, a Noul is used for a degree, or a Score has bare numbers as its levels.
- F3 **Structured state:** the state is JSON with named fields, items carry IDs, and questions point at paths (`` `ticket.body` ``). A plain string passes when the use case is a single piece of text (S1). It fails when several distinct parts are packed into one string. (S1, S5)
- F4 **Batching:** independent questions over the same state go in one request, and datasets use the inverted request (criteria in the state, one row per question) or batches. It fails if it sends questions one at a time in a loop.
- F5 **Thresholds in code:** cut-offs are constants or config in code. It fails if they're in prompt prose, left to the LLM, or missing.
- F6 **No invented values:** counting, arithmetic and date comparison happen in code; Jev only picks among supplied options. It fails if Jev is asked to count, compute, or produce values.
- F7 **Measured in the workflow:** accuracy, cost or latency is measured on the project's own task. It fails if there are no numbers, or only anecdotes.

**Question and state design**
- F8 **Options cover every case without overlapping:** every Choice's options are mutually exclusive and cover every realistic case (or use independent Nouls when answers can co-occur).
- F9 **An "unclear" or "other" option, where needed,** worded differently from anything in the state. It's needed when a Choice's options don't cover every case; n.a. when every Choice already does. If the Choice wording is in the fetched files, read it: unknown isn't allowed.
- F10 **Evidence recorded evenly:** the state doesn't list far more detail for one answer than for the others, and doesn't include conclusions ("likely fraud") as facts. n.a. when the state holds no per-answer evidence (a single object being judged).
- F11 **Confidence drives action:** probabilities or confidence gate what the code does (act / review / escalate), rather than the top answer being taken blindly.

**Execution and operations**
- F12 **The model is pinned to a versioned ID** from the models page (`jev-X.Y.Z`), not an alias, wherever thresholds were tuned.
- F13 **Choice order is handled:** high-stakes Choices are averaged over option orders, or the order is randomized per item. High-stakes: the answer can block, veto or route something, or change what a user sees, without review. n.a. if no Choice is high-stakes; no if one is and its order isn't handled. Never "partial".
- F14 **Size limits are respected:** state plus all questions ≤ 64k tokens; state plus the longest question ≤ 32k. Yes needs a guard that trims or stops above the limit, or a reported maximum size under it. "Small by construction" or logged usage alone is unverified, which counts as n.a.
- F20 **Values from code are fields, not templates:** schemas, rows and values from code are passed as JSON fields; they aren't spliced into question strings. It fails if any text taken from the data (a question, a row, a snippet), however short, is inserted into a question string by replace, format or string interpolation; cite the line. Fixed labels the builder wrote are fine. (Q2)
- F21 **No instructions in the state:** the state holds content, not directions to the model. Source text spliced into questions counts once, under F20. (S3)
- F22 **Untrusted text is treated as data:** user input, web pages or text from images in the state is flagged or tested for steering. Judge the project's own Jev calls. Checks the project runs on other people's content, and eval or corpus scripts, don't count. It fails if text a user or an input file supplied reaches the state or questions with no flag and no steering test. (S7)
- F23 **Non-English content is handled:** tested, or translated alongside, where accuracy matters. n.a. only when inputs are English by design; cite where that's stated. Translating the tool's own display text doesn't count. (S6)
- F19 **Typed answers are read directly:** the decision reads the typed field (`noul`, `choice`, `score`, probabilities). It fails if Jev (or an LLM standing in for it) is asked for free-text reasoning that code then string-matches.

**Evidence behind claims** (applies only if the project claims results)
- F15 The sample size is stated and adequate for the claim (zero errors in n supports a rate of at most about 3/n).
- F16 The labels are independent of the builder (an LLM panel or blind human labels, not the builder's own judgment), or that's disclosed.
- F17 The result is on a held-out set: the reported numbers weren't used to choose any threshold or wording. A threshold swept on the same sample as the headline number fails.
- F18 The baseline is fair (the same data, and a reasonable LLM or rules alternative).

## Dimensions (0-3; name the anchor you used)

**Jev execution** (F1-F6, F8-F11, F19-F22). F12, F14 and F23 are fix-only: a no goes into the fixes but doesn't move a score. A failed F20-F22 doesn't lower this score either; it caps the verdict at 3.
- 3: F1-F6 all yes, and F8-F11 yes wherever they apply.
- 2: Exactly one of F1-F6 is no, and it affects only one of several similar questions, not the main decision (for example, one compound question among many good ones).
- 1: Two or more of F1-F6 are no, or F1 or F19 fails for the main decision.
- 0: Jev is used like an LLM prompt (one broad question, prose in, top answer out), or not called.

**Fit of Jev's features** (does it use the *right* ones? Using fewer, well, beats using all of them)
- 3: Each decision uses the primitive that fits it; confidence is used wherever an action depends on it; parallel questions are used wherever questions share a state.
- 2: Exactly one mismatch (for example, the top answer taken where confidence should gate, or a failed F13).
- 1: Two or more mismatches, or a key feature ignored where the task needs it.
- 0: Jev isn't needed for this task at all (a regex or plain code would do), or its output isn't used.

**Coverage** (of the original if it's a remix; otherwise of its own stated goal)
Count the original's (or goal's) listed decisions or steps from phase 4.
- 3: 80% or more covered, or every omission explained.
- 2: 50 to 79% covered.
- 1: Under 50% covered, presented as the whole.
- 0: The stated goal isn't addressed by what the code does.

**Evidence** (F7, F15-F18; score "n.a." if it claims nothing)
- 3: Measured on independent labels, held out, with a stated sample and a fair baseline.
- 2: Measured with one weakness (small sample, builder's own labels, or no held-out set), disclosed.
- 1: Numbers given without method, or tuned and tested on the same data.
- 0: Claims results with no measurement shown.
- Only latency or cost measured, no accuracy on labels: score 1, and say so. F15-F18 are n.a.

## Build stages and the loop
Mark each build stage the project actually implements, using these four labels exactly: `data-prep` (retrieve, filter, serialize, IDs), `question-state` (question and state design), `execution` (batching, the inverted request, pinning, caching), `decision` (thresholds, combining answers, routing, acting).

The improvement loop: **evaluate** on labels, then **calibrate** (change the numbers: thresholds, weights, confidence mapping) and/or **revise** (change the questions, state or data). Record `closes_loop`: none, calibrates, revises, or both.

## Verdict anchors (not an average; rubric 2026-09-28)
- **5 Learn from it:** Execution 3, Fit 3, Evidence 3, and closes the loop.
- **4 Use it:** Execution and Fit at least 2, no fatal flaw; evidence may be missing.
- **3 Use with a fix:** One fixable flaw (a single failed fact from F1-F6, F8-F11 or F19-F22) caps it here.
- **2 Rework it:** Execution 1 or 0, or a fatal flaw: F1 fails on the main decision, F6 fails (Jev computes values), or confidence is ignored on a high-stakes action.
- **1 Jev in name only:** Jev isn't called, or its output doesn't drive any decision.
- **Can't rate yet** (`cant-rate` in the rating file): depth is readme-only, or the Jev code isn't public.
- A project with misleading claims (Evidence 0 while claiming results) can't score above 3.
