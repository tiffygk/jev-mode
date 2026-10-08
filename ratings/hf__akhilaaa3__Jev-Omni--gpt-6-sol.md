[← All ratings](README.md)

> **Jev-Omni** at [`5addda8`](https://huggingface.co/akhilaaa3/Jev-Omni/tree/5addda86ddee081a68fb067477ea100c221b8917) · jev replacement
> ### Not rated yet: replaces Jev
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - Jev-Omni is a local multimodal classifier that returns probabilities for caller-supplied options without calling hosted Jev.
> - Its loader, example, and model card show a usable typed-decision interface.
> - The current rubric assigns independent replacements a placeholder verdict until their own track exists.

## What holds it back

- **Calls hosted Jev** (F0): `jev_omni.py` loads local model weights and runs local inference, not a TypeSafe client ([`files/jev_omni.py:136`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee081a68fb067477ea100c221b8917/files/jev_omni.py#L136), [`files/jev_omni.py:103`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee081a68fb067477ea100c221b8917/files/jev_omni.py#L103)). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md

[Full rating: every fact, its evidence and the files read →](full/hf__akhilaaa3__Jev-Omni--gpt-6-sol.md)

