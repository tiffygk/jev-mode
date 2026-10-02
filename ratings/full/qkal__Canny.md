[← Summary](../qkal__Canny.md)

# Canny: full rating

**Verdict 4, Use it** · workflow · rated 2026-09-30 at [`f2c5e53`](https://github.com/qkal/Canny/tree/f2c5e53779) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

Canny is a hook layer for Claude Code and Codex CLI that asks Jev two kinds of yes/no question: whether the agent's last message claims it is done, and whether an edit breaks a project rule. It keeps facts in code and lets Jev only relax a block or add a note, with 0.9 and 0.1 cut-offs, a content-hash cache and a replayable ledger. The model is the unpinned `jev-latest` alias, and the agent's own text goes in unflagged.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Hook judge POSTs Noul questions with a bearer key to api.typesafe.ai/v1/systemone ([`src/jev.ts:92`](https://github.com/qkal/Canny/blob/f2c5e53779/src/jev.ts#L92)) |
| Pinned model version (F12) | **no.** Default is the `jev-latest` alias under fixed 0.9 and 0.1 cut-offs ([`src/jev.ts:7`](https://github.com/qkal/Canny/blob/f2c5e53779/src/jev.ts#L7)). https://docs.typesafe.ai/models |
| Untrusted text treated as data (F22) | **no.** The agent's own message and diffs go in with no flag; a crafted message could push claims_done to 0.1 ([`src/hook.ts:228`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L228)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** No test or translation for non-English messages or diffs ([`test/jev.test.ts:1`](https://github.com/qkal/Canny/blob/f2c5e53779/test/jev.test.ts#L1)). https://docs.typesafe.ai/models |

<details>
<summary><b>What passes (14) and doesn't apply (6)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each Noul asks one property: whether `message` claims completion, or whether `change` breaks one `rules[i]` ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L39)) |
| Right primitive (F2) | yes. Both are yes/no judgments asked as Noul with true/false criteria ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L39)) |
| Structured state (F3) | yes. State is `{message}` or `{rules, change:{file, added, removed}}`, and questions point at those paths ([`src/hook.ts:206`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L206)) |
| Batching (F4) | yes. All rule questions go in one request per change, and changes run in parallel ([`src/hook.ts:194`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L194)) |
| Thresholds in code (F5) | yes. `YES = 0.9` and `NO = 0.1` are named constants applied in the gate ([`src/jev.ts:12`](https://github.com/qkal/Canny/blob/f2c5e53779/src/jev.ts#L12)) |
| No invented values (F6) | yes. Code counts files, exit codes and checks; Jev only judges a claim or a rule ([`src/hook.ts:240`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L240)) |
| Measured in the workflow (F7) | yes. Bench times 25 Opus 5 pairs with and without Canny (turns, cost, seconds); no Jev answers recorded ([`README.md:245`](https://github.com/qkal/Canny/blob/f2c5e53779/README.md#L245)) |
| Options cover every case (F8) | n.a.. No Choice is used, only Noul. |
| An other option where needed (F9) | n.a.. No Choice is used. |
| Evidence recorded evenly (F10) | n.a.. One message or one diff is judged, with no per-answer evidence list ([`src/hook.ts:206`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L206)) |
| Confidence drives action, low (F11) | yes. Code acts only at 0.9 or above for rules and at 0.1 or below to relax the gate ([`src/hook.ts:211`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L211), [`src/hook.ts:252`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L252)) |
| Choice order handled (F13) | n.a.. No Choice is used. |
| Size limits respected (F14) | yes. Added and removed text are clipped to 4,000 characters each, and rules to 24 ([`src/hook.ts:367`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L367)) |
| Sample size adequate (F15) | yes. States 25 pairs and reports 1.6 +/- 3.4 s, claiming only no measurable overhead ([`README.md:245`](https://github.com/qkal/Canny/blob/f2c5e53779/README.md#L245)) |
| Independent labels (F16) | n.a.. Outcomes are the task's own hidden tests, not labels of Jev answers ([`bench/run.mjs:104`](https://github.com/qkal/Canny/blob/f2c5e53779/bench/run.mjs#L104)) |
| Held-out result (F17) | n.a.. No threshold or wording was tuned on the bench tasks ([`README.md:245`](https://github.com/qkal/Canny/blob/f2c5e53779/README.md#L245)) |
| Fair baseline (F18) | yes. The control arm runs the same tasks and prompts without Canny ([`bench/run.mjs:33`](https://github.com/qkal/Canny/blob/f2c5e53779/bench/run.mjs#L33)) |
| Typed answers read directly (F19) | yes. Reads `answers[id].noul` as a number and compares it to the cut-offs ([`src/jev.ts:103`](https://github.com/qkal/Canny/blob/f2c5e53779/src/jev.ts#L103)) |
| Data as fields, not templates (F20) | yes. Message and diff travel as state fields; the question text is fixed ([`src/hook.ts:206`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L206)) |
| No instructions in the state (F21) | yes. State holds the message, the diff and the rule texts to judge against ([`src/hook.ts:206`](https://github.com/qkal/Canny/blob/f2c5e53779/src/hook.ts#L206)) |

</details>

## Scores

- Execution 3 of 3: every question is an atomic Noul over a fielded state, gated on probability, with the cut-offs in named constants; F1-F6, F11 and F19 hold.
- Fit 3 of 3: Noul is the right primitive for both decisions, confidence gates each action, and rule questions share one request per change; F2, F4, F5, F11 hold.
- Coverage 3 of 3: the README promises a ledger, a done-gate, pattern checks and two Jev judgments, and all of them run in `src/hook.ts`.
- Evidence 2 of 3: the bench measures cost, turns and pass rate against a control arm with a stated sample, but it never isolates Jev and every run passed in both arms; F7, F15, F18 hold.

## Why this verdict

Verdict 4: no capping failure, since F1-F6, F11, F19 and F21 hold and both decisions are low stakes, so F22 and F20 move nothing. It is not 5 because Evidence is 2 and no labeled run of the two questions closes the loop (`closes_loop: none`). Jev can only relax a block or add a note, which keeps the unflagged agent text and the unpinned `jev-latest` alias to listed fixes.

## Fixes (from reading the code; not tested against it)

1. F22: flag the agent's message and diff as untrusted, add an injection-check Noul, or test a steering message against `claims_done`. Confirm with data. [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13); [`cookbooks/classifying_rag_passages`](https://docs.typesafe.ai/cookbooks/classifying_rag_passages).
2. F12: default to a versioned model ID, log the returned `model`, and retune 0.9 and 0.1 after upgrades. [`models`](https://docs.typesafe.ai/models).
3. Loop: label a small set of done-claims and rule breaks, then derive the cut-offs from the observed probabilities. [`confidence`](https://docs.typesafe.ai/confidence); [`cookbooks/autoresearch_feature_discovery`](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).
4. F23: test one non-English message and diff. [`concepts/state`](https://docs.typesafe.ai/concepts/state).

<details>
<summary><b>Files read (18)</b></summary>

- CHANGELOG.md -- read
- CONTRIBUTING.md -- read
- README.md -- read
- bench/run.mjs -- read
- package.json -- read
- src/checks.ts -- read
- src/cli.ts -- read
- src/hook.ts -- read
- src/jev.ts -- read
- src/ledger.ts -- read
- test/checks.test.ts -- read
- test/cli.test.ts -- read
- test/fixtures.test.ts -- read
- test/hook.test.ts -- read
- test/jev.test.ts -- read
- test/ledger.test.ts -- read
- test/robustness.test.ts -- read
- vitest.config.ts -- read

</details>
