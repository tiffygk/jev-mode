[← All ratings](README.md)

> **kitze/skillbox** at [`cda64ad`](https://github.com/kitze/skillbox/tree/cda64ad3310abe690c6d497352791da4cfeb9a0a) · agent tool
> ### Verdict 4: Use it
> Execution ●●● · Fit ●●● · Coverage ●●○ · Evidence n.a.
>
> - Skillbox sends an agent's task and authorized skill descriptions to hosted Jev for relevance scores.
> - Its bounded catalog, validation, permission recheck and explicit search fallback support dependable recommendations.
> - The score cutoff lacks calibration against real agent outcomes.

## What holds it back

- **Measured in the workflow** (F7): A live benchmark script exists, but no result for real agent loads is recorded ([`scripts/benchmark-recommendations.ts:40`](https://github.com/kitze/skillbox/blob/cda64ad3310abe690c6d497352791da4cfeb9a0a/scripts/benchmark-recommendations.ts#L40)). https://docs.typesafe.ai/cookbooks/skill_suggestion.md

**Minor:** Size limits respected (F14); Non-English handled (F23). These are listed fixes and don't lower the verdict.

[Full rating: every fact, its evidence and the files read →](full/kitze__skillbox--gpt-6-sol.md)

