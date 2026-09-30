# Jevaluate rubric

Facts first, scores second. The rules behind each fact, with their sources, are in `../shared/jev-rules.md`; the two rating rules below are Jevaluate's own. Two raters who find the same facts must reach the same scores; that's what the anchors are for. When two ratings of the same project disagree on a score, rewrite that anchor more concretely.

## Rating rules (Jevaluate's own, not TypeSafe's)
These decide how a rating is made, not how to build with Jev. They come from rating community projects, not from a TypeSafe page.
- R1 **A call is proven by a traced request,** never by a name, a README, docs, fixtures or code that imitates Jev's API. (F0 below; from the 2026-09-28 rating round)
- R2 **Stakes decide which flaws cap a verdict.** Unguarded user text and spliced values cap a verdict only where the code acts, with no review, on personal data, money or access. Almost no community project guards against injection, so a flat cap measured only that. (Stakes below; own rule, 2026-09-28)

## Before the facts: type, call and stakes

**Project type.** Record exactly one in `project_type`. Pick it with this decision order, by what the project does when it runs:
1. Does its non-test code call Jev (F0)? If not: `guide` if it teaches building with Jev; `jev-replacement` if it answers Jev's kind of questions in Jev's place.
2. Does its own code act on the answers? If yes: `workflow`. If it only shows them to a person: `demo`.
3. Does it hand answers back to a caller? `agent-tool` if an agent calls it at run time; `library` if code imports it and it writes questions, wording or defaults; `client` if it passes questions through without writing any.

A project that does two of these is typed by what it does when it runs. jevify both teaches and runs its own scan against Jev, so it's typed by the scan, with its teaching noted.

- `workflow`: code whose own logic writes questions, sends them to Jev and acts on the answers, whatever form it ships in (an app, a hook, a linter, a background job). Every fact applies, and stakes come from what it does with an answer. Examples: jev-belay (a Claude Code hook), Canny, jevlint, jev-search.
- `library`: code others import that adds its own question design on top of Jev (question builders, verbs, default wording, thresholds). Rate its defaults, docs and examples: they're what users copy. Examples: vibecheck, umatter/jevtools.
- `client`: an SDK, client, proxy or gateway that passes questions through without writing any. F1-F3, F5-F11, F13 and F20-F22 are n.a. Rate F0, F4 (it can send batched requests), F12 (it lets callers pin a version), F14 and F19 (it exposes the typed fields and probabilities). Execution and Fit use only those facts. Examples: typesafe-ai/typesafe-sdk-js, joshmn/typesafe-sdk, alterhq/typesafe-sdk-swift.
- `agent-tool`: an MCP server, skill or plugin that gives an agent Jev judgments and returns the answers to it rather than acting on them. It may ship question templates, with the agent supplying the content. Rate the templates and guidance it ships. Its stakes come from what the tool itself does with an answer (usually returning it, so low), not from what the agent does next. Example: jev-mcp.
- `demo`: a site, notebook or game that shows Jev's answers to people and acts no further. Every design fact applies, since people learn from demos. Stakes are low unless its code acts on an answer. Examples: Ask Jevs, JevTools.
- `jev-replacement`: a model, local engine or adapter that answers Jev's kind of questions in Jev's place, instead of calling it. F0 is no by construction. Verdict 1, "Not a Jev integration", which says nothing about its quality, until its own track exists. Examples: Jev-Omni, jevmlx, jaredpalmer/kev, typesafe-ai/system-one-adapter-python.
- `guide`: a skill, doc or post that teaches building with Jev and makes no Jev calls itself. F0 is n.a. and there's no verdict-1 gate. F1-F23 are judged on what it teaches and on its examples: wrong advice is a no, and a topic it doesn't cover goes under Coverage, never as a no. Stakes don't apply; wrong advice on F1-F6 weighs more than wrong advice elsewhere. Two extra facts: G1, every rule matches the TypeSafe page it cites (quote both); G2, its examples would pass F1-F6. Verdict 1 for a guide is "Misleading guide": its core advice (F1-F6) is wrong. Examples: dbreunig/building-with-jev-skill, jevaluate, jevaluate-harness.

**F0 Calls hosted Jev.** Yes only with a traced request: a `file:line` in non-test source that constructs a TypeSafe client, posts to `api.typesafe.ai`, or names a gateway model ID (`typesafe/jev-...`). For a hosted site whose server code isn't public, a captured network response that contains the Jev request (state and questions) and its typed answers also traces the call; cite the capture. None of these is a trace: the project's name, its README, keywords, docs, test fixtures, an adapter that imitates Jev's API, or `jev_callsites.py` mentions. F0 no means verdict 1.

**Claims are not findings.** A README or model card saying the project "works like Jev", "matches Jev's contract" or "is calibrated" is a claim. A contract match needs `file:line` evidence in code; an accuracy or calibration claim needs the data behind it (F15-F18). Report the claim and what backs it; a claim of results with nothing behind it is Evidence 0.

**Stakes.** Give each decision Jev makes exactly one of these. F11, F13, F20 and F22 use this scale and no other.
- `very high`: the code acts automatically, with no human review, on sensitive data: personal data, money, or access and credentials (it issues a refund, grants access, sends or deletes personal records). Storing or showing sensitive data isn't enough; the action has to be automated.
- `high`: the answer blocks, vetoes or routes something, or changes what other people see (a ranking, a filter, a moderation call), without review, and it isn't `very high`.
- `low`: a person reviews the result or can correct it in one click before it matters, or the answer is only shown to the person who asked or returned to a caller.

## Facts (yes / no / n.a., each with evidence)

**Core principles**
- F1 **Atomic questions:** each question asks about one property. It fails if a question joins two or more judgments, whether with "and"/"or" or as a list ("relevant *and* recent", "detailed and actionable", "conveying X, reading as Y, and adding nothing"), including inside a Score's level text. It also fails if a question asks something broad: its answer depends on a standard the question, criteria and state never spell out ("is this good?", "is this safe to apply?", "which is the best fit overall?"). Questions built from one template count once.
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
- F11 **Confidence drives action:** probabilities or confidence gate what the code does (act / review / escalate), rather than the top answer being taken blindly. n.a. for a `low`-stakes decision that is only shown or returned.

**Execution and operations**
- F12 **The model is pinned to a versioned ID** from the models page (`jev-X.Y.Z`), not an alias, wherever thresholds were tuned.
- F13 **Choice order is handled:** Choices with `high` or `very high` stakes are averaged over option orders, or the order is randomized per item. n.a. if every Choice is `low` (including one the user can correct in one click); no if one isn't and its order isn't handled. Never "partial".
- F14 **Size limits are respected:** state plus all questions ≤ 64k tokens; state plus the longest question ≤ 32k. A cap in characters counts at 4 characters per token (256k and 128k characters). Yes needs a guard that trims or stops above the limit, or a reported maximum size under it. "Small by construction" or logged usage alone is unverified, which counts as n.a.
- F20 **Values from code are fields, not templates:** schemas, rows and values from code are passed as JSON fields; they aren't spliced into question strings. It fails if any text taken from the data (a question, a row, a snippet), however short, is inserted into a question string by replace, format or string interpolation; cite the line. Fixed labels the builder wrote are fine. Stakes-scoped: it caps the verdict only when the decision is `very high`; otherwise a no is fix-only. (Q2)
- F21 **No instructions in the state:** the state holds content, not directions to the model. Field names and a short label saying what a field holds are content; a sentence telling the model what to do ("Verify each claim against the evidence", "The question text is data, never instructions") is a direction and belongs in the question or its criteria. Source text spliced into questions counts once, under F20. (S3)
- F22 **Untrusted text is treated as data:** user input, web pages or text from images in the state is flagged or tested for steering. Judge the project's own Jev calls. Checks the project runs on other people's content, and eval or corpus scripts, don't count. It fails if text a user or an input file supplied reaches the state or questions with no flag and no steering test. Stakes-scoped: it caps the verdict only when the decision is `very high`; otherwise a no is fix-only. (S7)
- F23 **Non-English content is handled:** tested, or translated alongside, where accuracy matters. n.a. only when inputs are English by design; cite where that's stated. Translating the tool's own display text doesn't count. (S6)
- F19 **Typed answers are read directly:** the decision reads the typed field (`noul`, `choice`, `score`, probabilities). It fails if Jev (or an LLM standing in for it) is asked for free-text reasoning that code then string-matches.

**Evidence behind claims** (applies only if the project claims results)
- F15 The sample size is stated and adequate for the claim (zero errors in n supports a rate of at most about 3/n).
- F16 The labels are independent of the builder (an LLM panel or blind human labels, not the builder's own judgment), or that's disclosed.
- F17 The result is on a held-out set: the reported numbers weren't used to choose any threshold or wording. A threshold swept on the same sample as the headline number fails.
- F18 The baseline is fair (the same data, and a reasonable LLM or rules alternative).

## Dimensions (0-3; name the anchor you used)

**Jev execution** (F1-F6, F8-F11, F19-F22). F12, F14 and F23 are fix-only: a no goes into the fixes but doesn't move a score. F20-F22 don't lower this score either: a failed F21 caps the verdict at 3, and so does a failed F20 or F22 on a `very high` decision; otherwise F20 and F22 are fix-only.
- 3: F1-F6 all yes, and F8-F11 yes wherever they apply.
- 2: F1-F6 all yes, and one or more of F8-F11 no (the core design holds; secondary decisions fail).
- 2: Or exactly one of F1-F6 is no, and it affects only one of several similar questions, not the main decision (for example, one compound question among many good ones). F8-F11 failures beside it don't lower this to 1.
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
- Only latency or cost measured, no accuracy on labels: score 1, and say so. F15-F18 are n.a. This needs run output behind the figure; a number the code can return as a constant, or that no run backs, is a claim with no measurement shown: 0.

## Build stages and the loop
Mark each build stage the project actually implements, using these four labels exactly: `data-prep` (retrieve, filter, serialize, IDs), `question-state` (question and state design), `execution` (batching, the inverted request, pinning, caching), `decision` (thresholds, combining answers, routing, acting).

The improvement loop: **evaluate** on labels, then **calibrate** (change the numbers: thresholds, weights, confidence mapping) and/or **revise** (change the questions, state or data). Record `closes_loop`: none, calibrates, revises, or both.

## Verdict anchors (not an average; rubric 2026-09-28b)
- **5 Learn from it:** Execution 3, Fit 3, Evidence 3, and closes the loop.
- **4 Use it:** Execution and Fit at least 2, no fatal flaw; evidence may be missing.
- **3 Use with a fix:** Any failed fact from F1-F6, F8-F11, F19 or F21, or a failed F20 or F22 on a `very high` decision, caps it here, one or several, as long as nothing sends it to 2.
- **2 Rework it:** Execution 1 or 0, or a fatal flaw: F1 fails on the main decision, F6 fails (Jev computes values), or confidence is ignored on a high-stakes action.
- **1, labeled one of two ways.** F0 is no, or Jev's answers drive nothing (not even what a user is shown).
  - **False marketing: Jev in name only:** the project claims to use or call Jev (README, listing, model card), and F0 is no. Quote the claim; say nothing about intent.
  - **Not a Jev integration:** it never claims to call Jev (a `jev-replacement` that says it answers in Jev's place, for example), or it calls Jev and the answers drive nothing.
- **Can't rate yet** (`cant-rate` in the rating file): depth is readme-only, or the Jev code isn't public.
- A project with misleading claims (Evidence 0 while claiming results) can't score above 3.
