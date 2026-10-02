[← All ratings](README.md)

> **kylemclaren/JevPDF** at [`7f23037`](https://github.com/kylemclaren/jevpdf/tree/7f23037096) · workflow
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence n.a.
>
> - JevPDF extracts PDF text locally, then asks Jev one noul per line ("does this line answer the query?") in batches of 16 sharing a page-text state, and ranks and highlights lines by the returned probability.
> - It does this well: narrow self-contained questions, token-limit guards, retries, caching and a near-miss fallback.
> - It claims no measured results and never checks the 0.55 hit threshold against labelled data.

## What holds it back

- **Measured in the workflow** (F7): No precision, recall or latency numbers; README cost and 150-page timing are estimates. ([`README.md:38`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/README.md#L38), [`src/lib/jev-config.ts:28`](https://github.com/kylemclaren/jevpdf/blob/7f23037096/src/lib/jev-config.ts#L28)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)

**Minor:** Pinned model version (F12); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/kylemclaren__jevpdf.md)

