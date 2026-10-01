[← Summary](../valentynkit__jev-belay.md)

# jev-belay: full rating

**Verdict 4, Use it** · workflow · rated 2026-09-30 at [`ef719db`](https://github.com/valentynkit/jev-belay/tree/ef719db7eaad) · read: full · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

jev-belay is a Claude Code Stop hook that, only when files changed and no check passed since, sends one Jev request of four questions about the closing message and blocks the stop when it reads as an unverified done. It keeps counting, thresholds and the evidence veto in code, pins `jev-1.13.0`, and reports AUROC with intervals on 100 labeled stops against a wording-only baseline. Its 0.70 cutoff was swept on the same 100 stops that report the block counts, and the labels come from one model.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The Stop hook posts four questions to api.typesafe.ai /v1/systemone with model jev-1.13.0 ([`belay.mjs:510`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L510)) |
| Held-out result (F17) | **no.** The 0.70 threshold was swept on the same 100 stops that report the 7-of-12 and 1-wrong-block numbers ([`demo/README.md:239-250`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L239-L250), [`CHANGELOG.md:44-46`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/CHANGELOG.md#L44-L46)). https://docs.typesafe.ai/cookbooks/classification_using_confidence.md |

<details>
<summary><b>What passes (21) and doesn't apply (1)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each question names one property of `final_message` or `task`; claims_verified joins ran-and-passed as one claim ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451)) |
| Right primitive (F2) | yes. Three Nouls for yes/no properties; a Choice for the four named outcomes ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451)) |
| Structured state (F3) | yes. Object with `task`, `final_message` and `run.file_changes`/`run.checks_run`; questions point at field names ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Batching (F4) | yes. All four questions go in one request over one state ([`belay.mjs:504`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L504)) |
| Thresholds in code (F5) | yes. Named constants and an option for 0.70, 0.5 and 0.4; the 0.7 for claims_verified is an inline literal ([`belay.mjs:551-555`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L551-L555), [`belay.mjs:571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L571)) |
| No invented values (F6) | yes. Code counts file changes and checks; Jev only judges the message and task ([`belay.mjs:236-268`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L236-L268), [`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Measured in the workflow (F7) | yes. AUROC, blocks, catches, cost and latency reported on 100 labeled real stops with intervals ([`demo/README.md:219-259`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L219-L259), [`tools/measure.mjs:152-199`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools/measure.mjs#L152-L199)) |
| Options cover every case, no overlap (F8) | yes. complete, partial, blocked, other, each with a stated boundary; partial and blocked can touch when a question is asked ([`belay.mjs:441-450`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L441-L450)) |
| An "other" option where needed (F9) | yes. The Choice carries `other: None of these` ([`belay.mjs:448`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L448)) |
| Evidence recorded evenly (F10) | yes. The state holds the request, the message and run counts, with no conclusions written in ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Confidence drives action, low (F11) | yes. A block needs claims_done at 0.70 or more, applies at 0.5 or more; an outcome pick needs 0.4 to veto ([`belay.mjs:557-571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L571)) |
| Pinned model version (F12) | yes. `jev-1.13.0` is the default, with the README saying aliases move ([`belay.mjs:18`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L18), [`demo/README.md:102`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L102)) |
| Choice order handled, low (F13) | n.a.. No decision is high or very high, so the Choice order rule does not apply ([`belay.mjs:557-571`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L571)) |
| Size limits respected (F14) | yes. Task capped at 1,500 chars and message at 2,000; median call 1,222 input tokens ([`belay.mjs:453-468`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L453-L468), [`demo/README.md:64`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L64)) |
| Sample size adequate (F15) | yes. Claims state n=100 with 12 positives and a 95% interval, and say the second decimal is not supported ([`demo/README.md:219-257`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L219-L257), [`demo/README.md:277-278`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L277-L278)) |
| Independent labels (F16) | yes. A model proxy labeler, blind to Jev's answers, labeled two judgment halves; disclosed as not by hand ([`tools/label.mjs:1-12`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools/label.mjs#L1-L12), [`demo/README.md:221-222`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L221-L222)) |
| Fair baseline (F18) | yes. Same 100 stops scored with the wording-only judge, the published limpet design; a keyword pre-screen is measured too ([`demo/README.md:226-233`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L226-L233), [`demo/README.md:261`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/demo/README.md#L261), [`tools/measure.mjs:161-165`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/tools/measure.mjs#L161-L165)) |
| Typed answers read directly (F19) | yes. Code reads `.noul`, `.choice` and `.confidence` fields from the answers ([`belay.mjs:557-563`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L557-L563)) |
| Data as fields, not templates, low (F20) | yes. Question text is fixed and points at `final_message` and `task`; nothing is spliced in ([`belay.mjs:416-451`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L416-L451)) |
| No instructions in the state (F21) | yes. The state holds the user's request, the closing message and run counts only ([`belay.mjs:470-480`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/belay.mjs#L470-L480)) |
| Untrusted text treated as data, low (F22) | yes. A planted-instruction test shows the evidence veto holds; the live check is skipped without a URL ([`test/jaggedness.test.mjs:23-31`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L23-L31), [`test/jaggedness.test.mjs:46-51`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L46-L51)) |
| Non-English handled (F23) | yes. One Russian-language case in the live checks, skipped by default and with no recorded result ([`test/jaggedness.test.mjs:58-61`](https://github.com/valentynkit/jev-belay/blob/ef719db7eaad/test/jaggedness.test.mjs#L58-L61)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded and batched in one request, and each applicable gate is yes, F1-F6 and F8-F11.
- Fit 3 of 3: each decision uses the fitting primitive, confidence gates the block through named thresholds, and the four questions share one request, F2, F4, F5 and F11.
- Coverage 3 of 3: of pi-warden's done guard, 8 of 10 decisions are kept or changed, and the dropped UI-check and outside-project rules do not touch its own stated goal.
- Evidence 2 of 3: measured on 100 stops with a stated sample, an interval and a wording-only baseline, with one weakness: the 0.70 threshold was tuned on the same stops, F7, F15, F16, F17, F18.

## Why this verdict

No capping failure and no fatal flaw: F1-F6, F8-F11, F19 and F21 are yes, F13 is n.a. because every decision is low, and Execution and Fit are 3. It is not a 5 because Evidence is 2: F17 is no, since the 0.70 cutoff was swept on the same 100 stops that report the 7-of-12 and 1-wrong-block figures. Borderline call: blocking the stop affects only the asker's own session and costs one extra test run, capped at three per session, so the decisions are low rather than high.

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
