[← All ratings](README.md)

> **Fox-Islam/jevlint** at [`582c0b8`](https://github.com/Fox-Islam/jevlint/tree/582c0b8be072fb0d14fcaa5bd72b278205543ed7) · library
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●● · Evidence ●○○
>
> - jevlint imports hosted Jev to inspect query designs and returns lint findings and probe readings to its users.
> - It combines static shape checks with bundled Jev questions and a probe for answer movement.
> - Its measured evidence is uneven across checks, and several checks have no independent positive labels.

## What holds it back

- **Held-out result** (F17): Published corpus readings also guided wording and trigger revisions, without a distinct final holdout ([`docs/evidence.md:113`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L113)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one
- **Fair baseline** (F18): Answer arms compare original and repaired queries, but no alternative linter on the same task ([`docs/evidence.md:376`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L376)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one

**Minor:** Pinned model version (F12); Size limits respected (F14); Data as fields, not templates, low (F20). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/Fox-Islam__jevlint--gpt-6-sol.md)

