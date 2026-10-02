[← All ratings](README.md)

> **superagents-lab/jev-search** at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe0) · workflow
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence n.a.
>
> - Jev Search sends each request to Jev as one set of typed questions that picks a time window, sources and a query, then scores every result as a yes/no relevance question.
> - It does this well: code proposes the query candidates and Jev only selects, the state is small, lanes are scored in parallel and streamed, and three Jev providers fall back on outage.
> - It is held back by ignoring every confidence value Jev returns, by pinning no model version, and by publishing no measured results.
>
> **Top fix:** Confidence ignored on the window and query Choices ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L140)): fall back to `any` and to `c0` below a confidence constant ([`confidence`](https://docs.typesafe.ai/confidence)).

## What holds it back

- **Measured in the workflow** (F7): No accuracy numbers on its task; tests mock Jev and the README calls scores model judgments (`README.md`, `test/pipeline.test.ts`). docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Confidence drives action, low** (F11): Window and query Choices act at any probability; relevance (0.3) and source (0.6) gates hold ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L140)). docs.typesafe.ai/confidence

## Fixes (from reading the code; not tested against it)

1. F11, confidence ignored on the window and query Choices ([`src/lib/pipeline.ts:131`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L131), [`src/lib/pipeline.ts:140`](https://github.com/superagents-lab/jev-search/blob/36d3723fe0/src/lib/pipeline.ts#L140)): fall back to `any` and to `c0` below a confidence constant ([`confidence`](https://docs.typesafe.ai/confidence)).
2. F7, nothing measured: label real requests and report source-choice and relevance precision and recall ([`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)). Needs data to confirm.
3. F12, model alias: pin the versioned model once thresholds are tuned ([`models`](https://docs.typesafe.ai/models)).

**Minor:** Pinned model version (F12); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/superagents-lab__jev-search.md)

