[← All ratings](README.md)

> **typesafe-ai/system-one-adapter-python** at [`e1d4cc9`](https://github.com/typesafe-ai/system-one-adapter-python/tree/e1d4cc938204b22fc5a3c3aca7044072fe3f712d) · jev replacement
> ### Not rated yet: replaces Jev
> Execution n.a. · Fit n.a. · Coverage n.a. · Evidence n.a.
>
> - The adapter accepts TypeSafe `system_one` questions and produces TypeSafe-shaped answers using other LLM providers.
> - It supports probability and discrete answers, schema validation, and provider error traces.
> - Its replacement design falls under the pending replacement track rather than the Jev integration scores.

## What holds it back

- **Calls hosted Jev** (F0): src/system_one_adapter/_response.py,src/system_one_adapter/_schema.py,src/system_one_adapter/_utils/error_handling.py,src/system_one_adapter/providers/anthropic.py,src/system_one_adapter/providers/base.py,src/system_one_adapter/providers/gemini.py,src/system_one_adapter/providers/openai.py are SDK references, not hosted calls ([`src/system_one_adapter/_client.py:496`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc938204b22fc5a3c3aca7044072fe3f712d/src/system_one_adapter/_client.py#L496), [`src/system_one_adapter/providers/openai.py:153`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc938204b22fc5a3c3aca7044072fe3f712d/src/system_one_adapter/providers/openai.py#L153)). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md

[Full rating: every fact, its evidence and the files read →](full/typesafe-ai__system-one-adapter-python--gpt-6-sol.md)

