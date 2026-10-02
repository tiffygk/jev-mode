[← All ratings](README.md)

> **RileyCarney/JevTools** at [`7f6907b`](https://github.com/RileyCarney/JevTools/tree/7f6907b461) · demo
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - JevTools sends review and topic text to hosted Jev through OpenRouter or the TypeSafe API, with six and four typed questions per request, and shows the answers plus a rule-based suggested action in a CLI and a local dashboard.
> - It decomposes questions well, keeps policy in code and gates on Choice confidence, though a mock mode replaces Jev for offline runs.
> - Nothing acts on the suggestions, no thresholds or results were checked on data, and the README latency figures disagree with each other and with the code.
>
> **Top fix:** Make the topic options exclusive and exhaustive, or switch to independent Nouls where topics can co-occur, and confirm the change with data (F8; [`primitives`](https://docs.typesafe.ai/primitives) Choice page).

## What holds it back

- **Measured in the workflow** (F7): Only a latency figure is claimed, 300 ms here and 287 elsewhere, with no recorded runs ([`README.md:17`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/README.md#L17)). Parallel questions cookbook
- **Options cover every case, no overlap** (F8): Topic options overlap: medicine sits in science and health, environmental policy in environment and politics ([`jev_demo.py:1136-1140`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/jev_demo.py#L1136-L1140)). Primitives advanced page
- **Sample size adequate** (F15): The latency claim names no run count, and sources disagree on its value ([`tests/test_jev_demo.py:247`](https://github.com/RileyCarney/JevTools/blob/7f6907b461/tests/test_jev_demo.py#L247)). Launch post and evals page

## Fixes (from reading the code; not tested against it)

1. Make the topic options exclusive and exhaustive, or switch to independent Nouls where topics can co-occur, and confirm the change with data (F8; [`primitives`](https://docs.typesafe.ai/primitives) Choice page).
2. Add an evaluation: label a sample of reviews and paragraphs, report precision and recall at the chosen thresholds, and replace the 300 and 287 ms figures with recorded runs that state how many (F7, F15; [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence), TypeSafe's workflow evals).
3. After evaluating, calibrate the thresholds or revise the questions for the misses, then re-measure (closes_loop none; [`confidence`](https://docs.typesafe.ai/confidence), [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery)).

**Minor:** Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/RileyCarney__JevTools.md)

