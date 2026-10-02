[← All ratings](README.md)

> **typesafe-ai/system-one-adapter-python** at [`e1d4cc9`](https://github.com/typesafe-ai/system-one-adapter-python/tree/e1d4cc9382) · jev replacement
> ### Not rated yet: replaces Jev
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - This Python package imitates TypeSafe's `system_one` API by sending the same Noul, Choice and Score questions to OpenAI, Anthropic or Gemini models and returning typed answers.
> - It validates output against a per-request schema, retries malformed output, normalizes probabilities and derives confidence, and its README says it is for comparing TypeSafe against an LLM.
> - It never calls hosted Jev and does not claim to, so it is routed 1r until a replacement track exists.

## What holds it back

- **Calls hosted Jev** (F0): Requests go to LLM provider SDKs, never TypeSafe ([`src/system_one_adapter/providers/openai.py:153`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc9382/src/system_one_adapter/providers/openai.py#L153)). Flagged files `src/system_one_adapter/__init__.py` `src/system_one_adapter/_client.py` `src/system_one_adapter/_response.py` `src/system_one_adapter/_schema.py` `src/system_one_adapter/providers/anthropic.py` `src/system_one_adapter/providers/base.py` `src/system_one_adapter/providers/gemini.py` `src/system_one_adapter/providers/openai.py` `tests/test_gemini_transports.py` `tests/test_openai_transports.py` `tests/test_provider_nonanswers.py` `tests/test_provider_retries.py` `tests/utils/test_error_handling.py` import only SDK types and errors, no client. https://docs.typesafe.ai/llms.txt

[Full rating: every fact, its evidence and the files read →](full/typesafe-ai__system-one-adapter-python.md)

