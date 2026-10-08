[← All ratings](README.md)

> **valentynkit/jev-belay** at [`ef719db`](https://github.com/valentynkit/jev-belay/tree/ef719db7eaad) · workflow
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - jev-belay is a Claude Code Stop hook that sends four batched questions to Jev after a local check finds edits without a fresh passing test, build or lint run.
> - It keeps transcript parsing and thresholds in code, makes one hosted call for a narrow judgment, and reports its ablation and operating costs.
> - Overlapping `outcome` options can alter the block veto, while its claimed error rate rests on a small slice used for threshold selection.
>
> **Top fix:** Make `outcome` options exclusive, or use independent Nouls for partial progress and a blocker; confirm on ambiguous stops that the veto is stable (F8, [`belay.mjs:443-448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L443-L448)).

## What holds it back

- **Options cover every case, no overlap** (F8): A partly completed task can also report a blocker; either pick changes veto ([`belay.mjs:443-448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L443-L448)). https://docs.typesafe.ai/primitives/advanced.md
- **Sample size adequate** (F15): One wrong block in 100 cannot establish the claimed under-2% error rate ([`demo/README.md:239-257`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L257)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Held-out result** (F17): The reported threshold and result use the same 100-stop audit ([`tools__measure.mjs:201-245`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools__measure.mjs#L201-L245)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Fair baseline** (F18): Comparison is Jev wording alone, without a rules or separate-model alternative ([`demo/README.md:225-236`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L225-L236)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md

## Fixes (from reading the code; not tested against it)

1. Make `outcome` options exclusive, or use independent Nouls for partial progress and a blocker; confirm on ambiguous stops that the veto is stable (F8, [`belay.mjs:443-448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L443-L448)). [TypeSafe Choice guidance](https://docs.typesafe.ai/primitives/choice.md).
2. Hold out a disjoint labeled set before tuning 0.70, then report its wrong-block count with an interval; the present 100 stops and one error cannot establish under 2% (F15, F17, [`demo/README.md:239-257`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L257)). [TypeSafe confidence guidance](https://docs.typesafe.ai/confidence.md).
3. Compare the same stops with a practical rules or LLM alternative to establish the added value of this design (F18, [`demo/README.md:225-236`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L225-L236)). [TypeSafe self-consistency example](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md).

**Minor:** Untrusted text treated as data, low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/valentynkit__jev-belay--gpt-6-sol.md)

