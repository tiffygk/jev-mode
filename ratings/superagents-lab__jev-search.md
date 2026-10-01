[← All ratings](README.md)

> **superagents-lab/jev-search** at [`36d3723`](https://github.com/superagents-lab/jev-search/tree/36d3723fe0) · workflow
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●○ · Coverage ●●● · Evidence n.a.
>
> - Jev Search sends each request to Jev as one set of typed questions that picks a time window, sources and a query, then scores every result as a yes/no relevance question.
> - It does this well: code proposes the query candidates and Jev only selects, the state is small, lanes are scored in parallel and streamed, and three Jev providers fall back on outage.
> - It is held back by ignoring every confidence value Jev returns, by pinning no model version, and by publishing no measured results.

## What holds it back

- **Measured in the workflow** (F7): No accuracy numbers on its task; tests mock Jev and the README calls scores model judgments (`README.md`, `test/pipeline.test.ts`). docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Pinned model version (F12); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/superagents-lab__jev-search.md)

