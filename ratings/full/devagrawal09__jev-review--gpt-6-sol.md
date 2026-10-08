[← Summary](../devagrawal09__jev-review--gpt-6-sol.md)

# jev-review: full rating

**Verdict 3, Use with a fix** · workflow · rated 2026-10-06 at [`31f8960`](https://github.com/devagrawal09/jev-review/tree/31f89602797fb7bea007f8a480bf368bf564954e) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jev Review screens changed files and complete JavaScript or TypeScript source, then uses Jev to locate and classify potential findings. It batches five typed risk questions and keeps thresholds in code. Overlapping profile categories and severity actions without confidence gates limit its reliability as a review workflow.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Change and codebase reviewers send typed questions through TypeSafeClient ([`src/review/judgments.ts:38`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38), [`src/review/codebase-judgments.ts:47`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L47)). |
| Measured in the workflow (F7) | **no.** README calls this an experiment and reports no task accuracy, cost, or latency numbers ([`README.md:85`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L85)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Options cover every case, no overlap (F8) | **no.** An authentication route can be both entrypoint and boundary, changing its displayed profile category ([`src/review/codebase-judgments.ts:30`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L30)). https://docs.typesafe.ai/primitives/advanced.md |
| Confidence drives action, low (F11) | **no.** Severity alone requests changes and triggers routing; its confidence is recorded but never gates either action ([`src/review/judgments.ts:225`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L225), [`src/review/judgments.ts:254`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L254)). https://docs.typesafe.ai/concepts/confidence.md |
| Pinned model version (F12) | **no.** TypeSafeClient is created without a model ID despite fixed probability and score cutoffs ([`src/review/judgments.ts:23`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L23), [`src/domain/config.ts:5`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L5)). https://docs.typesafe.ai/models.md |
| Size limits respected (F14) | **no.** Full patches and changed tests enter screening state without a size guard ([`src/review/judgments.ts:39`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L39)). https://docs.typesafe.ai/models.md |
| Data as fields, not templates, high or low (F20) | **no.** Candidate line numbers are spliced into Choice option text in both modes ([`src/review/judgments.ts:187`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L187), [`src/review/codebase-judgments.ts:212`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L212)). https://docs.typesafe.ai/primitives/advanced.md |
| Untrusted text treated as data, high or low (F22) | **no.** Repository source enters state without an untrusted-source flag or visible steering test ([`src/review/codebase-judgments.ts:49`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L49)). https://docs.typesafe.ai/model-jaggedness/jev-1.13.md |
| Non-English handled (F23) | **no.** Whole-repository scan accepts arbitrary source text, but no translation or multilingual evaluation is documented ([`src/review/codebase-judgments.ts:46`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L46)). https://docs.typesafe.ai/models.md |

<details>
<summary><b>What passes (10) and doesn't apply (5)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each screening question targets one concern category; later questions separately select evidence, mechanism, impact, and owner ([`src/review/judgments.ts:41`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L41), [`src/review/judgments.ts:180`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L180)). |
| Right primitive (F2) | yes. Binary concern screens use Noul, named categories use Choice, and ordered impact uses a described Score ([`src/review/judgments.ts:41`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L41), [`src/review/judgments.ts:203`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L203), [`src/review/judgments.ts:215`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L215)). |
| Structured state (F3) | yes. Named file, tests, concern, and candidate fields are supplied as JSON; questions point to them ([`src/review/judgments.ts:39`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L39), [`src/review/judgments.ts:174`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L174)). |
| Batching (F4) | yes. Five independent screens share one request per patch or source region; dependent investigation follows in later calls ([`src/review/judgments.ts:38`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38), [`src/review/codebase-judgments.ts:47`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L47)). |
| Thresholds in code (F5) | yes. Screening, location confidence, routing, and blocking cutoffs are named constants ([`src/domain/config.ts:5`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L5)). |
| No invented values (F6) | yes. Code computes probabilities' maxima and compares cutoffs; Jev judges concerns and chooses supplied candidates ([`src/review/workflow.ts:64`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/workflow.ts#L64), [`src/review/judgments.ts:180`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L180)). |
| An other option where needed (F9) | yes. Evidence selections include noMatch, mechanism choices include other and noIssue, and owner choices include maintainer ([`src/review/judgments.ts:189`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L189), [`src/domain/config.ts:40`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L40)). |
| Evidence recorded evenly (F10) | yes. Candidate regions and hunks share a uniform structure; no candidate gets extra supporting claims ([`src/review/codebase-judgments.ts:198`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L198), [`src/review/judgments.ts:173`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L173)). |
| Choice order handled, low (F13) | n.a.. All Choice results stay in a local report for human review ([`src/review/workflow.ts:110`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/workflow.ts#L110)). |
| Sample size adequate (F15) | n.a.. No numerical result claim appears in the README ([`README.md:85`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L85)). |
| Independent labels (F16) | n.a.. No result labels or benchmark are reported ([`README.md:85`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L85)). |
| Held-out result (F17) | n.a.. No tuned or held-out result is reported ([`README.md:85`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L85)). |
| Fair baseline (F18) | n.a.. No comparative performance claim is reported ([`README.md:85`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L85)). |
| Typed answers read directly (F19) | yes. The workflow reads `.noul`, `.choice`, `.score`, and `.confidence` fields directly ([`src/review/judgments.ts:127`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L127), [`src/review/judgments.ts:195`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L195), [`src/review/judgments.ts:222`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L222)). |
| No instructions in the state (F21) | yes. Source, tests, concern metadata, and candidate evidence are data; judgment directions sit in questions ([`src/review/codebase-judgments.ts:198`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L198), [`src/review/codebase-judgments.ts:205`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L205)). |

</details>

## Scores

- Execution 2 of 3: Core questions are typed, structured, and batched, while overlapping Choice options and ungated severity actions remain; F1-F6 and F19 yes, F8 and F11 no.
- Fit 2 of 3: The workflow uses Jev for bounded judgments and batches shared state, but severity confidence does not gate actions; F2, F4, and F11.
- Coverage 3 of 3: Both promised review modes screen all five stated concern categories and follow selected evidence; README scope and F1-F6.
- Evidence n.a.: The project makes no measured-result claim; F7 and F15-F18.

## Why this verdict

Verdict 3, Use with a fix: F8 and F11 cap the verdict despite strong question structure and coverage. The local report keeps all decisions low stakes, so ungated severity does not trigger the high-stakes fatal-flaw rule. There is no public task evaluation to support stronger performance claims.

<details>
<summary><b>Files read (16)</b></summary>

- .env.example -- read
- README.md -- read
- package.json -- read
- scripts/check-dependencies.ts -- read
- src/cli/review-changes.ts -- read
- src/cli/review-codebase.ts -- read
- src/cli/save-changes.ts -- read
- src/cli/save-codebase.ts -- read
- src/dashboard/public/app.js -- read
- src/domain/config.ts -- read
- src/domain/types.ts -- read
- src/review/changes.ts -- read
- src/review/codebase-judgments.ts -- read
- src/review/codebase.ts -- read
- src/review/judgments.ts -- read
- src/review/workflow.ts -- read

</details>
