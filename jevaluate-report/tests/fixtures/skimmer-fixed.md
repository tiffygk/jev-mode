---
title: "skimmer: a Jevaluate rating and suggested fixes"
repo: https://github.com/dorkitude/skimmer
commit: 6ede87c0c1d77fcff823a1d2d36051ab120b3eaf
date: 2026-10-15
method: "Jevaluate rubric 2026-09-29.2 (https://github.com/tiffygk/jev-mode) and a statistics claim check of the eval's headline figures"
verdict: "2, Rework it"
scores: {execution: 1, fit: 3, coverage: 3, evidence: 1}
fixes:
  - S1: Split the keep-or-drop question
  - S2: Pin the default model
  - S3: Test Noul criteria
  - S4: Keep data out of the question text
  - S5: Add a prompt-injection check
  - S6: Fix id matching in the chunk-size sweep
  - S7: Hold out goals the settings never saw
  - S8: Add a keyword baseline
  - S9: Add near-miss negative goals
  - S10: Run more draws and shift offsets
  - S11: Add a non-English page
  - S12: Put n and an interval on each headline
  - S13: Test the equal-or-better claim
  - S14: Reconcile the token-per-goal figures
  - S15: Fix the batch token estimate
  - S16: Report unjudged chunks
---

# skimmer: a Jevaluate rating and suggested fixes

Thanks for building the eval in #1 and shipping the state prompt in #2. You've seen how I review Jev projects; this is that review run on skimmer at `6ede87c`, plus a statistics check of the eval that could use work to be unbiased (this explains how your recall is so high).

skimmer's structure has a lot of great things: structured state with ids, batching under a token budget, typed answers read directly, and a rule that keeps any chunk Jev never judged. However the verdict (see it right below the index), is still a 2 "Rework It" due to poor "atomic" question design, as questions weight multiple factors at once in a Noul. 

Start with three fixes to get it to a 4 "Use it!" verdict: 
- [Pin the default model](#s2-pin-the-default-model) starts with a one-line change: per the docs' alias table, defaults run `jev-1.13.0`, and every figure came from `jev-1.14.0`. 
- [Split the keep-or-drop question](#s1-split-the-keep-or-drop-question) is the one change that moves the verdict. 
- [Fix id matching in the chunk-size sweep](#s6-fix-id-matching-in-the-chunk-size-sweep) comes third, because the harness can't measure the "discrimination collapses" result it reports.

Note my Jevaluate and Stats ML Eval workflows are still early, so if you disagree with anything or find it simply nitpicky lmk and I will incorporate your feedback too! Feel free to point your agents at my suggestions prioritized in the index below:

| ID | Fix | Where | Order |
|---|---|---|---|
| S1 | [Split the keep-or-drop question](#s1-split-the-keep-or-drop-question) | [DEFAULT.md#L9-L18][c1] | first |
| S2 | [Pin the default model](#s2-pin-the-default-model) | [config.go#L28][c2] | first |
| S6 | [Fix id matching in the chunk-size sweep](#s6-fix-id-matching-in-the-chunk-size-sweep) | [evalskim/main.go#L348-L361][c3] | first |
| S3 | [Test Noul criteria](#s3-test-noul-criteria) | [types.go#L18-L24][c4] | next |
| S4 | [Keep data out of the question text](#s4-keep-data-out-of-the-question-text) | [DEFAULT.md#L8-L9][c5] | next |
| S7 | [Hold out goals the settings never saw](#s7-hold-out-goals-the-settings-never-saw) | [results.md#L45-L48][c6] | next |
| S8 | [Add a keyword baseline](#s8-add-a-keyword-baseline) | [evals/README.md#L25-L27][c7] | next |
| S12 | [Put n and an interval on each headline](#s12-put-n-and-an-interval-on-each-headline) | [README.md#L189-L192][c8] | next |
| S13 | [Test the equal-or-better claim](#s13-test-the-equal-or-better-claim) | [CHANGELOG.md#L14-L17][c9] | next |
| S5 | [Add a prompt-injection check](#s5-add-a-prompt-injection-check) | [judge.go#L179][c10] | later |
| S9 | [Add near-miss negative goals](#s9-add-near-miss-negative-goals) | [goals.json#L263-L268][c11] | later |
| S10 | [Run more draws and shift offsets](#s10-run-more-draws-and-shift-offsets) | [results.md#L23][c12] | later |
| S11 | [Add a non-English page](#s11-add-a-non-english-page) | [SOURCES.md#L10-L23][c13] | later |
| S14 | [Reconcile the token-per-goal figures](#s14-reconcile-the-token-per-goal-figures) | [results.md#L22][c14] | later |
| S15 | [Fix the batch token estimate](#s15-fix-the-batch-token-estimate) | [judge.go#L105][c15] | later |
| S16 | [Report unjudged chunks](#s16-report-unjudged-chunks) | [skim.go#L162-L170][c16] | later |

For other readers, a few terms explained from your eval. A goal-draw is one goal in one of the eval's two runs. R@k asks whether any gold chunk ranks in the top k; all-modes@10, whether every gold chunk does. Base and state are two prompts in the variants run, collect goals ask for every instance of something, and a confusable goal is answered by only one of two near-duplicate chunks: the gold chunk, not the "other". A Noul is Jev's yes/no question. Intervals are 95% Wilson.

## Rating: verdict 2, Rework it

Execution ●○○ · Fit ●●● · Coverage ●●● · Evidence ●○○

This is my Jevaluate skill in action: [tiffygk/jev-mode](https://github.com/tiffygk/jev-mode), rubric `2026-09-29.2`. It scores four dimensions from 0 to 3, then sets a verdict by rule, never by average, from 5 (Learn from it) down to 2 (Rework it); 1 marks projects it doesn't rate. I checked the eval's figures with my statistics skill too, which reads each claim as a statistician would: the unit counted, n, the interval, the baseline, and whether the goals were held out.

- **Verdict 2, Rework it:** in the rubric, 2 means a core rule is broken. Here it's one rule: the main keep-or-drop question weighs several factors at once, a fatal flaw on the main decision in the rubric (see [Split the keep-or-drop question](#s1-split-the-keep-or-drop-question)). It was the closest call in the rating. With that one fixed, skimmer would rate 4, Use it.
- **Execution 1 of 3:** the same question sets it. The state, typed answers, batching and thresholds pass the rubric's checks.
- **Fit 3 of 3:** a Noul suits the keep-or-drop call, and the probability gates the action.
- **Coverage 3 of 3:** skimmer ships every command its README lists.
- **Evidence 1 of 3:** the figures come with a method, but the prompt, cutoff advice and chunk size were chosen and reported on the same goals, with no intervals and no baseline outside Jev (see [Hold out goals the settings never saw](#s7-hold-out-goals-the-settings-never-saw), [Add a keyword baseline](#s8-add-a-keyword-baseline) and [Put n and an interval on each headline](#s12-put-n-and-an-interval-on-each-headline)).


## What already works

- One run at threshold 0 stores every chunk's probability, so all 11 thresholds are scored on identical data, paired by construction ([evals/README.md#L45-L47][c17]).
- A fingerprint of goals, catalog and corpus is stored with each run ([results.md#L7][c18]).
- The key is adjudicated mechanically: the decisive fact must appear in the gold chunk, and goals that fail are dropped ([evals/README.md#L25-L27][c7]).
- Gold, confusable and distractor goals are scored apart, not blended ([evalskim/main.go#L309][c19]).
- The second goal set was written blind: goals came from document openings before any chunk was seen, then a second model family marked the gold chunks ([results-v2.md#L5-L7][c20]).
- The eval pins `jev-1.14.0`, never an alias ([evals/README.md#L45-L47][c17]), and names its two misses (g005, g016) with a cause ([results.md#L59-L62][c21]).
- Misses sit beside hits: the variants table shows R@10 dropping from 1.000 to 0.986, 72 to 71 of 72 goal-draws ([variants/README.md#L31-L32][c22]).
- "19% fewer input tokens" holds for the variants' state question: 5,053 to 4,105 is an 18.8% drop, an exact count (same table).
- Unjudged chunks are kept, so a failed batch never deletes content ([skim.go#L162-L170][c16]).

## Jev question and model

### S1: Split the keep-or-drop question

**What we saw.** One question per chunk weighs three things at once: topic ("passages about a different topic"), substance ("carries substance that bears on the goal") and what the reader knows ("generic background the reader already knows") ([DEFAULT.md#L9-L18][c1]). A multi-part goal goes in whole. The "atomic" variant split it into a subject question and a usable-fact question and lost at R@10 ([variants/README.md#L16-L18][c23], [#L48-L50][c24]).

**Why it matters.** Collect goals lose a gold chunk from the top 10, which your results put down to "a single generic relevance noul" ([results-v2.md#L24-L29][c25]). Before the state prompt, that happened in 5 of 28 goal-draws through the real pipeline ([`runs-v2.jsonl`][c26]; 3 of 14 goals, Wilson 0.08 to 0.48) and 13 of 28 through the variants harness's base question (7 of 14, 0.27 to 0.73). The state prompt in that harness loses 10 of 28 ([#L44-L45][c27]; 5 of 14, 0.16 to 0.61). Before the state prompt, comparison goals reach R@1 on 2 of 4 (0.15 to 0.85). The split hasn't had a fair test: the atomic variant multiplied its two answers ([evalvariants/main.go#L232][c28]), so a chunk that is on-topic but thin scores near zero.

**Source.** Reference rule, [Introduction](https://docs.typesafe.ai/introduction#atomic-questions-composed-in-code): "If the question you want to ask would require extended reasoning or weighs multiple independent factors, decompose it." Reference rule, [Primitives](https://docs.typesafe.ai/primitives#split-a-complex-judgment-into-several-questions): "A judgment that depends on several things is best split into one question per thing. Combine the answers in your code, giving each a weight for its relative importance." Reference rule, [Noul](https://docs.typesafe.ai/primitives/noul#writing-a-noul-question): "Ask one yes/no question per Noul." Cookbook example, [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages): four Nouls per passage, routed in code; none of the four asks whether to include the passage.

**Suggested change.** skimmer takes one `--goal` string ([skim.go#L58][c29]), so let the caller pass a multi-part goal (a comparison, a list of things to collect) as several goals; ask one Noul per part and keep a chunk that clears any part. In place of the atomic variant's product, try a weighted sum, or a low relevance cutoff and then rank by evidence. The cookbook's cutoffs (relevance 0.45, evidence 0.55) are still two thresholds, and it says to "Treat them as a starting point, not defaults."

**How to check it.** Run the new combine as a sixth variant in `evalvariants`, on held-out goals (see [Hold out goals the settings never saw](#s7-hold-out-goals-the-settings-never-saw)). Compare all-modes@10 on collect and comparison goals against `state`, goal by goal.

### S2: Pin the default model

**What we saw.** `DefaultModel = "jev-latest"` ([config.go#L28][c2], [client.go#L18][c30]). The README says "Measured on `jev-1.14.0`" ([README.md#L189][c31]), and the response's `Model` field ([types.go#L56][c32]) is never read.

**Why it matters.** Per the docs' alias table, a user on defaults runs `jev-1.13.0` today, the model none of the figures or the 0.7 threshold advice came from. When the alias moves, the answers change with no change to skimmer, and nothing in the output says which model answered. The 1.13 docs also warn that "Accuracy falls as the state grows with content unrelated to the decision", and skimmer sends up to 24 chunks in one state ([judge.go#L19-L27][c33]).

**Source.** Reference rule, [Models](https://docs.typesafe.ai/models#aliases): `jev-latest` points to `jev-1.13.0`, "The most recent stable, official release", and `jev-preview` to `jev-1.14.0`, "The most recent release, official or not." Same section: "Each response's `model` field gives the versioned ID that answered, so you can log which model produced each result. If you have tuned confidence thresholds against one version, send that version's ID instead of the alias." Reference rule, [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13#large-state-full-of-irrelevant-detail).

**Suggested change.** Rerun the evals on `jev-1.13.0` and pin it, or pin `jev-1.14.0` knowing the docs list it as the preview build. Print the answering `model` in `--json` output and the stderr summary.

**How to check it.** Run `evalskim -model jev-1.13.0` (the harness refuses aliases) and compare with the 1.14 figures.

### S3: Test Noul criteria

**What we saw.** The yes and no boundaries live in the instruction text. `NoulQuestion` never sets criteria, and the `Criteria []string` field fits Score levels, not a Noul's `true` and `false` ([types.go#L18-L24][c4]). None of the five variants tried criteria.

**Why it matters.** That boundary ("substance that bears on the goal" versus "only mentions a keyword") sits in prose, and no variant tested whether criteria change its answers.

**Source.** Reference rule, [Noul](https://docs.typesafe.ai/primitives/noul#writing-a-noul-question): "When the boundary is subtle, add `criteria` with `true` and `false` descriptions ... try your questions with and without `criteria` and keep whichever gives better answers on your documents." Reference rule, [API](https://docs.typesafe.ai/api#noul): Noul `criteria` is an object with `true` and `false`.

**Suggested change.** Add a Noul criteria type with `true` and `false`. Move the "answer yes if" and "answer no for" sentences into it, leaving one short question.

**How to check it.** A `criteria` variant scored against `state` on held-out goals (see [Hold out goals the settings never saw](#s7-hold-out-goals-the-settings-never-saw)). Exact McNemar needs at least 6 goals to flip one way, and none the other, for p < 0.05.

### S4: Keep data out of the question text

**What we saw.** When a source is set, the default prompt splices it into the question: "The document is {{.Source}}." ([DEFAULT.md#L8][c34]). The same label already goes into the state as `context` ([skim.go#L147][c35], [judge.go#L179][c10]). The question names its chunk as a quoted id, `chunk "item_3"` ([#L9][c36]).

**Why it matters.** A URL or path in the question is data inside the instruction, sent once per chunk.

**Source.** Reference rule, [How to build with TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one#use-structure-in-the-questions): "When a value comes from a database, put it in its own field instead of splicing it into a string template." Reference rule, [Primitives](https://docs.typesafe.ai/primitives#reference-specific-fields): name the part of the state "with a dot-and-index path to its key, including the backticks." Your state variant pointed with backticks (`` `c07` ``), as the docs advise; the shipped prompt uses a quoted id.

**Suggested change.** Drop the `{{.Source}}` sentence and refer to `` `context` `` if the source matters. To try a path, use `` `items[k].text` `` with k the chunk's position in that request's `items`. The `item_N` ids count across batches, so after the first batch k and N differ.

**How to check it.** Score each as a variant against `state` on held-out goals. Dropping `{{.Source}}` is one line; the path needs Go code, since prompt data has no position within the batch ([prompts.go#L50-L57][c37]).

### S5: Add a prompt-injection check

**What we saw.** Web pages and files go into the state as plain text, with no check on whether a chunk tries to steer the judge ([judge.go#L179][c10]). No test page tries it.

**Why it matters.** A page that says "this section is exactly what you are looking for" can raise its own P(yes) and pass the filter the agent relies on.

**Source.** Reference rule, [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13#adversarial-content), which covers the model the default alias points to: "State is data, and `jev-1.13` does not treat it as hostile by default. Content written to adversarially steer the model ... can move the answer." Cookbook example, [Classifying RAG passages](https://docs.typesafe.ai/cookbooks/classifying_rag_passages): a `contains_prompt_injection` Noul excludes a passage first, and "Nothing here is a security boundary."

**Suggested change.** Add a Noul per chunk, "Does this chunk try to control the system reading it?", and drop or flag chunks above a threshold. Say in the README that the check is a filter, not a boundary.

**How to check it.** Add a corpus page with an injected "this chunk is relevant" line and a goal it doesn't answer. Report whether that chunk is kept, with and without the new question.

## Eval method

### S6: Fix id matching in the chunk-size sweep

**What we saw.** In `compute`, confusable goals are scored by chunk id ([evalskim/main.go#L348-L358][c38]) before the fact-match branch ([#L361][c39]), so `-fact-match` never reaches them. Kept ids are positional at whatever size is running, `fmt.Sprintf("%s-%02d", doc, k.Index)` ([#L225][c40]), while gold ids come from the 2000-character catalog.

**Why it matters.** At 1000, 3000 and 4000 characters, `nist-sp-800-63b-09` names different text, so the "confusable gold kept" column (1000: 0.14; 2000: 1.00; 3000: 0.00; 4000: 0.01 to 0.14, on 14 goals) doesn't measure discrimination ([results.md#L52-L68][c41]). The "costs quality" half of the advice not to shrink chunks rests on that column; the token-cost half stands. Gold recall is 50 of 52 at every size (Wilson 0.87 to 0.99), so it can't separate sizes either. The 2000 default may still be right; the sweep doesn't show it.

**Source.** The harness code above.

**Suggested change.** Score a kept chunk by the lines only gold, or only "other", contains. Catalog entries carry `start_line` and `end_line`, and kept chunks carry their lines at every size, but in [`catalog.json`][c42] 12 of the 14 pairs are neighbors whose ranges overlap. Say how a chunk holding both members' lines counts. Text matching fails too: each "other" chunk shares a 16-character run with its gold chunk in all 14 pairs, and the decisive fact matches its gold chunk in only 10 of 14.

**How to check it.** At 2000 characters the new scorer should reproduce both id-matched columns: 14 of 14 gold kept and 6 of 28 goal-draws "other" kept. Then rerun 1000, 3000 and 4000.

### S7: Hold out goals the settings never saw

**What we saw.** The 0.7 threshold advice comes from a sweep of the same 78 goals that report it ([results.md#L45-L48][c6]). The decision to keep 2000-character chunks rests on those 78 goals, and the state prompt was picked from five variants on the same 36 goals that report its gain ([variants/README.md#L42-L47][c43]).

**Why it matters.** The 0.7 advice was picked from 11 settings on the goals that report it, so it looks better there than it will on new goals. "0.7 halves the near-duplicate leakage" is 6 to 3 of 28 goal-draws (14 goals). Both thresholds read the same stored scores, so all 3 of those changes go one way; exact McNemar still gives p = 0.25, and counting per goal doesn't lower it.

**Source.** Cookbook example, [AutoResearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery): 1,200 dev rows and 800 held out, because "Scoring on the same rows would mostly measure how well the loop fitted itself to them." scikit-learn, [Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html): "there is still a risk of overfitting on the test set because the parameters can be tweaked until the estimator performs optimally." Dwork et al., [Generalization in Adaptive Data Analysis and Holdout Reuse](https://arxiv.org/abs/1506.02629): "Reusing a holdout set adaptively multiple times can easily lead to overfitting to the holdout set itself."

**Suggested change.** Split goals into a development set and a held-out set before the next round of choices, by document so that no document is in both. Tune the threshold, chunk size and prompt on development goals only, and report the held-out numbers once.

**How to check it.** The held-out recall and kept-chunk figures at the chosen settings, beside the development figures.

### S8: Add a keyword baseline

**What we saw.** First-set gold goals are "a paraphrased reading goal with a known gold chunk; authored per selected chunk" ([evals/README.md#L25-L27][c7]), so each goal is written while looking at the chunk that answers it. Apart from the keep-everything threshold of 0, every comparison in the repo is Jev against Jev.

**Why it matters.** Goals written from their answer can share its words, and nothing in the repo measures how much. 52 of 52 fits a working filter; without a cheaper method on the same goals, it can't show what Jev adds.

**Source.** Lee, Chang and Toutanova, [Latent Retrieval for Weakly Supervised Open Domain Question Answering](https://arxiv.org/abs/1906.00300): when SQuAD's question writers saw the evidence, the result was "artificially large lexical overlap between the question and evidence."

**Suggested change.** Run a keyword filter (BM25 over the same chunks, keeping the top k) on both goal sets, with k set so it keeps about as many chunks as skimmer does.

**How to check it.** Recall and kept chunks per goal for both methods, side by side, on the first set and on goals-v2.

### S9: Add near-miss negative goals

**What we saw.** The 12 distractors are far off-topic, such as "Find the recommended daily intake of vitamin D for adults." and "What is the capital of Australia and its population?" ([goals.json#L263-L268][c11]).

**Why it matters.** "Never keeps a chunk for an unanswerable goal" ([results.md#L20][c44]) rests on 0 of 12 easy cases (Wilson 0 to 0.24). A goal on the document's topic that the document doesn't answer isn't tested.

**Source.** Brown, Cai and DasGupta, [Interval Estimation for a Binomial Proportion](https://repository.upenn.edu/handle/20.500.14332/47517) (2001): "we recommend the Wilson interval or the equal-tailed Jeffreys prior interval for small n."

**Suggested change.** Write near-miss goals per document: same subject, a fact the document doesn't contain. Score them as their own kind.

**How to check it.** The kept-chunk rate on near-miss goals, with its n and interval.

### S10: Run more draws and shift offsets

**What we saw.** "Cross-draw score delta mean 0.003, max 0.09" comes from 2 draws ([results.md#L23][c12]). No code under `evals/cmd/` computes it. The boundary claim rests on one shift of 200 runes ([`runs-shift.jsonl`][c45], [#L72-L76][c46]).

**Why it matters.** Draws already flip decisions: in [`runs.jsonl`][c47], 15 chunks in 13 goals land on opposite sides of 0.5 in the two draws, and the largest swing I find is 0.12 (over the 4,199 chunks scored in both draws). One offset, equal to the overlap, can't show robustness to the others.

**Source.** Atil et al., [Non-Determinism of "Deterministic" LLM Settings](https://arxiv.org/abs/2408.04667): "none of the LLMs consistently delivers repeatable accuracy across all tasks, much less identical output strings."

**Suggested change.** Commit the delta script. Run 5 or more draws and report how many chunks change sides of the threshold. Shift by a few offsets (for example 50, 100, 200 and 500 runes).

**How to check it.** A flip count per draw pair, and recall per offset, each with its n.

### S11: Add a non-English page

**What we saw.** All 12 corpus documents are English ([SOURCES.md#L10-L23][c13]), and skimmer takes any URL.

**Why it matters.** A user skimming a page in another language gets no measured number.

**Source.** Reference rule, [Models](https://docs.typesafe.ai/models#language-support): "Other languages, including CJK scripts, are handled but not equally well; test on your own content before relying on Jev for a non-English workload."

**Suggested change.** Add one or two non-English documents with gold goals, or say in the README that the figures cover English pages only.

**How to check it.** Recall and kept chunks on the new documents, reported apart from the English ones.

## Reporting

### S12: Put n and an interval on each headline

**What we saw.** "Measured on `jev-1.14.0`: recall 1.000, distractor leak 0.000" ([README.md#L189-L192][c8]). These come from the 0.1.101 prompt ([CHANGELOG.md#L12-L18][c48]). The shipped 0.1.102 prompt hasn't been measured: the variants' state question is shorter, points with backticks and sends each document in one request ([evalvariants/main.go#L198-L209][c49]), while `DEFAULT.md` keeps the boundary text and a quoted id, sent in batches of up to 24.

**Why it matters.** "Recall 1.000" reads as perfect. The data support "52 of 52 goals, Wilson 0.93 to 1.00". The two draws rerun the same goals, so n is 52. Leak is 0 of 12 goals (0 to 0.24); confusable gold kept, 14 of 14 (0.78 to 1.00).

**Source.** Brown, Cai and DasGupta (2001), as in [Add near-miss negative goals](#s9-add-near-miss-negative-goals).

**Suggested change.** Write each headline as k of n with its interval, name the prompt version and model, and count goals rather than goal-draws.

**How to check it.** Every figure in the README and results files has its n and interval.

### S13: Test the equal-or-better claim

**What we saw.** The CHANGELOG says "equal-or-better recall at every rank" ([CHANGELOG.md#L14-L17][c9]). The table shows R@10 of 1.000 for base and 0.986 for state ([variants/README.md#L29-L32][c50]).

**Why it matters.** Per goal, from [`base-runs.json`][c51] and [`state-runs.json`][c52]: state wins 2 to 0 at R@3 and 1 to 0 at R@5, base wins 1 to 0 at R@10, and R@1 and all-modes@10 split evenly. A goal counts for the prompt that hit in more of its two draws; score ties break by chunk id, as in your harness. Exact McNemar p is 0.5 at R@3 and 1 elsewhere. With 36 goals, the data can't tell the two prompts apart in either direction.

**Source.** Dietterich, [Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms](https://web.engr.oregonstate.edu/~tgd/publications/dietterich-approximate-statistical-tests-nc1998.pdf) (1998): recommends McNemar's test when two classifiers are each run once on the same test set. MedCalc, [McNemar test](https://www.medcalc.org/en/book/mcnemar-test.php): below about 25 goals where the two methods disagree, use the exact form of the test. Walker and Nowacki, [Understanding equivalence and noninferiority testing](https://pmc.ncbi.nlm.nih.gov/articles/PMC3019319): a claim of no worse needs a margin set in advance.

**Suggested change.** Reword to "In the variants run: 19% fewer input tokens, recall within 2 goals of base at every rank." Or set a margin first, then rerun with enough goals to test it.

**How to check it.** Per rank, the number of goals where the two prompts disagree, and the test result against the margin.

### S14: Reconcile the token-per-goal figures

**What we saw.** At the default design, input tokens per goal are 16,986 in the baseline table ([results.md#L22][c14]) and 53,786 in the chunk-size table ([#L55][c53]), both on the 78 goals, and 5,053 for base on the 36 goals-v2 goals ([variants/README.md#L31][c54]).

**Why it matters.** These are token counts for the goals run, so no interval applies; the question is what they count. 53,786 is the mean of `runs.jsonl` over all 78 goals, including 12 distractors judged over all 236 chunks at about 239,200 tokens each. 16,986 matches no goal kind in that file (gold goals average 19,577). A reader can't tell what one goal costs.

**Source.** The three tables above and `runs.jsonl`.

**Suggested change.** State what each figure counts (one draw or both, distractors over all 12 documents or one, harness or CLI batching), or recompute them one way.

**How to check it.** One input-tokens-per-goal figure at the default design, with its definition.

## Minor

### S15: Fix the batch token estimate

**What we saw.** `planBatches` charges `2*estimateTokens(text)` per item ([judge.go#L105][c15]), and the comment says text "appears twice in a request" ([#L15-L16][c55]). Since 0.1.102 the built-in prompts send it once. The overhead probe subtracts the chunk's text from a question that no longer contains it, so overhead clamps to 24 tokens before a quarter of the goal's estimate is added ([#L134-L138][c56]).

**Why it matters.** The estimate is off both ways: about 500 tokens too high per 2,000-character chunk, and too low by the question's own length, about 190 tokens for the built-in skim prompt. At the default the 24-item cap usually binds first; with larger `--chunk-chars`, batches hold about half what the budget allows.

**Source.** The code above and [CHANGELOG.md#L12-L18][c48].

**Suggested change.** Charge the text once, twice only when the template uses `{{.Text}}`, and measure overhead from the rendered question without subtracting the text.

**How to check it.** A unit test in `judge_test.go` that compares the estimate with the length of the marshaled request, for a built-in prompt and for a `{{.Text}}` prompt.

### S16: Report unjudged chunks

**What we saw.** An unjudged chunk is kept ([skim.go#L162-L170][c16], [filter.go#L133][c57]). The CLI already prints "unjudged kept" ([cmd/skim.go#L303-L305][c58]), but the eval results files don't record it.

**Why it matters.** A failed batch keeps its chunks, so eval recall rises with no sign of the failure.

**Source.** The code above.

**Suggested change.** Add an unjudged count per goal to `runs.jsonl` and the results tables.

**How to check it.** The unjudged count is zero, or shown, in every results table.

[c1]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/prompts/skim_document/DEFAULT.md#L9-L18
[c2]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/config/config.go#L28
[c3]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalskim/main.go#L348-L361
[c4]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/types.go#L18-L24
[c5]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/prompts/skim_document/DEFAULT.md#L8-L9
[c6]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L45-L48
[c7]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/README.md#L25-L27
[c8]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/README.md#L189-L192
[c9]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/CHANGELOG.md#L14-L17
[c10]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/judge.go#L179
[c11]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/gold/goals.json#L263-L268
[c12]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L23
[c13]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/corpus/SOURCES.md#L10-L23
[c14]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L22
[c15]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/judge.go#L105
[c16]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/skim/skim.go#L162-L170
[c17]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/README.md#L45-L47
[c18]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L7
[c19]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalskim/main.go#L309
[c20]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results-v2.md#L5-L7
[c21]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L59-L62
[c22]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L31-L32
[c23]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L16-L18
[c24]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L48-L50
[c25]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results-v2.md#L24-L29
[c26]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/runs-v2.jsonl
[c27]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L44-L45
[c28]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalvariants/main.go#L232
[c29]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/cmd/skim.go#L58
[c30]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/client.go#L18
[c31]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/README.md#L189
[c32]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/types.go#L56
[c33]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/judge.go#L19-L27
[c34]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/prompts/skim_document/DEFAULT.md#L8
[c35]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/skim/skim.go#L147
[c36]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/prompts/skim_document/DEFAULT.md#L9
[c37]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/prompts/prompts.go#L50-L57
[c38]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalskim/main.go#L348-L358
[c39]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalskim/main.go#L361
[c40]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalskim/main.go#L225
[c41]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L52-L68
[c42]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/gold/catalog.json
[c43]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L42-L47
[c44]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L20
[c45]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/runs-shift.jsonl
[c46]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L72-L76
[c47]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/runs.jsonl
[c48]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/CHANGELOG.md#L12-L18
[c49]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/cmd/evalvariants/main.go#L198-L209
[c50]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L29-L32
[c51]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/base-runs.json
[c52]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/state-runs.json
[c53]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/skimmer/0.1.101/results.md#L55
[c54]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/evals/variants/README.md#L31
[c55]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/judge.go#L15-L16
[c56]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/internal/jev/judge.go#L134-L138
[c57]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/cmd/filter.go#L133
[c58]: https://github.com/dorkitude/skimmer/blob/6ede87c0c1d77fcff823a1d2d36051ab120b3eaf/cmd/skim.go#L303-L305
