[← All ratings](README.md)

> **superagents-lab/jev-search** at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe09d1ccfe720f38998f36cc25f4176df) · workflow
> ### Verdict 2: Rework it
> Execution ●●○ · Fit ●○○ · Coverage ●●● · Evidence n.a.
>
> - Jev Search uses Jev to choose a search configuration and rank Search1API results.
> - It batches typed judgments, keeps thresholds in code, and lets readers override filters.
> - Ungated Choice decisions and untested search quality limit its reliability.
>
> **Top fix:** Gate window, keyword and entity Choice actions on confidence; fall back to a wider window or original request when uncertain.

## What holds it back

- **Structured state** (F3): Result objects omit IDs although result questions address array positions; `results` from a lane reaches ranking ([`src/lib/typesafe.ts:426-444`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L426-L444)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Measured in the workflow** (F7): Tests use mocked Jev answers; no measured task accuracy, cost or latency is reported ([`test/pipeline.test.ts:16-42`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L16-L42), [`README.md:51`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L51)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Options cover every case, no overlap** (F8): Original and stripped query candidates overlap for “New papers on speculative decoding,” changing search terms ([`src/lib/candidates.ts:80-102`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L80-L102), [`README.md:19`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/README.md#L19)). https://docs.typesafe.ai/primitives/advanced.md
- **An "other" option where needed** (F9): Entity Choice lacks a none option for topic searches without a named entity, affecting IMDb queries ([`src/lib/typesafe.ts:346-351`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L346-L351), [`src/lib/sources.ts:156-165`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L156-L165)). https://docs.typesafe.ai/cookbooks/semantic_find.md
- **Confidence drives action, high or very high** (F11): Window, keyword and entity Choices act without checking confidence ([`src/lib/pipeline.ts:131-142`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L131-L142)). https://docs.typesafe.ai/confidence.md
- **Choice order handled, high** (F13): Window and candidate Choices run once in fixed order before routing ([`src/lib/typesafe.ts:318-360`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L318-L360)). https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md

## Fixes (from reading the code; not tested against it)

1. **F11:** Gate window, keyword and entity Choice actions on confidence; fall back to a wider window or original request when uncertain. Confirm the cutoffs with labeled queries. https://docs.typesafe.ai/confidence.md
2. **F8, F9:** Make candidate options exclusive and add a none case for entity selection; confirm query changes against real searches. https://docs.typesafe.ai/primitives/choice.md
3. **F3:** Add stable IDs to result state and address them explicitly in questions. https://docs.typesafe.ai/concepts/state.md

**Minor:** Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/superagents-lab__jev-search--gpt-6-sol.md)

