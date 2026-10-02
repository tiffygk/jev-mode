[← All ratings](README.md)

> **altryne/Jevify** at [`11f36f8`](https://github.com/altryne/jevify/tree/11f36f8d54) · agent tool
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - Jevify is an installable agent skill that teaches an agent to hand bulk semantic judgments to Jev, with a standard-library scanner that sends text chunks to hosted Jev as Score questions and returns a ranked reading shortlist to the agent.

## What holds it back

- **Measured in the workflow** (F7): Only latency and token counts on 24 synthetic records, with no accuracy on any labeled set. ([`references/validation-2026-09-21.md:25`](https://github.com/altryne/jevify/blob/11f36f8d54/references/validation-2026-09-21.md#L25)). docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Untrusted text treated as data, high or low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/altryne__jevify.md)

