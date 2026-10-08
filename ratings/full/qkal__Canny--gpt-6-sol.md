[← Summary](../qkal__Canny--gpt-6-sol.md)

# Canny: full rating

**Verdict 4, Use it** · workflow · rated 2026-10-06 at [`f2c5e53`](https://github.com/qkal/Canny/tree/f2c5e53779445d60dc4a09d2dbced2308fccb820) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Canny supervises coding-agent sessions with deterministic checks and uses hosted Jev for completion-claim and project-rule judgments.
Its Noul questions are narrow, fielded, batched by change, cached, and acted on only at conservative thresholds.
Its published agent comparison does not validate live Jev judgments, and requests lack a total size guard.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The judge posts typed Noul questions and state to TypeSafe’s System One endpoint ([`src/jev.ts:8`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L8), [`src/jev.ts:90-99`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L90-L99)). |
| Measured in workflow (F7) | **no.** Published agent A/B measures Canny, while Jev behavior has only mocked endpoint tests ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271); [`test/jev.test.ts:8-21`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/test/jev.test.ts#L8-L21)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Size limits respected (F14) | **no.** Message length and combined rules plus diff have no total request guard ([`src/hook.ts:207-210`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L207-L210), [`src/hook.ts:228`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L228)). https://docs.typesafe.ai/models |
| Sample size adequate (F15) | **no.** The 25-pair agent result cannot establish Jev judgment accuracy because it reports no live Jev judgments ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Independent labels (F16) | **no.** The A/B task tests label task completion, but no independent labels audit Jev’s two judgments ([`bench/run.mjs:93-106`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/bench/run.mjs#L93-L106); [`README.md:273`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L273)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Held-out result (F17) | **no.** The same five tasks informed gate changes and the later agent run; Jev has no held-out result ([`README.md:271`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L271); [`CHANGELOG.md:10-13`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/CHANGELOG.md#L10-L13)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Untrusted text treated as data (F22) | **no.** Agent messages and edited text reach Jev without source flags or steering tests ([`src/hook.ts:207-210`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L207-L210), [`src/hook.ts:227-230`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L227-L230); [`test/hook.test.ts:506-545`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/test/hook.test.ts#L506-L545)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Both agent-message and code-rule judgments are untested in other languages ([`test/hook.test.ts:506-545`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/test/hook.test.ts#L506-L545); [`test/jev.test.ts:8-80`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/test/jev.test.ts#L8-L80)). https://docs.typesafe.ai/models |

<details>
<summary><b>What passes (11) and doesn't apply (5)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Completion and each project rule get separate yes/no questions with explicit criteria ([`src/hook.ts:39-44`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39-L44), [`src/hook.ts:195-201`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L195-L201)). |
| Right primitive (F2) | yes. Both decisions ask binary questions through Noul ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39), [`src/hook.ts:197`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L197)). |
| Structured state (F3) | yes. Stop sends `message`; rule checks send named `rules`, `change.file`, `added`, and `removed` fields ([`src/hook.ts:208`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L208), [`src/hook.ts:228`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L228)). |
| Batching (F4) | yes. Every rule for one change is sent in one request; changes have different state ([`src/hook.ts:194-210`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L194-L210)). |
| Thresholds in code (F5) | yes. Named constants define 0.9 for rule notes and 0.1 for Stop relaxation ([`src/jev.ts:12-13`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L12-L13)). |
| No invented values (F6) | yes. Code determines edits, command success, and repeat counts; Jev only judges two text properties ([`src/checks.ts:71-96`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/checks.ts#L71-L96); [`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39), [`src/hook.ts:197`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L197)). |
| Options cover every case (F8) | n.a.. No Choice questions ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39), [`src/hook.ts:197`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L197)). |
| Other option (F9) | n.a.. No Choice questions ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39), [`src/hook.ts:197`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L197)). |
| Evidence recorded evenly (F10) | n.a.. Each judgment examines one message or one code change against project rules, without competing evidence ([`src/hook.ts:207-210`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L207-L210), [`src/hook.ts:228`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L228)). |
| Confidence drives action (F11) | yes. Only scores at least 0.9 create notes; only scores at most 0.1 relax Stop ([`src/hook.ts:211`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L211), [`src/hook.ts:252`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L252)). |
| Pinned model version (F12) | n.a.. Thresholds are fixed from claimed drift, with no reported tuning dataset ([`src/jev.ts:7`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L7), [`src/jev.ts:10-13`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L10-L13); [`README.md:186-193`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/README.md#L186-L193)). |
| Choice order handled (F13) | n.a.. No Choice questions ([`src/hook.ts:39`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L39), [`src/hook.ts:197`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L197)). |
| Fair baseline (F18) | yes. The harness alternates Canny and control on identical tasks and restores original tests before judging ([`bench/run.mjs:56-61`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/bench/run.mjs#L56-L61), [`bench/run.mjs:93-106`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/bench/run.mjs#L93-L106)). |
| Typed answers read directly (F19) | yes. The adapter reads `answers[id].noul` and decision code compares numeric values ([`src/jev.ts:103-108`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/jev.ts#L103-L108); [`src/hook.ts:211`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L211), [`src/hook.ts:231`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L231)). |
| Data as fields (F20) | yes. Message, rules, and change text occupy state fields; question wording uses field paths and indices ([`src/hook.ts:195-209`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L195-L209), [`src/hook.ts:227-230`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L227-L230)). |
| No instructions in state (F21) | yes. `rules` contains project policy being judged against; Jev’s directions and true/false criteria stay in questions ([`src/hook.ts:195-209`](https://github.com/qkal/Canny/blob/f2c5e53779445d60dc4a09d2dbced2308fccb820/src/hook.ts#L195-L209)). |

</details>

## Scores

- Execution 3 of 3: atomic, structured Nouls are batched and read as probabilities with coded thresholds (F1-F6, F11, F19).
- Fit 3 of 3: both binary judgments use Nouls, rule questions share a request, and confidence gates every Jev-triggered action (F2, F4, F11).
- Coverage 3 of 3: both stated Jev judgments run in the hooks, with tests for their decision paths (F0, F1, F11, F19).
- Evidence 1 of 3: paired agent outcomes and timing are reported, but live Jev judgments lack labeled measurement (F7, F15-F18).

## Why this verdict

Canny merits 4 because both Jev judgments use fitting Nouls, direct probabilities, and conservative coded thresholds, with no capping failure. It does not reach 5 because the published benchmark measures agent outcomes and timing rather than labeled Jev judgments, and no labeled result revises the design. The Stop judgment only relaxes a ledger block for the asker's own session; the rule judgment adds a note to that session.

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
