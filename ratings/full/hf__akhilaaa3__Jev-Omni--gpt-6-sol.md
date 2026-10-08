[← Summary](../hf__akhilaaa3__Jev-Omni--gpt-6-sol.md)

# Jev-Omni: full rating

**Not rated yet: replaces Jev** · jev replacement · rated 2026-10-06 at [`5addda8`](https://huggingface.co/akhilaaa3/Jev-Omni/tree/5addda86ddee081a68fb067477ea100c221b8917) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jev-Omni is a local multimodal classifier that returns probabilities for caller-supplied options without calling hosted Jev. Its loader, example, and model card show a usable typed-decision interface. The current rubric assigns independent replacements a placeholder verdict until their own track exists.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** `jev_omni.py` loads local model weights and runs local inference, not a TypeSafe client ([`files/jev_omni.py:136`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee081a68fb067477ea100c221b8917/files/jev_omni.py#L136), [`files/jev_omni.py:103`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee081a68fb067477ea100c221b8917/files/jev_omni.py#L103)). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md |

## Scores

- n.a. under the replacement placeholder.

## Why this verdict

The project offers Jev-style typed decision answers through its own weights and classifier head. It explicitly describes itself as independent and unaffiliated ([`files/README.md:92`](https://huggingface.co/akhilaaa3/Jev-Omni/blob/5addda86ddee081a68fb067477ea100c221b8917/files/README.md#L92)), and its runtime code has no hosted Jev call. The replacement route yields placeholder code 1r.

<details>
<summary><b>Files read (15)</b></summary>

- files/api.json -- read
- files/assets__medium-accuracy.svg -- read
- files/assets__medium-calibration.svg -- read
- files/chat_template.jinja -- read
- files/config.json -- read
- files/decision_config.json -- read
- files/decision-bench__README.md -- read
- files/example.py -- read
- files/generation_config.json -- read
- files/jev_omni.py -- read
- files/processor_config.json -- read
- files/README.md -- read
- files/requirements.txt -- read
- files/sha256.json -- read
- files/verification.json -- read

</details>
