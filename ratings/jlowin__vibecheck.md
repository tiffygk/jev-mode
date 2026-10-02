[← All ratings](README.md)

> **jlowin/vibecheck** at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · library
> ### Verdict 3: Use with a fix
> Execution ●●○ · Fit ●●○ · Coverage ●●● · Evidence ○○○
>
> - vibecheck is a Python package that turns one function call (`check`, `classify`, `label`, `score`, `assess`, `filter`, `group`) into typed Jev questions and returns a plain Python value.
> - It writes the question wording itself, keeps every probability available, offers a three-way threshold band for unsure answers, and ships a fake backend for tests.
> - It does not use the answer's own confidence field or pin a model by default, ships no calibration tooling, and its README claims accuracy results with no data behind them.
>
> **Top fix:** Switch the README batch example and `examples/score/numeric_levels.py` to described levels, written as situations with no numbers in the level text.

## What holds it back

- **Right primitive** (F2): Verbs map to Noul, Choice and Score, but bare-number levels send "1".."5" as level text, also in README examples ([`src/vibecheck/_plans.py:364`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/src/vibecheck/_plans.py#L364), [`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180), [`README.md:430`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L430)). [`primitives/score`](https://docs.typesafe.ai/primitives/score)
- **Measured in the workflow** (F7): README claims 100 questions matched 100 requests at about 1% of tokens; no test or data is shipped ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)
- **Sample size adequate** (F15): The one results claim covers one 5,000-token document, with no counts or runs shown ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`models`](https://docs.typesafe.ai/models)
- **Fair baseline** (F18): The 100-separate-requests comparison is stated but nothing in the repo reproduces it ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). [`concepts/how-to-build-with-system-one`](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)

## Fixes (from reading the code; not tested against it)

1. **F2 wrong primitive: bare-number Score levels.** Switch the README batch example and `examples/score/numeric_levels.py` to described levels, written as situations with no numbers in the level text. Source: [`primitives/score`](https://docs.typesafe.ai/primitives/score), [`primitives`](https://docs.typesafe.ai/primitives).
2. **F7 nothing measured, with F15 and F18.** Publish the 100-question batching test as a script with its document and counts, or drop the number; report the sample and compare against the separate-request baseline. Confirm with data. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence), [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook).
3. **F22 untrusted text.** Add a README note and a steering-input test for customer text passed as state, with an injection-check Noul before routing. Source: [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13), [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages).

**Minor:** Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/jlowin__vibecheck.md)

