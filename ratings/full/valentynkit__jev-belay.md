[← Summary](../valentynkit__jev-belay.md)

# jev-belay: full rating

**Verdict 4, Use it** · workflow · rated 2026-10-06 at [`ef719db`](https://github.com/valentynkit/jev-belay/tree/ef719db7eaad) · read: full · rubric 2026-09-29.2 · claude-sonnet-5-5, medium effort

## Summary

jev-belay is a Claude Code Stop hook that, only when files changed and no check passed since, sends one Jev request of four questions about the closing message and blocks the stop when it reads as an unverified done. It keeps counting, thresholds and the evidence veto in code, pins `jev-1.13.0`, and reports AUROC with intervals on 100 labeled stops against a wording-only baseline. Its 0.70 cutoff was swept on the same 100 stops that report the block counts, labels come from one model, and the injection and non-English checks are skipped by default.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The Stop hook posts four questions to api.typesafe.ai/v1/systemone with model jev-1.13.0 ([`belay.mjs:510`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L510)) |
| Held-out result (F17) | **no.** The 0.70 cut-off was swept on the same 100 stops that report its caught and wrong-block counts ([`demo/README.md:239-251`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L251), [`CHANGELOG.md:56-60`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/CHANGELOG.md#L56-L60)). cookbooks/autoresearch |
| Untrusted text treated as data, high or low (F22) | **no.** Task and message go in unflagged; injection test covers only decide(); its model-side twin is skipped, unrecorded ([`test/jaggedness.test.mjs:30-41`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L30-L41), [`test/jaggedness.test.mjs:51-56`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L51-L56)). model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** A non-English check is skipped unless JEV_LIVE_URL is set and no result is recorded ([`test/jaggedness.test.mjs:58-61`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L58-L61)). concepts/state |

<details>
<summary><b>What passes (19) and doesn't apply (1)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Three Nouls each test one property of `final_message` or `task`; the Choice asks one thing, what the message reports ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451)) |
| Right primitive (F2) | yes. Yes/no judgments are Nouls; the four report types are a Choice ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451)) |
| Structured state (F3) | yes. State is `{task, final_message, run: {file_changes, checks_run}}`; questions name `final_message` and `task` ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Batching (F4) | yes. All four questions go in one request per stop ([`belay.mjs:504`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L504), [`belay.mjs:740`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L740)) |
| Thresholds in code (F5) | yes. Named constants and a plugin option hold cut-offs; claims_verified's 0.7 is an inline literal that only edits a reason ([`belay.mjs:551-555`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L551-L555), [`belay.mjs:571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L571)) |
| No invented values (F6) | yes. Code counts edits, classifies checks and builds `run`; Jev only judges the message ([`belay.mjs:236-268`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L236-L268), [`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Measured in the workflow (F7) | yes. README reports AUROC with intervals on 100 labeled stops, plus latency, tokens and cost; `measure.mjs` regenerates them ([`demo/README.md:217-262`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L217-L262), [`tools/measure.mjs:140-190`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools/measure.mjs#L140-L190)) |
| Options cover every case, no overlap (F8) | yes. Four described options; blocked ("or the user is asked something") also fits a done message ending in an offer ([`belay.mjs:441-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L441-L450)) |
| An "other" option where needed (F9) | yes. The Choice has `other`, "None of these" ([`belay.mjs:447-449`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L447-L449)) |
| Evidence recorded evenly (F10) | yes. The state gives the request, the closing message and the run counts, with passing and failing checks both listed ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Confidence drives action, low (F11) | yes. A block needs claims_done 0.70 or more and applies 0.5 or more; an outcome pick of 0.4 vetoes ([`belay.mjs:557-571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L571)) |
| Pinned model version (F12) | yes. Default model is `jev-1.13.0`, with the README noting aliases move ([`belay.mjs:18`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L18), [`demo/README.md:102`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L102)) |
| Choice order handled, low (F13) | n.a.. The only Choice is low stakes; the rubric marks F13 n.a. below high |
| Size limits respected (F14) | yes. Task is cut to 1500 characters and the message to its last 2000 before sending ([`belay.mjs:453-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L453-L480)) |
| Sample size adequate (F15) | yes. README states 100 stops with 12 positives and says the second decimal is not established ([`demo/README.md:254-258`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L254-L258), [`demo/README.md:277-278`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L277-L278)) |
| Independent labels (F16) | yes. A Sonnet proxy labeled two judgments without seeing Jev's answers, disclosed as not by hand ([`tools/label.mjs:12-13`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools/label.mjs#L12-L13), [`demo/README.md:219-223`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L219-L223)) |
| Fair baseline (F18) | yes. Same 100 stops through a wording-only claims_done arm and a keyword pre-screen; no general chat-model prompt was tried ([`demo/README.md:229-233`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L229-L233), [`demo/README.md:260-262`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L260-L262)) |
| Typed answers read directly (F19) | yes. `decide` reads the `noul`, `choice` and [`confidence`](https://docs.typesafe.ai/confidence) fields ([`belay.mjs:557-562`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L562)) |
| Data as fields, not templates, high or low (F20) | yes. Task and message sit in state fields; question text is constant ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451), [`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| No instructions in the state (F21) | yes. State holds the request, the message and two counts, and no directions ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded and batched, and the options, other option, even evidence and confidence gating hold, from F1-F6, F8-F11 and F19.
- Fit 3 of 3: each decision uses the fitting primitive, confidence gates the one action, and four questions share one request, from F2, F4 and F11.
- Coverage 3 of 3: the pi-warden done check it grew from is kept whole (four questions, both belts, the same unverified-done rule) and its stated goal is met, from F0-F4 and F11.
- Evidence 1 of 3: numbers come with method, but the cut-off was tuned and reported on the same 100 stops, from F7, F15, F16 and F17.

## Why this verdict

No capping failure and no fatal flaw: F1-F6, F8-F11, F19 and F21 are yes, F13 is n.a. because every decision is low, and Execution and Fit are 3. It is not a 5 because Evidence is 1: F17 is no, since the 0.70 cutoff was swept on the same 100 stops that report the 7-of-12 and 1-wrong-block figures. F22 and F23 are no (skipped tests, no recorded result) but sit below very high, so they are fixes only. Borderline call: blocking the stop affects only the asker's own session and costs one extra test run, capped at three per session, so the decisions are low rather than high.

<details>
<summary><b>Files read (27)</b></summary>

- .claude-plugin/plugin.json -- read
- .github/workflows/test.yml -- read
- CHANGELOG.md -- read
- CLAUDE.md -- read
- CONTRIBUTING.md -- read
- README.md -- read
- belay.mjs -- read
- demo/README.md -- read
- demo/sample-decisions.jsonl -- read
- demo/take-vhs.sh -- read
- test/belts.test.mjs -- read
- test/cli.test.mjs -- read
- test/client.test.mjs -- read
- test/evidence.test.mjs -- read
- test/fixtures.mjs -- read
- test/hook.test.mjs -- read
- test/jaggedness.test.mjs -- read
- test/redact.test.mjs -- read
- test/runners.test.mjs -- read
- test/subagents.test.mjs -- read
- test/tui.test.mjs -- read
- test/watch.test.mjs -- read
- tools/extract-corpus.mjs -- read
- tools/fake-jev.mjs -- read
- tools/label.mjs -- read
- tools/measure.mjs -- read
- tui.mjs -- read

</details>
