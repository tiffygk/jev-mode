[← All ratings](README.md)

> **valentynkit/jev-belay** at [`ef719db`](https://github.com/valentynkit/jev-belay/tree/ef719db7eaad) · workflow
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - jev-belay is a Claude Code Stop hook that, only when files changed and no check passed since, sends one Jev request of four questions about the closing message and blocks the stop when it reads as an unverified done.
> - It keeps counting, thresholds and the evidence veto in code, pins `jev-1.13.0`, and reports AUROC with intervals on 100 labeled stops against a wording-only baseline.
> - Its 0.70 cutoff was swept on the same 100 stops that report the block counts, labels come from one model, and the injection and non-English checks are skipped by default.

## What holds it back

- **Held-out result** (F17): The 0.70 cut-off was swept on the same 100 stops that report its caught and wrong-block counts ([`demo/README.md:239-251`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L251), [`CHANGELOG.md:56-60`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/CHANGELOG.md#L56-L60)). cookbooks/autoresearch

**Minor:** Untrusted text treated as data, high or low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/valentynkit__jev-belay.md)

