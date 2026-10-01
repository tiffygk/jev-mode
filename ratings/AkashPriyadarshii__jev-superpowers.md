[← All ratings](README.md)

> **AkashPriyadarshii/jev-superpowers** at [`4e5f569`](https://github.com/AkashPriyadarshii/jev-superpowers/tree/4e5f569653a4fdb321afe1ef7f4a3c23ef7130a9) · jev replacement
> ### Verdict 1: False marketing: Jev in name only
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - The repo is a skill pack, three hooks and a local bridge, `scripts/serve-laya.py`, that accepts Jev's `/v1/systemone` request format and answers Choice, Score and Noul questions by word overlap and keyword lists.
> - Its skills and hooks are clearly written and put a stop on failures, but no code in the repo creates a TypeSafe client, posts to `api.typesafe.ai` or names a gateway model ID.
> - The README says Jev gates every decision and quotes latency, cost and hallucination figures with no capture behind them.
>
> **Top fix:** Failed F0: either make a traced call to hosted Jev through the SDK or `api.typesafe.ai` and let its typed answers drive a decision, or say plainly in the README that this repo does not call Jev and the bridge is a keyword stand-in ([`introduction/quickstart`](https://docs.typesafe.ai/introduction/quickstart), `sdk`).

## What holds it back

- **Calls hosted Jev** (F0): `jev_callsites.py` flags no file; the seven mentions are docs. `hooks/pre-commit:20` only runs the external `git jev check` binary. (`hooks/pre-commit:20`) Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md

## Fixes (from reading the code; not tested against it)

1. Failed F0: either make a traced call to hosted Jev through the SDK or `api.typesafe.ai` and let its typed answers drive a decision, or say plainly in the README that this repo does not call Jev and the bridge is a keyword stand-in ([`introduction/quickstart`](https://docs.typesafe.ai/introduction/quickstart), `sdk`).

[Full rating: every fact, its evidence and the files read →](full/AkashPriyadarshii__jev-superpowers.md)

