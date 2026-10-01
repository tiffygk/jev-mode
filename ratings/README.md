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

| Project | Type | Verdict | Why | Rated |
|---|---|---|---|---|
| [Fox-Islam/jevlint](Fox-Islam__jevlint.md) | library | **4 Use it** | Typed, batched, trigger-gated checks; evidence is independent but wordings were tuned on the same corpus and no baseline. | 2026-09-30 |
| [altryne/Jevify](altryne__jevify.md) | agent tool | **4 Use it** | Atomic batched Score scanner with pinned model and size guard; nothing measured on accuracy and no injection or non-English test. | 2026-09-30 |
| [kitze/skillbox](kitze__skillbox.md) | agent tool | **4 Use it** | Batched atomic Score questions with thresholds in code and a safe search fallback; no accuracy measured and model floats. | 2026-09-30 |
| [kylemclaren/JevPDF](kylemclaren__jevpdf.md) | workflow | **4 Use it** | One atomic noul per line, batched and gated by a named threshold; no accuracy measured, model unpinned. | 2026-09-30 |
| [qkal/Canny](qkal__Canny.md) | workflow | **4 Use it** | Atomic Noul questions, gated at 0.9 and 0.1, only relax or note; model unpinned, agent text unflagged. | 2026-09-30 |
| [superagents-lab/jev-search](superagents-lab__jev-search.md) | workflow | **4 Use it** | Batched atomic questions gated by code thresholds; no capping failure, but model unpinned and nothing measured. | 2026-09-30 |
| [valentynkit/jev-belay](valentynkit__jev-belay.md) | workflow | **4 Use it** | Four batched questions gated by thresholds in code; the 0.70 cutoff was tuned on the same labeled stops it reports. | 2026-09-30 |
| [RileyCarney/JevTools](RileyCarney__JevTools.md) | demo | **3 Use with a fix** | Batched, typed and in code; one two-part question and overlapping topic options. | 2026-09-28 † |
| [devagrawal09/jev-review](devagrawal09__jev-review.md) | workflow | **3 Use with a fix** | Staged, gated, well-typed calls; earlier Jev conclusions feed later states (F10) and nothing is measured. | 2026-09-30 |
| [jkudish/jev-mcp](jkudish__jev-mcp.md) | agent tool | **3 Use with a fix** | Sound typed design with caller-set thresholds, held at 3 by directive `purpose` fields in state; speed and cost unmeasured. | 2026-09-30 |
| [jlowin/vibecheck](jlowin__vibecheck.md) | library | **3 Use with a fix** | Sound typed API, but bare-number Score levels ship in examples and its one results claim has no measurement behind it. | 2026-09-30 |
| [umatter/jevtools](umatter__jevtools.md) | library | **3 Use with a fix** | Sound election design; very-high recipient Choices use one option order, some questions splice values, defaults tuned on held-out. | 2026-09-30 |
| [Ask Jevs](site__askjevs.site.md) | demo | **2 Rework it** | Raw user questions carry no standard, word tags use the wrong primitive, options overlap, and rules sit in state. | 2026-09-30 |
| [browser-use/jev-ultrafast](browser-use__jev-ultrafast.md) | library | **2 Rework it** | Top answer acts in the user's Chrome at any probability and the Choice order is never varied. | 2026-09-30 |
| [thruwire/foreman](thruwire__foreman.md) | workflow | **2 Rework it** | Finish decision rests on broad catch-all questions, and Jev's earlier scores are fed back into state; nothing measured. | 2026-09-30 |
| [AkashPriyadarshii/jev-superpowers](AkashPriyadarshii__jev-superpowers.md) | jev replacement | **1 False marketing: Jev in name only** | Claims Jev answers gate every decision, but ships no Jev call; its own bridge answers with keyword matching. | 2026-09-30 |
| [Jev-Omni](hf__akhilaaa3__Jev-Omni.md) | jev replacement | **1 Replaces Jev, not yet rated** | Open Gemma-based model offering Jev-style probabilities with no Jev call; no replacement track exists yet. | 2026-09-30 |
| [bnsd55/jevmlx](bnsd55__jevmlx.md) | jev replacement | **1 Replaces Jev, not yet rated** | Local Apple Silicon reimplementation of Jev-style scoring; makes no hosted Jev calls, so it routes to replacement. | 2026-09-30 |
| [typesafe-ai/system-one-adapter-python](typesafe-ai__system-one-adapter-python.md) | jev replacement | **1 Replaces Jev, not yet rated** | Offers Jev-style typed answers from OpenAI, Anthropic and Gemini models without calling Jev; replacement track not yet defined. | 2026-09-30 |

† Rated under an earlier rubric; a re-rating is queued.
