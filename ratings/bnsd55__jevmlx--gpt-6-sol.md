[← All ratings](README.md)

> **bnsd55/jevmlx** at [`7e0d746`](https://github.com/bnsd55/jevmlx/tree/7e0d746081b8) · jev replacement
> ### Not rated yet: replaces Jev
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - jevmlx serves Jev-style typed answers using a local Apple Silicon model and exposes a System One-compatible endpoint.
> - It supports boolean, choice, and ordered-choice outputs with probabilities and a documented benchmark workflow.
> - Its replacement use falls outside the current Jev integration rubric.

## What holds it back

- **Calls hosted Jev** (F0): `jevmlx/api.py` invokes the local engine; `benchmarks/typesafe/fetch.py` downloads public evaluation pages, not hosted answers ([`jevmlx/api.py:541`](https://github.com/bnsd55/jevmlx/blob/7e0d746081b8/jevmlx/api.py#L541); [`benchmarks/typesafe/fetch.py:93`](https://github.com/bnsd55/jevmlx/blob/7e0d746081b8/benchmarks/typesafe/fetch.py#L93)). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md

[Full rating: every fact, its evidence and the files read →](full/bnsd55__jevmlx--gpt-6-sol.md)

