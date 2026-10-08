[← Summary](../jkudish__jev-mcp--gpt-6-sol.md)

# jev-mcp: full rating

**Verdict 3, Use with a fix** · agent tool · rated 2026-10-06 at [`fcd18d8`](https://github.com/jkudish/jev-mcp/tree/fcd18d8609ba05a2f1988af91407d86377801ca0) · read: full · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

This MCP server exposes twelve Jev judgment tools to agents, with typed questions and advisory probability-based actions. It batches related questions, validates answers, and fails closed on malformed responses. Instructions embedded in state and unmeasured performance claims limit the rating.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** The tool builds a hosted Jev relation Choice with the TypeSafe SDK ([`src/server.ts:211`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L211)). |
| Measured in workflow (F7) | **no.** README asserts 150–500 ms without a project-specific measured distribution or accuracy study ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Pinned model (F12) | **no.** Tuned classification defaults run on redirecting `jev-latest` unless caller pins a version ([`src/server.ts:86`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L86)). https://docs.typesafe.ai/models |
| Size limits respected (F14) | **no.** Caller-supplied verification claims and evidence have no aggregate guard, including long reports ([`src/server.ts:178`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L178)). https://docs.typesafe.ai/models |
| Sample size adequate (F15) | **no.** The 150–500 ms claim supplies neither sample size nor measurement conditions ([`README.md:27`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/README.md#L27)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Data as fields (F20) | **no.** Claim text and a caller query are interpolated into instructions, changing the question for realistic inputs ([`src/server.ts:206`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L206)). https://docs.typesafe.ai/primitives/advanced |
| No instructions in state (F21) | **no.** State contains a directive-like `purpose` that tells Jev to verify each claim ([`src/server.ts:229`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L229)). https://docs.typesafe.ai/concepts/state |
| Untrusted text as data (F22) | **no.** Injected claim text can reach `jev_verify` without provenance or a steering test ([`src/server.ts:206`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L206)). https://docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** General web and document inputs have no non-English tests or translation path ([`test/e2e.test.mjs:1`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/test/e2e.test.mjs#L1)). https://docs.typesafe.ai/models |

<details>
<summary><b>What passes (11) and doesn't apply (4)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Tools split claim relations, screening properties, review rubrics and audit failure modes into separate questions ([`src/server.ts:1455`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1455)). |
| Right primitive (F2) | yes. Boolean checks use Noul, finite alternatives Choice, and ordered review rubrics Score ([`src/server.ts:1463`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1463)). |
| Structured state (F3) | yes. Claims, evidence and IDs travel as named JSON fields ([`src/server.ts:229`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L229)). |
| Batching (F4) | yes. Independent claim questions share one state and one request ([`src/server.ts:235`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L235)). |
| Thresholds in code (F5) | yes. Named defaults and config parameters gate review outcomes ([`src/lib.ts:329`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L329)). |
| No invented values (F6) | yes. Regex produces candidate substrings; Jev selects a key and code returns the original substring ([`src/server.ts:1234`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1234)). |
| Options cover cases (F8) | yes. Evidence relations include silence; candidate decisions include ask, investigate and none ([`src/lib.ts:153`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L153)). |
| Other option (F9) | yes. Selection tools include escape options, and semantic find pairs forced Choice with existence Noul ([`src/server.ts:511`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L511)). |
| Evidence recorded evenly (F10) | yes. Choice criteria carry neutral definitions while caller evidence travels in one shared state ([`src/server.ts:220`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L220)). |
| Confidence drives action (F11) | yes. Classify requires top probability and margin for `auto`; other tools gate review or escalation ([`src/lib.ts:143`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/lib.ts#L143)). |
| Choice order handled (F13) | n.a.. All decisions are low-stakes advisory outputs ([`src/server.ts:851`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L851)). |
| Independent labels (F16) | n.a.. No project-specific accuracy result is reported ([`examples/exa-classify.md:64`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/examples/exa-classify.md#L64)). |
| Held-out result (F17) | n.a.. No project-specific tuned-result evaluation is reported ([`examples/exa-classify.md:64`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/examples/exa-classify.md#L64)). |
| Fair baseline (F18) | n.a.. No project-specific comparative evaluation is reported ([`examples/exa-classify.md:64`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/examples/exa-classify.md#L64)). |
| Typed answers read directly (F19) | yes. Server validates and reads Choice probabilities, Noul values and Score fields ([`src/server.ts:1517`](https://github.com/jkudish/jev-mcp/blob/fcd18d8609ba05a2f1988af91407d86377801ca0/src/server.ts#L1517)). |

</details>

## Scores

- Execution 3 of 3: atomic typed questions, structured state, batching, coded thresholds, and validated outputs cover the tool decisions (F1–F6, F8–F11, F19).
- Fit 3 of 3: each tool uses Jev's fitting primitive, batches related questions, and returns confidence-gated advice (F2, F4, F11).
- Coverage 3 of 3: all twelve promised tools exist; the citation-check quote-presence omission is explained as caller work (lineage coverage, F0).
- Evidence 0 of 3: latency and example-result claims lack a documented project-specific measurement method (F7, F15).

## Why this verdict

Verdict 3, Use with a fix: F21 mixes task directions into state, and Evidence 0 reflects unsupported latency and example-result claims. The tools otherwise earn Execution 3 and Fit 3, with no fatal flaw. Verdict 4 requires no capping failure.

<details>
<summary><b>Files read (24)</b></summary>

- .github/workflows/ci.yml -- read
- CHANGELOG.md -- read
- CONTRIBUTING.md -- read
- README.md -- read
- SECURITY.md -- read
- examples/exa-classify.md -- read
- examples/exa-classify.mjs -- read
- package.json -- read
- skills/jev/SKILL.md -- read
- skills/jev/reference/tools.md -- read
- src/http.ts -- read
- src/index.ts -- read
- src/lib.ts -- read
- src/provider.ts -- read
- src/server.ts -- read
- test/e2e.test.mjs -- read
- test/exa-example.test.mjs -- read
- test/fixtures/typesafe-abort-child.mjs -- read
- test/http.test.mjs -- read
- test/mock.test.mjs -- read
- test/provider.test.mjs -- read
- test/server.test.mjs -- read
- test/typesafe-abort-regression.test.mjs -- read
- test/unit.test.mjs -- read

</details>
