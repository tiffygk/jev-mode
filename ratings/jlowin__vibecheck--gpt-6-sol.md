[← All ratings](README.md)

> **jlowin/vibecheck** at [`1011988`](https://github.com/jlowin/vibecheck/tree/1011988a5c7b71b891d3a022fdbd5745c2a36edb) · library
> ### Verdict 2: Rework it
> Execution ●○○ · Fit ●○○ · Coverage ●●● · Evidence ○○○
>
> - vibecheck is a Python library that sends caller questions and data to Jev as typed Noul, Choice and Score requests.
> - It makes async and sync calls, batching, schema assessment and probability-aware checks accessible through a small API.
> - Broad example wording, bare numeric Score levels, forced Choices and unverified performance claims limit the guidance users can copy.

## What holds it back

- **Atomic questions** (F1): The lead example asks whether unspecified “vibes” are good, with no standard ([`README.md:16`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L16)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Right primitive** (F2): Bare numbered satisfaction levels reach Score without described situations ([`README.md:180`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L180)). https://docs.typesafe.ai/primitives/score
- **Measured in the workflow** (F7): The README’s 100-question token and answer claim has no task evaluation in retained files ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Options cover every case, no overlap** (F8): Basic ticket routing omits non-team messages, and returns and billing can overlap ([`examples/classify/basic.py:27`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/examples/classify/basic.py#L27)). https://docs.typesafe.ai/primitives/advanced
- **An other option where needed** (F9): The README’s first team classifier forces unrelated tickets into three teams ([`README.md:115`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L115)). https://docs.typesafe.ai/primitives/advanced
- **Confidence drives action, low** (F11): A callable handler can be selected and invoked from top Choice without a confidence gate ([`README.md:234`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L234)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Sample size adequate** (F15): “Same answers” for 100 questions lacks a sample of documents or repeated runs ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Held-out result** (F17): The performance claim has no separate held-out run reported ([`README.md:414`](https://github.com/jlowin/vibecheck/blob/1011988a5c7b71b891d3a022fdbd5745c2a36edb/README.md#L414)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Size limits respected (F14); Untrusted text treated as data, low (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/jlowin__vibecheck--gpt-6-sol.md)

