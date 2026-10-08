[← All ratings](README.md)

> **RileyCarney/JevTools** at [`7f6907b`](https://github.com/RileyCarney/JevTools/tree/7f6907b4614914cb47c8b089252832f1f2da485f) · display
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●● · Coverage ●○○ · Evidence ○○○
>
> - The CLI and local dashboard send typed Jev questions for customer-review analysis, topic classification, and arbitrary user questions, then show suggested actions.
> - It batches independent questions, preserves answer probabilities, and computes review scores and routing labels in Python.
> - The labels are suggestions rather than executed handoffs, and the repository shows no labeled live-outcome evaluation.
>
> **Top fix:** Make topic options exclusive, or use independent Nouls when topics co-occur; confirm the resulting routing on real paragraphs.

## What holds it back

- **Thresholds in code** (F5): Review and topic cutoffs are inline literals rather than named constants or config ([`jev_demo.py:1014-1036`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1014-L1036), [`jev_demo.py:1200-1209`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1200-L1209)). https://docs.typesafe.ai/confidence.md
- **Measured in the workflow** (F7): A 300 ms latency constant and mock tests do not show measured live task outcomes ([`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82), [`jev_demo.py:790-819`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L790-L819); [`tests/test_jev_demo.py:163-230`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/tests/test_jev_demo.py#L163-L230)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md
- **Options cover every case, no overlap** (F8): A medical research paragraph fits science and health; that can change expert versus standard labels ([`jev_demo.py:1135-1144`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1135-L1144), [`jev_demo.py:1205-1209`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L1205-L1209)). https://docs.typesafe.ai/primitives/advanced.md
- **Sample size adequate** (F15): The claimed tested latency gives no live run count or captured timings ([`README.md:18`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/README.md#L18); [`jev_demo.py:82`](https://github.com/RileyCarney/JevTools/blob/7f6907b4614914cb47c8b089252832f1f2da485f/jev_demo.py#L82)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md

## Fixes (from reading the code; not tested against it)

1. F8: make topic options exclusive, or use independent Nouls when topics co-occur; confirm the resulting routing on real paragraphs. https://docs.typesafe.ai/primitives.md
2. F7 and F15: label review and topic examples, report sample size and precision/recall at the chosen cutoffs, and capture live task latency. https://docs.typesafe.ai/cookbooks/classification_using_confidence.md
3. F5: move inline cutoffs into named constants and set them from labeled examples. https://docs.typesafe.ai/confidence.md

**Minor:** Pinned model version (F12); Size limits respected (F14); Data as fields, not templates (F20); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/RileyCarney__JevTools--gpt-6-sol.md)

