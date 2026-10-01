[← All ratings](README.md)

> **bnsd55/jevmlx** at [`7e0d746`](https://github.com/bnsd55/jevmlx/tree/7e0d746081b8) · jev replacement
> ### Verdict 1: Replaces Jev, not yet rated
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - jevmlx is a local Apple Silicon engine that scores every option of typed fields from logits in one batched pass, and its server offers a `/v1/systemone` endpoint that accepts Jev's request shape and returns Jev-style typed answers (README.md).
> - It documents its prompt contract, calibration bundle and abstention rule, and benchmarks against TypeSafe's public eval pages.
> - It makes no hosted Jev call and does not claim to be or call Jev (README.md: "Not affiliated with TypeSafe AI"), so it routes to 1r until a replacement track exists.

## What holds it back

- **Calls hosted Jev** (F0): No hosted call; a local MLX model scores options and the server mimics Jev's request shape (`README.md`, `js/tests/fixtures/systemone-200.json`). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md

[Full rating: every fact, its evidence and the files read →](full/bnsd55__jevmlx.md)

