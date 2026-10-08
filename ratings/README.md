# Jev project ratings

Jev, which TypeSafe launched on September 15, 2026, makes decisions instead of writing text. It answers typed questions with calibrated probabilities, and we're all still working out the frameworks for building with it. TypeSafe has documented a lot of what works. I downloaded and indexed all of its documentation, cookbooks and patterns, and I rate community projects against them.

## How projects are rated

These ratings follow TypeSafe's guidelines, not my taste. Every problem cites the code at a pinned commit and links the TypeSafe page it departs from, along with the fix that page recommends. A few rules come from my own testing; those are marked.

## If your project is here

The fixes are yours. Everything in this folder is released under CC0: use it, change it, ship it, no credit needed. The fixes come from reading your code and haven't been tested against it.

Open an issue if you disagree with a rating, if you've shipped improvements and want a re-rating, or if you'd like help fixing your project.

## Still learning

The rating skill is early, and it learns from this report: each new rating is checked against the ones here, and every disagreement sharpens the rubric. As I keep improving it, some ratings will be redone. If one reads as too harsh or too generous, I'm sorry. Tell me in an issue, and it will help the next version.

The goal is a Jev community that uplevels itself, sharing resources built on the best practices TypeSafe has already laid out.

## Ratings

| Project | Type | Verdict | Why | Rated | Rated by |
|---|---|---|---|---|---|
| [Fox-Islam/jevlint](Fox-Islam__jevlint--gpt-6-sol.md) | library | **4 Use it** | Strong query linting and iterative measurement, with an unpinned model and incomplete comparative evidence. | 2026-10-06 | GPT-6 Sol |
| [Fox-Islam/jevlint](Fox-Islam__jevlint.md) | library | **4 Use it** | Typed, batched, trigger-gated checks; evidence is independent but wordings were tuned on the same corpus and no baseline. | 2026-09-30 | Sonnet 5.5 |
| [altryne/Jevify](altryne__jevify.md) | agent tool | **4 Use it** | Atomic batched Score scanner with pinned model and size guard; nothing measured on accuracy and no injection or non-English test. | 2026-09-30 | Sonnet 5.5 |
| [kitze/skillbox](kitze__skillbox--gpt-6-sol.md) | agent tool | **4 Use it** | Atomic batched Scores support agent recommendations, while outcome measurement and token guarding remain absent. | 2026-10-06 | GPT-6 Sol |
| [kitze/skillbox](kitze__skillbox.md) | agent tool | **4 Use it** | Batched atomic Score questions with thresholds in code and a safe search fallback; no accuracy measured and model floats. | 2026-09-30 | Sonnet 5.5 |
| [kylemclaren/JevPDF](kylemclaren__jevpdf.md) | workflow | **4 Use it** | One atomic noul per line, batched and gated by a named threshold; no accuracy measured, model unpinned. | 2026-09-30 | Sonnet 5.5 |
| [qkal/Canny](qkal__Canny--gpt-6-sol.md) | workflow | **4 Use it** | Two narrow Jev judgments are batched and confidence-gated; live Jev accuracy remains unmeasured. | 2026-10-06 | GPT-6 Sol |
| [qkal/Canny](qkal__Canny.md) | workflow | **4 Use it** | Atomic Noul questions, gated at 0.9 and 0.1, only relax or note; model unpinned, agent text unflagged. | 2026-09-30 | Sonnet 5.5 |
| [valentynkit/jev-belay](valentynkit__jev-belay.md) | workflow | **4 Use it** | Four batched atomic questions gated by code thresholds; cutoff tuned and reported on the same 100 labeled stops. | 2026-10-06 | Sonnet 5.5 |
| [RileyCarney/JevTools](RileyCarney__JevTools--gpt-6-sol.md) | display | **3 Use with a fix** | Real batched Jev display, but overlapping topics, inline thresholds, and unsupported latency claims require fixes. | 2026-10-06 | GPT-6 Sol |
| [RileyCarney/JevTools](RileyCarney__JevTools.md) | display | **3 Use with a fix** | Sound batched design, but overlapping topic options cap it at 3; only an inconsistent latency figure is claimed. | 2026-10-01 | Sonnet 5.5 |
| [altryne/Jevify](altryne__jevify--gpt-6-sol.md) | agent tool | **3 Use with a fix** | A runnable question pack mixes a judgment instruction into state; evaluation remains synthetic. | 2026-10-06 | GPT-6 Sol |
| [Ask Jevs](site__askjevs.site--gpt-6-sol.md) | display | **3 Use with a fix** | Compound questions and incomplete or overlapping choices can produce misleading answers. | 2026-10-06 | GPT-6 Sol |
| [devagrawal09/jev-review](devagrawal09__jev-review--gpt-6-sol.md) | workflow | **3 Use with a fix** | Bounded review calls need confidence-gated severity actions and exclusive Choice categories. | 2026-10-06 | GPT-6 Sol |
| [devagrawal09/jev-review](devagrawal09__jev-review.md) | workflow | **3 Use with a fix** | Staged, gated, well-typed calls; earlier Jev conclusions feed later states (F10) and nothing is measured. | 2026-09-30 | Sonnet 5.5 |
| [jkudish/jev-mcp](jkudish__jev-mcp--gpt-6-sol.md) | agent tool | **3 Use with a fix** | Strong typed tool design is capped by instructions in state and unsupported performance claims. | 2026-10-06 | GPT-6 Sol |
| [jkudish/jev-mcp](jkudish__jev-mcp.md) | agent tool | **3 Use with a fix** | Sound typed design with caller-set thresholds, held at 3 by directive `purpose` fields in state; speed and cost unmeasured. | 2026-09-30 | Sonnet 5.5 |
| [jlowin/vibecheck](jlowin__vibecheck.md) | library | **3 Use with a fix** | Sound typed API, but bare-number Score levels ship in examples and its one results claim has no measurement behind it. | 2026-09-30 | Sonnet 5.5 |
| [kylemclaren/JevPDF](kylemclaren__jevpdf--gpt-6-sol.md) | display | **3 Use with a fix** | Untagged page text weakens state structure, and performance claims lack project measurements. | 2026-10-06 | GPT-6 Sol |
| [superagents-lab/jev-search](superagents-lab__jev-search.md) | workflow | **3 Use with a fix** | Batched atomic questions gated by code thresholds; window and query Choices ignore confidence; model unpinned, nothing measured. | 2026-09-30 | Sonnet 5.5 |
| [umatter/jevtools](umatter__jevtools--gpt-6-sol.md) | library | **3 Use with a fix** | Overlapping action options, fixed Choice order, and spliced candidate text cap an otherwise capable tool binder. | 2026-10-06 | GPT-6 Sol |
| [umatter/jevtools](umatter__jevtools.md) | library | **3 Use with a fix** | Sound election design; very-high recipient Choices use one option order, some questions splice values, defaults tuned on held-out. | 2026-09-30 | Sonnet 5.5 |
| [valentynkit/jev-belay](valentynkit__jev-belay--gpt-6-sol.md) | workflow | **3 Use with a fix** | Overlapping outcome options can change the block veto; reported error rate lacks independent validation. | 2026-10-06 | GPT-6 Sol |
| [Ask Jevs](site__askjevs.site.md) | display | **2 Rework it** | Raw user questions carry no standard, word tags use the wrong primitive, options overlap, and rules sit in state. | 2026-09-30 | Sonnet 5.5 |
| [browser-use/jev-ultrafast](browser-use__jev-ultrafast--gpt-6-sol.md) | library | **2 Rework it** | Automatic browser actions ignore confidence across arbitrary sites and existing Chrome sessions. | 2026-10-06 | GPT-6 Sol |
| [browser-use/jev-ultrafast](browser-use__jev-ultrafast.md) | library | **2 Rework it** | Top answer acts in the user's Chrome at any probability and the Choice order is never varied. | 2026-09-30 | Sonnet 5.5 |
| [jlowin/vibecheck](jlowin__vibecheck--gpt-6-sol.md) | library | **2 Rework it** | Broad questions and undescribed Score levels make the shipped patterns unreliable despite solid typed batching. | 2026-10-06 | GPT-6 Sol |
| [superagents-lab/jev-search](superagents-lab__jev-search--gpt-6-sol.md) | workflow | **2 Rework it** | Ungated Choice answers control search routing and query selection at high stakes. | 2026-10-06 | GPT-6 Sol |
| [thruwire/foreman](thruwire__foreman--gpt-6-sol.md) | library | **2 Rework it** | Broad completion judgments govern autonomous worker actions without a task-specific standard or measured calibration. | 2026-10-06 | GPT-6 Sol |
| [thruwire/foreman](thruwire__foreman.md) | workflow | **2 Rework it** | Finish decision rests on broad catch-all questions, and Jev's earlier scores are fed back into state; nothing measured. | 2026-09-30 | Sonnet 5.5 |
| [AkashPriyadarshii/jev-superpowers](AkashPriyadarshii__jev-superpowers--gpt-6-sol.md) | jev replacement | **1 False marketing: Jev in name only** | The offered Jev-compatible local endpoint uses heuristics, while the project claims TypeSafe Cloud Jev gates without a hosted call. | 2026-10-06 | GPT-6 Sol |
| [AkashPriyadarshii/jev-superpowers](AkashPriyadarshii__jev-superpowers.md) | jev replacement | **1 False marketing: Jev in name only** | Claims Jev answers gate every decision, but ships no Jev call; its own bridge answers with keyword matching. | 2026-09-30 | Sonnet 5.5 |
| [Jev-Omni](hf__akhilaaa3__Jev-Omni--gpt-6-sol.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | Offers local typed decision answers without hosted Jev; the replacement track is not yet rated. | 2026-10-06 | GPT-6 Sol |
| [Jev-Omni](hf__akhilaaa3__Jev-Omni.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | Open Gemma-based model offering Jev-style probabilities with no Jev call; no replacement track exists yet. | 2026-09-30 | Sonnet 5.5 |
| [bnsd55/jevmlx](bnsd55__jevmlx--gpt-6-sol.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | Local model serves Jev-style typed answers without calling hosted Jev; replacement track is not yet rated. | 2026-10-06 | GPT-6 Sol |
| [bnsd55/jevmlx](bnsd55__jevmlx.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | Local Apple Silicon reimplementation of Jev-style scoring; makes no hosted Jev calls, so it routes to replacement. | 2026-09-30 | Sonnet 5.5 |
| [typesafe-ai/system-one-adapter-python](typesafe-ai__system-one-adapter-python--gpt-6-sol.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | It offers Jev-shaped answers through other LLM providers, so the replacement track applies. | 2026-10-06 | GPT-6 Sol |
| [typesafe-ai/system-one-adapter-python](typesafe-ai__system-one-adapter-python.md) | jev replacement | **n.a. (replaces Jev, not yet rated)** | Offers Jev-style typed answers from OpenAI, Anthropic and Gemini models without calling Jev; replacement track not yet defined. | 2026-09-30 | Sonnet 5.5 |

