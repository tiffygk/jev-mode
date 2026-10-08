[← All ratings](README.md)

> **kylemclaren/jevpdf** at [`7f23037`](https://github.com/kylemclaren/jevpdf/tree/7f230370961c4a8e2f8b19c1729085b852124448) · display
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●● · Coverage ●●● · Evidence ○○○
>
> - JevPDF asks hosted Jev whether each extracted PDF line answers a reader's query, then displays ranked highlights.
> - Its narrow Noul questions, batching, local extraction, and visible confidence support the search task.
> - The fixed thresholds and lack of measured retrieval quality limit confidence in its matches.

## What holds it back

- **Structured state** (F3): Page lines are joined into untagged `page_text`; questions repeat text without pointing to line IDs ([`src/lib/jev.ts:93`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/src/lib/jev.ts#L93)). https://docs.typesafe.ai/concepts/state
- **Measured in the workflow** (F7): The README claims speed and cost, but provides no task measurements ([`README.md:47`](https://github.com/kylemclaren/jevpdf/blob/7f230370961c4a8e2f8b19c1729085b852124448/README.md#L47)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/kylemclaren__jevpdf--gpt-6-sol.md)

