[← All ratings](README.md)

> **superagents-lab/jev-search** at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe09d1ccfe720f38998f36cc25f4176df) · workflow
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence n.a.
>
> - Jev Search sends each request to hosted Jev to pick a time window, sources and the engine query, then scores every returned result's relevance with one Noul each.
> - It handles provider fallback, streaming, source overrides and result ordering carefully, and a user can override every inferred filter.
> - It has no measurement of whether Jev's choices or scores are right, ignores Choice confidence, and never lets Jev's uncertainty change an action beyond fixed cut-offs.
>
> **Top fix:** Gate the window, query and entity picks on [`confidence`](https://docs.typesafe.ai/confidence); below a floor, use "any time" and the original request.

## What holds it back

- **Measured in the workflow** (F7): No accuracy, cost or latency numbers on the search task; every test stubs Jev's answers ([`test/pipeline.test.ts:24`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/test/pipeline.test.ts#L24)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)
- **Options cover every case, no overlap** (F8): Window has no option for "last 3 months", which the code expects; 30d would drop older rows ([`src/lib/sources.ts:219`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L219), [`src/lib/candidates.ts:10`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/candidates.ts#L10)). [`primitives/choice`](https://docs.typesafe.ai/primitives/choice)
- **An "other" option where needed** (F9): Entity Choice has no none-of-these; a described movie with no title still sends a forced pick to IMDb ([`src/lib/typesafe.ts:346`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/typesafe.ts#L346), [`src/lib/sources.ts:174`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/sources.ts#L174)). [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced)
- **Confidence drives action, low** (F11): Source Noul is gated at 0.6, but window and query Choice picks apply at any confidence ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe09d1ccfe720f38998f36cc25f4176df/src/lib/pipeline.ts#L140)). [`confidence`](https://docs.typesafe.ai/confidence)

## Fixes (from reading the code; not tested against it)

1. **F11:** Gate the window, query and entity picks on [`confidence`](https://docs.typesafe.ai/confidence); below a floor, use "any time" and the original request. Confirm the floor with labeled queries. [`confidence`](https://docs.typesafe.ai/confidence), [`patterns/confidence-routing`](https://docs.typesafe.ai/patterns/confidence-routing)
2. **F8:** Add windows for spans between 30 days and any time, or ask recency as independent Nouls, so "last 3 months" is not forced into 30d. Confirm with data. [`primitives/choice`](https://docs.typesafe.ai/primitives/choice)
3. **F9:** Add a none-of-these option to the entity Choice, worded unlike the candidates, and fall back to the keyword query. [`primitives/choice`](https://docs.typesafe.ai/primitives/choice)

**Minor:** Pinned model version (F12); Data as fields, not templates, high or low (F20); Untrusted text treated as data, high or low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/superagents-lab__jev-search.md)

