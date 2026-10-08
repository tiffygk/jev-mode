[← All ratings](README.md)

> **qkal/Canny** at [`f2c5e53`](https://github.com/qkal/Canny/tree/f2c5e53779445d60dc4a09d2dbced2308fccb820) · workflow
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - Canny supervises coding-agent sessions with deterministic checks and uses hosted Jev for completion-claim and project-rule judgments.
> - Its Noul questions are narrow, fielded, batched by change, cached, and acted on only at conservative thresholds.
> - Its published agent comparison does not validate live Jev judgments, and requests lack a total size guard.

## What holds it back

- **Measured in workflow** (F7): Published agent A/B measures Canny, while Jev behavior has only mocked endpoint tests ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271); [`test/jev.test.ts:8-21`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/test/jev.test.ts#L8-L21)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Sample size adequate** (F15): The 25-pair agent result cannot establish Jev judgment accuracy because it reports no live Jev judgments ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Independent labels** (F16): The A/B task tests label task completion, but no independent labels audit Jev’s two judgments ([`bench/run.mjs:93-106`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/bench/run.mjs#L93-L106); [`README.md:273`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L273)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Held-out result** (F17): The same five tasks informed gate changes and the later agent run; Jev has no held-out result ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271); [`CHANGELOG.md:10-13`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/CHANGELOG.md#L10-L13)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Size limits respected (F14); Untrusted text treated as data (F22); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/qkal__Canny--gpt-6-sol.md)

