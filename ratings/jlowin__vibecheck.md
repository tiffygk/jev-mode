[← All ratings](README.md)

> **jlowin/vibecheck** at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · library
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ○○○
>
> - vibecheck is a Python library that turns check, classify, label, score and assess calls into typed Noul, Choice and Score requests to Jev and returns plain Python values.
> - It does well on batching, structured state, probability thresholds with an unsure band, and reading typed answers directly.
> - Bare numeric Score levels, an unmeasured batching claim, no state size guard and a spliced example question hold it back.
>
> **Top fix:** Describe Score levels as situations instead of bare numbers in [`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`README.md:430`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L430) and [`examples/score/numeric_levels.py:26`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/score/numeric_levels.py#L26), using the dict form.

## What holds it back

- **Right primitive** (F2): check is Noul, classify Choice, score Score, but bare `range(1, 6)` levels go as "1".."5" ([`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`src/vibecheck/_plans.py:364`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L364)). primitives/score
- **Measured in the workflow** (F7): One unlinked batching figure, no accuracy numbers, and tests use FakeBackend only ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). how-to-build-with-system-one
- **Sample size adequate** (F15): The batching claim names one 5,000-token document and 100 questions, with no runs or files to check ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). how-to-build-with-system-one

## Fixes (from reading the code; not tested against it)

1. F2: describe Score levels as situations instead of bare numbers in [`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`README.md:430`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L430) and [`examples/score/numeric_levels.py:26`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/score/numeric_levels.py#L26), using the dict form. Source: [`primitives/score`](https://docs.typesafe.ai/primitives/score).
2. F7, F15: measure the batching claim at [`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414) on a stated sample and report the numbers, or drop the figure. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence).
3. F14: guard or report state size so a whole database row stays under 32k tokens per request. Source: [`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

**Minor:** Size limits respected (F14); Data as fields, not templates (F20); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/jlowin__vibecheck.md)

