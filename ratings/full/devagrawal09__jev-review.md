[← Summary](../devagrawal09__jev-review.md)

# jev-review: full rating

**Verdict 3, Use with a fix** · workflow · rated 2026-09-30 at [`31f8960`](https://github.com/devagrawal09/jev-review/tree/31f89602797fb7bea007f8a480bf368bf564954e) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

It runs a staged code review: five Noul risk screens per file or 160-line region, then evidence-hunk, mechanism, severity and owner questions for the top 8 flagged signals. Calls are narrow with explicit options, thresholds live in one config file in code, and confidence gates the evidence step. It never checks its own results, pins no model, and its saved findings only inform a dashboard.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Twelve client.systemOne calls in two files: screening, profiling, evidence, mechanism, severity, routing ([`src/review/judgments.ts:38`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38)) |
| Measured in the workflow (F7) | **no.** No accuracy, precision or cost numbers on any codebase; README calls it an experiment ([`README.md:78`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L78)). concepts/how-to-build-with-system-one |
| Evidence recorded evenly (F10) | **no.** Earlier Jev conclusions (screening probabilities, suspectedConcern with probability) go into later states as facts ([`src/review/judgments.ts:140`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L140)). concepts/state |
| Size limits respected (F14) | **no.** Whole patches and whole files go into profile state with no token guard, only a 20MB git buffer ([`src/adapters/git.ts:14`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/adapters/git.ts#L14)). models |
| Untrusted text treated as data (F22) | **no.** Reviewed code from any repo enters state unflagged and no injection test exists ([`src/adapters/git.ts:40`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/adapters/git.ts#L40)). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No test or note on non-English source comments or identifiers ([`README.md:1`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/README.md#L1)). models |

<details>
<summary><b>What passes (12) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each Noul tests one concern against file.patch with focus and ignore lists; one Choice or Score per property ([`src/review/judgments.ts:38`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38)) |
| Right primitive (F2) | yes. Noul for yes/no concerns, Choice for named options, Score for severity and priority with situation-worded levels ([`src/domain/config.ts:98`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L98)) |
| Structured state (F3) | yes. Named fields, hunk and region IDs, questions pointing at paths such as file.patch ([`src/review/judgments.ts:173`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L173)) |
| Batching (F4) | yes. Five screens share one request, profile pair too; mechanism and severity are separate requests, but noIssue gates severity ([`src/review/judgments.ts:210`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L210)) |
| Thresholds in code (F5) | yes. Screen 0.7, route 1.5, blocking 2, location confidence 0.55 are named constants ([`src/domain/config.ts:5`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L5)) |
| No invented values (F6) | yes. Code splits hunks and regions and picks tests; Jev only judges or picks among supplied candidates ([`src/review/codebase-judgments.ts:271`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/codebase-judgments.ts#L271)) |
| Options cover every case, no overlap (F8) | yes. Mechanism, owner and role sets each carry a catch-all; entrypoint and boundary can overlap but only change a display label ([`src/domain/config.ts:70`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L70)) |
| An "other" option where needed (F9) | yes. Evidence has noMatch, mechanisms have other and noIssue, owners have maintainer, change types have routine ([`src/domain/config.ts:75`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L75)) |
| Confidence drives action, low (F11) | yes. Screen probability gates follow-up and location confidence gates evidence; mechanism and severity confidences are recorded, not gating ([`src/review/workflow.ts:64`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/workflow.ts#L64)) |
| Pinned model version (F12) | n.a.. Thresholds were never tuned on data and no model ID appears ([`src/domain/config.ts:5`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/domain/config.ts#L5)) |
| Choice order handled, low (F13) | n.a.. Every Choice decision is low stakes ([`src/review/judgments.ts:196`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L196)) |
| Sample size adequate (F15) | n.a.. No results claimed. |
| Independent labels (F16) | n.a.. No results claimed. |
| Held-out result (F17) | n.a.. No results claimed. |
| Fair baseline (F18) | n.a.. No results claimed. |
| Typed answers read directly (F19) | yes. Code reads .noul, .choice, .score and .confidence fields ([`src/review/judgments.ts:196`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L196)) |
| Data as fields, not templates (F20) | yes. Patch and source go in state fields; only hunk IDs and line numbers enter option text ([`src/review/judgments.ts:187`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L187)) |
| No instructions in the state (F21) | yes. State holds file, patch, probabilities and concern definitions; directions sit in the questions ([`src/review/judgments.ts:166`](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L166)) |

</details>

## Scores

- Execution 2 of 3: F1-F6 all hold, but F10 fails because earlier Jev conclusions (screening probabilities, suspected concern) go into later states as facts.
- Fit 2 of 3: one mismatch; primitives and batching fit, but the mechanism noIssue drop and the severity cut-off ignore the recorded confidence (F11).
- Coverage 3 of 3: both review modes, all five concern screens, test context, evidence selection, thresholds and routing the README promises all run (F0).
- Evidence n.a.: it claims no results and says it is an experiment (F7 no; F15-F18 n.a.).

## Why this verdict

It is a 3, not a 4, because F10 fails: screening probabilities and the suspected concern, both earlier Jev conclusions, enter later states as facts, and that caps the verdict. Questions are atomic, typed, batched and gated by thresholds in code, and no fatal flaw applies. The F11 call is borderline: the screen and location confidence gate, but the mechanism drop and the severity cut-off ignore confidence. Nothing is measured, so Evidence is n.a. and the loop is open.

## Fixes (from reading the code; not tested against it)

1. F10: ask each stage over the code itself and its own evidence, and keep the earlier probabilities out of the profile and later states, confirming with data by removing one field at a time and rerunning ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).
2. F14: filter the profile state to relevant fields, split long patches, and keep state plus the longest question under 32k tokens ([`models`](https://docs.typesafe.ai/models), [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13)).
3. F22: flag reviewed code as untrusted, add an injection-check Noul, and test adversarial patches ([`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13); [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)).
4. F7: label a sample of reviews and report precision and recall at 0.7; then calibrate or revise from the results ([`confidence`](https://docs.typesafe.ai/confidence); [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence)).
5. F23: test on non-English comments and identifiers, or add a translation beside them ([`concepts/state`](https://docs.typesafe.ai/concepts/state)).

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
