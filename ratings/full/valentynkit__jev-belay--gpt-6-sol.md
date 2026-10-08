[← Summary](../valentynkit__jev-belay--gpt-6-sol.md)

# jev-belay: full rating

**Verdict 3, Use with a fix** · workflow · rated 2026-10-06 at [`ef719db`](https://github.com/valentynkit/jev-belay/tree/ef719db7eaad) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

jev-belay is a Claude Code Stop hook that sends four batched questions to Jev after a local check finds edits without a fresh passing test, build or lint run. It keeps transcript parsing and thresholds in code, makes one hosted call for a narrow judgment, and reports its ablation and operating costs. Overlapping `outcome` options can alter the block veto, while its claimed error rate rests on a small slice used for threshold selection.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Stop hook posts four typed questions to TypeSafe System One ([`belay.mjs:510`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L510)). |
| Options cover every case, no overlap (F8) | **no.** A partly completed task can also report a blocker; either pick changes veto ([`belay.mjs:443-448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L443-L448)). https://docs.typesafe.ai/primitives/advanced.md |
| Sample size adequate (F15) | **no.** One wrong block in 100 cannot establish the claimed under-2% error rate ([`demo/README.md:239-257`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L257)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Held-out result (F17) | **no.** The reported threshold and result use the same 100-stop audit ([`tools__measure.mjs:201-245`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools__measure.mjs#L201-L245)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Fair baseline (F18) | **no.** Comparison is Jev wording alone, without a rules or separate-model alternative ([`demo/README.md:225-236`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L225-L236)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Untrusted text treated as data, low (F22) | **no.** User text is unflagged and model-side injection test skips by default ([`test__jaggedness.test.mjs:46-50`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test__jaggedness.test.mjs#L46-L50)). https://docs.typesafe.ai/model-jaggedness/jev-1.13.md |
| Non-English handled (F23) | **no.** Non-English model-side test skips by default and no recorded result is supplied ([`test__jaggedness.test.mjs:58-60`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test__jaggedness.test.mjs#L58-L60)). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (16) and doesn't apply (1)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each asks one property of task or closing message ([`belay.mjs:416-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L450)). |
| Right primitive (F2) | yes. Binary judgments use Noul; reported status uses four-way Choice ([`belay.mjs:417-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L417-L450)). |
| Structured state (F3) | yes. Named task, final message, and run fields are referenced by questions ([`belay.mjs:470-479`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L479)). |
| Batching (F4) | yes. Four independent questions share one request ([`belay.mjs:504-510`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L504-L510)). |
| Thresholds in code (F5) | yes. Named constants and plugin config control decision cutoffs ([`belay.mjs:551-571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L551-L571)). |
| No invented values (F6) | yes. Code counts changes and checks; Jev judges statements and applicability ([`belay.mjs:236-267`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L236-L267)). |
| Measured in the workflow (F7) | yes. Reports task-specific ablation, threshold sweep, latency and cost ([`demo/README.md:217-258`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L217-L258)). |
| An other option where needed (F9) | yes. Outcome Choice includes `other` ([`belay.mjs:441-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L441-L450)). |
| Evidence recorded evenly (F10) | yes. State supplies the same task, closing message and run evidence to every answer ([`belay.mjs:470-479`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L479)). |
| Confidence drives action, low (F11) | yes. Noul thresholds and Choice confidence floor gate blocking ([`belay.mjs:557-571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L571)). |
| Pinned model version (F12) | yes. Default uses versioned `jev-1.13.0`; caller can override it ([`belay.mjs:18`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L18)). |
| Choice order handled, low (F13) | n.a.. Low-stakes Choice is always n.a. |
| Size limits respected (F14) | yes. Task and closing message are capped; check list lacks a cap, with no large-check example ([`belay.mjs:453-479`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L453-L479)). |
| Independent labels (F16) | yes. Proxy labeling is disclosed, and labels are generated before Jev answers ([`tools__label.mjs:79-86`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools__label.mjs#L79-L86)). |
| Typed answers read directly (F19) | yes. Decision uses `noul`, Choice pick and confidence fields ([`belay.mjs:557-563`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L563)). |
| Data as fields, not templates, low (F20) | yes. Task and message travel in JSON state, while questions stay fixed ([`belay.mjs:470-479`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L479)). |
| No instructions in the state (F21) | yes. Projected state holds content and run evidence only ([`belay.mjs:470-479`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L479)). |

</details>

## Scores

- Execution 2 of 3: Core structure works, but overlapping outcome options can change the veto, F8.
- Fit 3 of 3: The four questions use fitting primitives, one request and probability gates, F2, F4, F11.
- Coverage 3 of 3: Keeps pi-warden's four done questions, evidence gate and nudge, and extends runner checks and subagent evidence ([`belay.mjs:88-177`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L88-L177), [`belay.mjs:338-395`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L338-L395), [`belay.mjs:416-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L450), [`belay.mjs:584-590`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L584-L590)); visual checks are outside its stated goal ([`demo/README.md:3-10`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L3-L10)).
- Evidence 1 of 3: Method and intervals are disclosed, but threshold selection and headline result share one 100-stop slice and lack a separate-model baseline, F7, F15, F17, F18.

## Why this verdict

**3, Use with a fix.** The `outcome` Choice can classify a partly completed task that reports a blocker as either `partial` or `blocked`; the latter vetoes a block, so F8 caps the verdict below 4. The measured workflow and code-side evidence veto keep it above 2, but the reported under-2% wrong-block rate has not been established on held-out data.

## Fixes (from reading the code; not tested against it)

1. Make `outcome` options exclusive, or use independent Nouls for partial progress and a blocker; confirm on ambiguous stops that the veto is stable (F8, [`belay.mjs:443-448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L443-L448)). [TypeSafe Choice guidance](https://docs.typesafe.ai/primitives/choice.md).
2. Hold out a disjoint labeled set before tuning 0.70, then report its wrong-block count with an interval; the present 100 stops and one error cannot establish under 2% (F15, F17, [`demo/README.md:239-257`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L257)). [TypeSafe confidence guidance](https://docs.typesafe.ai/confidence.md).
3. Compare the same stops with a practical rules or LLM alternative to establish the added value of this design (F18, [`demo/README.md:225-236`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L225-L236)). [TypeSafe self-consistency example](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md).
4. Run the model-side injection and non-English checks in a recorded evaluation, or mark untrusted text and add a translation where needed (F22, F23, [`test/jaggedness.test.mjs:46-65`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L46-L65)). [TypeSafe jaggedness guidance](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md), [state guidance](https://docs.typesafe.ai/concepts/state.md).

<details>
<summary><b>Files read (27)</b></summary>

- `.claude-plugin/plugin.json` -- read
- `.github/workflows/test.yml` -- read
- `CHANGELOG.md` -- read
- `CLAUDE.md` -- read
- `CONTRIBUTING.md` -- read
- `README.md` -- read
- `belay.mjs` -- read
- `demo/README.md` -- read
- `demo/sample-decisions.jsonl` -- read
- `demo/take-vhs.sh` -- read
- `test/belts.test.mjs` -- read
- `test/cli.test.mjs` -- read
- `test/client.test.mjs` -- read
- `test/evidence.test.mjs` -- read
- `test/fixtures.mjs` -- read
- `test/hook.test.mjs` -- read
- `test/jaggedness.test.mjs` -- read
- `test/redact.test.mjs` -- read
- `test/runners.test.mjs` -- read
- `test/subagents.test.mjs` -- read
- `test/tui.test.mjs` -- read
- `test/watch.test.mjs` -- read
- `tools/extract-corpus.mjs` -- read
- `tools/fake-jev.mjs` -- read
- `tools/label.mjs` -- read
- `tools/measure.mjs` -- read
- `tui.mjs` -- read

</details>
