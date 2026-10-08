[← Summary](../umatter__jevtools--gpt-6-sol.md)

# jevtools: full rating

**Verdict 3, Use with a fix** · library · rated 2026-10-06 at [`6ab3541`](https://github.com/umatter/jevtools/tree/6ab35414c8) · read: extract · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

Jevtools is a Python library that builds typed Jev questions to choose tools and bind their arguments from candidate pools. It uses hosted Jev backends, typed answers, channel filters and risk-tiered policy. Coverage of open-world values and untuned thresholds limit reliability beyond app-owned domains.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** HTTP backend posts typed decision requests to the hosted endpoint ([`src/jevtools/backends/http.py:203`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/backends/http.py#L203)). |
| Options cover every case, no overlap (F8) | **no.** A merged catalog offers near-duplicate share_file/share_report actions and yields three wrong shown writes ([`docs/BENCH.md:329`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L329)). https://docs.typesafe.ai/primitives/advanced.md |
| Choice order handled (F13) | **no.** Automatic read and external record Choices retain canonical order; reverse probes default only for critical ([`src/jevtools/policy.py:173`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L173)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Held-out result (F17) | **no.** Held-out cases were reused to select hybrid decoding, search cues, and present fallback ([`docs/BENCH.md:284`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L284)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Fair baseline (F18) | **no.** Reported app-domain comparisons are internal variants and an oracle, without a same-case LLM caller ([`docs/BENCH.md:309`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L309)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md |
| Data as fields, not templates (F20) | **no.** A record candidate and drafted content are spliced into verify and accept question objects ([`src/jevtools/templates.py:248`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L248)). https://docs.typesafe.ai/primitives/advanced.md |
| Non-English handled (F23) | **no.** Only English extraction is complete; German and French are basic without reported accuracy ([`README.md:628`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L628)). https://docs.typesafe.ai/concepts/state.md |

<details>
<summary><b>What passes (16) and doesn't apply (1)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Slot templates ask for one argument or property at a time ([`src/jevtools/templates.py:24`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L24)). |
| Right primitive (F2) | yes. Named options use Choice, authorization uses Noul, and ordered levels use Score ([`README.md:98`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L98)). |
| Structured state (F3) | yes. Requests carry a separate JSON state with named fields and typed questions ([`src/jevtools/ballot.py:303`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/ballot.py#L303)). |
| Batching (F4) | yes. The ballot sends independent questions in each planned request, splitting only at limits ([`src/jevtools/ballot.py:293`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/ballot.py#L293)). |
| Thresholds in code (F5) | yes. Risk-tier thresholds and authorization gates are explicit policy fields ([`src/jevtools/policy.py:145`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L145)). |
| No invented values (F6) | yes. Tool arguments decode from finite candidate pools; numeric and temporal parsing occurs in code ([`src/jevtools/candidates.py:128`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L128)). |
| Measured in the workflow (F7) | yes. Live held-out app cases report accuracy, controls, wrong executions, and tokens ([`docs/BENCH.md:309`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L309)). |
| An other option where needed (F9) | yes. Tool and slot Choices include unsupported or none-of-these sentinels ([`src/jevtools/templates.py:81`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L81)). |
| Evidence recorded evenly (F10) | yes. Candidate options carry labels and self-contained descriptions; no asymmetric conclusions are prescribed ([`src/jevtools/candidates.py:128`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L128)). |
| Confidence drives action (F11) | yes. Composed confidence and tier gates control execute, confirm, and clarify ([`src/jevtools/policy.py:647`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L647)). |
| Pinned model version (F12) | n.a.. Thresholds are identified as untuned priors ([`README.md:495`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L495)). |
| Size limits respected (F14) | yes. Preflight caps estimated requests at 24,000 tokens and state at 16,000 ([`src/jevtools/validate.py:70`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/validate.py#L70)). |
| Sample size adequate (F15) | yes. The reported 93% finding states 284 cases, three replays, and its synthetic-app scope ([`README.md:22`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L22)). |
| Independent labels (F16) | yes. Held-out labels are deterministically generated from app rows, and this method is disclosed ([`docs/BENCH.md:221`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L221)). |
| Typed answers read directly (F19) | yes. Choice probabilities are decoded directly by label into value masses ([`src/jevtools/kinds/base.py:534`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/kinds/base.py#L534)). |
| No instructions in the state (F21) | yes. The question templates carry directions and point to request, history, and observations ([`src/jevtools/templates.py:22`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L22)). |
| Untrusted text treated as data (F22) | yes. Observation values receive an untrusted channel; live injection cases showed no planted value reaching a call ([`src/jevtools/candidates.py:29`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L29); [`docs/BENCH.md:154`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L154)). |

</details>

## Scores

- Execution 2 of 3: core question and decision mechanics work, but near-duplicate tool options overlap (F1–F6, F8, F9–F11, F19).
- Fit 2 of 3: typed questions, batching and confidence gates fit; very high impact Choices lack general order averaging (F2, F4, F11, F13).
- Coverage 3 of 3: the library implements its declared app-domain tool and argument binding, with open-world limits stated ([`README.md:52`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L52)).
- Evidence 1 of 3: live measurements and sample sizes exist, but held-out cases guided revisions and no same-case LLM baseline is reported (F7, F15–F18).

## Why this verdict

Verdict 3, Use with a fix. Overlapping tool choices can yield a wrong shown write, fixed Choice order remains on very high decisions, and candidate text enters question fields. Execution and Fit are both 2, so the project does not qualify for 4. Live synthetic-app results support the design but do not establish performance on independent production tasks.

## Fixes (from reading the code; not tested against it)

1. F8: separate overlapping tool actions such as `share_file` and `share_report`, or ask independent action Nouls; confirm on the merged catalog. Source: https://docs.typesafe.ai/primitives/advanced.md
2. F13: average or randomize order for very high impact Choices, including tool selection and access-granting recipients. Source: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
3. F20: put candidates and draft content in structured state or question fields instead of substituted instruction strings. Source: https://docs.typesafe.ai/primitives/advanced.md
4. F17–F18: measure on untouched labeled cases and compare with a reasonable LLM caller on those same cases; only data can confirm a gain. Source: https://docs.typesafe.ai/cookbooks/classification_using_confidence.md

<details>
<summary><b>Files read (15; 408 skipped)</b></summary>

- CLAUDE.md -- skipped: scoped
- README.md -- read
- docs/ARCHITECTURE.md -- read
- docs/BENCH.md -- read
- docs/DECISIONS.md -- skipped: scoped
- docs/SPEC.md -- skipped: scoped
- examples/01_quickstart_weather.py -- skipped: scoped
- examples/02_email_contacts.py -- skipped: scoped
- examples/03_transfer_confirm.py -- read
- examples/04_file_shortlist_widen.py -- skipped: scoped
- examples/05_calendar_temporal.py -- skipped: scoped
- examples/06_agent_loop_invoice.py -- read
- examples/07_openai_dropin.py -- skipped: scoped
- examples/08_bring_your_own_tools.py -- skipped: scoped
- examples/README.md -- skipped: scoped
- examples/_show.py -- skipped: scoped
- examples/fixtures/R1-dropin.answers.json -- skipped: scoped
- examples/fixtures/R1.answers.json -- skipped: scoped
- examples/fixtures/R2-free-text.answers.json -- skipped: scoped
- examples/fixtures/R2-no-history.answers.json -- skipped: scoped
- examples/fixtures/R2.answers.json -- skipped: scoped
- examples/fixtures/R3.answers.json -- skipped: scoped
- examples/fixtures/R4-found-in-bucket.answers.json -- skipped: scoped
- examples/fixtures/R4-miss.answers.json -- skipped: scoped
- examples/fixtures/R4.answers.json -- skipped: scoped
- examples/fixtures/R5.answers.json -- skipped: scoped
- examples/fixtures/R6-refuse.answers.json -- skipped: scoped
- examples/fixtures/R6.answers.json -- skipped: scoped
- examples/fixtures/R7.answers.json -- skipped: scoped
- examples/fixtures/helpdesk.answers.json -- skipped: scoped
- examples/fixtures/regenerate.py -- skipped: scoped
- examples/proxy/README.md -- skipped: scoped
- examples/proxy/client.py -- skipped: scoped
- examples/proxy/data/files.json -- skipped: scoped
- examples/proxy/jevtools.toml -- skipped: scoped
- pyproject.toml -- skipped: scoped
- src/jevtools/__init__.py -- skipped: scoped
- src/jevtools/_compat.py -- skipped: scoped
- src/jevtools/adapters/__init__.py -- skipped: scoped
- src/jevtools/adapters/_router.py -- skipped: scoped
- src/jevtools/adapters/anthropic.py -- skipped: scoped
- src/jevtools/adapters/langchain.py -- skipped: scoped
- src/jevtools/adapters/mcp.py -- skipped: scoped
- src/jevtools/adapters/openai.py -- skipped: scoped
- src/jevtools/adapters/pending.py -- skipped: scoped
- src/jevtools/adapters/pydantic_ai.py -- skipped: scoped
- src/jevtools/backends/__init__.py -- skipped: scoped
- src/jevtools/backends/auto.py -- skipped: scoped
- src/jevtools/backends/base.py -- skipped: scoped
- src/jevtools/backends/cassette.py -- skipped: scoped
- src/jevtools/backends/http.py -- read
- src/jevtools/backends/scripted.py -- skipped: scoped
- src/jevtools/backends/simulator.py -- skipped: scoped
- src/jevtools/ballot.py -- read
- src/jevtools/bench/__init__.py -- skipped: scoped
- src/jevtools/bench/app/__init__.py -- skipped: scoped
- src/jevtools/bench/app/_generate.py -- skipped: scoped
- src/jevtools/bench/app/_heldout.py -- skipped: scoped
- src/jevtools/bench/app/domains/banking/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/domains/banking/catalog.json -- skipped: scoped
- src/jevtools/bench/app/domains/banking/context.json -- skipped: scoped
- src/jevtools/bench/app/domains/crm/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/domains/crm/context.json -- skipped: scoped
- src/jevtools/bench/app/domains/helpdesk/context.json -- skipped: scoped
- src/jevtools/bench/app/domains/inbox/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/domains/inbox/context.json -- skipped: scoped
- src/jevtools/bench/app/domains/research/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/domains/research/context.json -- skipped: scoped
- src/jevtools/bench/app/domains/research/data/variables.json -- skipped: scoped
- src/jevtools/bench/app/domains/workspace/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/domains/workspace/context.json -- skipped: scoped
- src/jevtools/bench/app/heldout/banking/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/heldout/research/cases.jsonl -- skipped: scoped
- src/jevtools/bench/app/runner.py -- skipped: scoped
- src/jevtools/bench/bfcl.py -- skipped: scoped
- src/jevtools/bench/oracle.py -- skipped: scoped
- src/jevtools/bench/run.py -- skipped: scoped
- src/jevtools/bench/tau2.py -- skipped: scoped
- src/jevtools/bench/when2call.py -- skipped: scoped
- src/jevtools/budget.py -- read
- src/jevtools/candidates.py -- read
- src/jevtools/canonical.py -- skipped: scoped
- src/jevtools/cli.py -- skipped: scoped
- src/jevtools/compat.py -- skipped: scoped
- src/jevtools/confidence.py -- read
- src/jevtools/context.py -- skipped: scoped
- src/jevtools/decision.py -- skipped: scoped
- src/jevtools/decode.py -- skipped: scoped
- src/jevtools/demo/__init__.py -- skipped: scoped
- src/jevtools/demo/scenario.py -- skipped: scoped
- src/jevtools/demo/scripts.py -- skipped: scoped
- src/jevtools/errors.py -- skipped: scoped
- src/jevtools/eval/__init__.py -- skipped: scoped
- src/jevtools/eval/dataset.py -- skipped: scoped
- src/jevtools/eval/experiments.py -- skipped: scoped
- src/jevtools/eval/harness.py -- skipped: scoped
- src/jevtools/eval/metrics.py -- skipped: scoped
- src/jevtools/eval/report.py -- skipped: scoped
- src/jevtools/eval/stats.py -- skipped: scoped
- src/jevtools/eval/tuning.py -- skipped: scoped
- src/jevtools/extract/__init__.py -- skipped: scoped
- src/jevtools/extract/base.py -- skipped: scoped
- src/jevtools/extract/catalogs.py -- skipped: scoped
- src/jevtools/extract/coref.py -- skipped: scoped
- src/jevtools/extract/cues.py -- skipped: scoped
- src/jevtools/extract/data/iso4217.json -- skipped: scoped
- src/jevtools/extract/locales/__init__.py -- skipped: scoped
- src/jevtools/extract/locales/de.py -- skipped: scoped
- src/jevtools/extract/locales/en.py -- skipped: scoped
- src/jevtools/extract/locales/fr.py -- skipped: scoped
- src/jevtools/extract/money.py -- skipped: scoped
- src/jevtools/extract/numbers.py -- skipped: scoped
- src/jevtools/extract/patterns.py -- skipped: scoped
- src/jevtools/extract/places.py -- skipped: scoped
- src/jevtools/extract/temporal.py -- skipped: scoped
- src/jevtools/extract/text.py -- skipped: scoped
- src/jevtools/fallback.py -- skipped: scoped
- src/jevtools/kinds/__init__.py -- skipped: scoped
- src/jevtools/kinds/base.py -- read
- src/jevtools/kinds/common.py -- skipped: scoped
- src/jevtools/kinds/derived.py -- skipped: scoped
- src/jevtools/kinds/enum.py -- skipped: scoped
- src/jevtools/kinds/flag.py -- skipped: scoped
- src/jevtools/kinds/late.py -- skipped: scoped
- src/jevtools/kinds/listing.py -- skipped: scoped
- src/jevtools/kinds/money.py -- skipped: scoped
- src/jevtools/kinds/normalize.py -- skipped: scoped
- src/jevtools/kinds/ordinal.py -- skipped: scoped
- src/jevtools/kinds/quantity.py -- skipped: scoped
- src/jevtools/kinds/record.py -- skipped: scoped
- src/jevtools/kinds/ref.py -- skipped: scoped
- src/jevtools/kinds/span.py -- skipped: scoped
- src/jevtools/kinds/temporal.py -- skipped: scoped
- src/jevtools/kinds/text.py -- skipped: scoped
- src/jevtools/kinds/widen.py -- skipped: scoped
- src/jevtools/loop.py -- skipped: scoped
- src/jevtools/plan.py -- skipped: scoped
- src/jevtools/policy.py -- read
- src/jevtools/preview.py -- skipped: scoped
- src/jevtools/probe.py -- skipped: scoped
- src/jevtools/prompts.py -- skipped: scoped
- src/jevtools/qid.py -- skipped: scoped
- src/jevtools/router.py -- skipped: scoped
- src/jevtools/serve/__init__.py -- skipped: scoped
- src/jevtools/serve/app.py -- skipped: scoped
- src/jevtools/serve/config.py -- skipped: scoped
- src/jevtools/sources/__init__.py -- skipped: scoped
- src/jevtools/sources/base.py -- skipped: scoped
- src/jevtools/sources/files.py -- skipped: scoped
- src/jevtools/sources/mcp.py -- skipped: scoped
- src/jevtools/sources/provider.py -- skipped: scoped
- src/jevtools/sources/registry.py -- skipped: scoped
- src/jevtools/sources/retrieval.py -- skipped: scoped
- src/jevtools/sources/specs.py -- skipped: scoped
- src/jevtools/sources/toolsource.py -- skipped: scoped
- src/jevtools/spec/__init__.py -- skipped: scoped
- src/jevtools/spec/catalog.py -- skipped: scoped
- src/jevtools/spec/constraints.py -- skipped: scoped
- src/jevtools/spec/decorators.py -- skipped: scoped
- src/jevtools/spec/infer.py -- read
- src/jevtools/spec/ingest.py -- skipped: scoped
- src/jevtools/spec/markers.py -- skipped: scoped
- src/jevtools/spec/models.py -- skipped: scoped
- src/jevtools/spec/schema.py -- skipped: scoped
- src/jevtools/spec/sidecar.py -- skipped: scoped
- src/jevtools/spec/xjev.py -- skipped: scoped
- src/jevtools/templates.py -- read
- src/jevtools/trace.py -- skipped: scoped
- src/jevtools/validate.py -- read
- src/jevtools/wire.py -- skipped: scoped
- tests/adapters/fixtures/mcp_tools_list.json -- skipped: scoped
- tests/adapters/support.py -- skipped: scoped
- tests/adapters/test_anthropic.py -- skipped: scoped
- tests/adapters/test_extras.py -- skipped: scoped
- tests/adapters/test_langchain.py -- skipped: scoped
- tests/adapters/test_mcp.py -- skipped: scoped
- tests/adapters/test_openai.py -- skipped: scoped
- tests/adapters/test_pydantic_ai.py -- skipped: scoped
- tests/backends/test_auto.py -- skipped: scoped
- tests/backends/test_cassette.py -- skipped: scoped
- tests/backends/test_http.py -- skipped: scoped
- tests/backends/test_probe.py -- skipped: scoped
- tests/backends/test_scripted_fixture.py -- skipped: scoped
- tests/backends/test_simulator.py -- skipped: scoped
- tests/bench/data/BFCL_v4_live_multiple.json -- skipped: scoped
- tests/bench/data/BFCL_v4_live_relevance.json -- skipped: scoped
- tests/bench/data/possible_answer/BFCL_v4_live_multiple.json -- skipped: scoped
- tests/bench/test_app.py -- skipped: scoped
- tests/bench/test_bfcl.py -- skipped: scoped
- tests/bench/test_run.py -- skipped: scoped
- tests/bench/test_tau2.py -- skipped: scoped
- tests/conftest.py -- skipped: scoped
- tests/docs/test_docs.py -- skipped: scoped
- tests/eval/support.py -- skipped: scoped
- tests/eval/test_dataset.py -- skipped: scoped
- tests/eval/test_experiments.py -- skipped: scoped
- tests/eval/test_harness.py -- skipped: scoped
- tests/eval/test_metrics.py -- skipped: scoped
- tests/eval/test_tuning.py -- skipped: scoped
- tests/examples/test_examples.py -- skipped: scoped
- tests/fixtures/scenario_catalog.json -- skipped: scoped
- tests/fixtures/spec_r2_request.json -- skipped: scoped
- tests/fixtures/spec_r5_request.json -- skipped: scoped
- tests/golden/422-isolation/ballot.json -- skipped: scoped
- tests/golden/422-isolation/case.json -- skipped: scoped
- tests/golden/422-isolation/catalog.json -- skipped: scoped
- tests/golden/422-isolation/context.json -- skipped: scoped
- tests/golden/422-isolation/decision.json -- skipped: scoped
- tests/golden/422-isolation/request_1.json -- skipped: scoped
- tests/golden/422-isolation/request_2.json -- skipped: scoped
- tests/golden/422-isolation/response_1.json -- skipped: scoped
- tests/golden/422-isolation/response_2.json -- skipped: scoped
- tests/golden/422-isolation/trace.json -- skipped: scoped
- tests/golden/R1/ballot.json -- skipped: scoped
- tests/golden/R1/case.json -- skipped: scoped
- tests/golden/R1/catalog.json -- skipped: scoped
- tests/golden/R1/context.json -- skipped: scoped
- tests/golden/R1/decision.json -- skipped: scoped
- tests/golden/R1/request.json -- skipped: scoped
- tests/golden/R1/response.json -- skipped: scoped
- tests/golden/R1/trace.json -- skipped: scoped
- tests/golden/R2-click/ballot.json -- skipped: scoped
- tests/golden/R2-click/case.json -- skipped: scoped
- tests/golden/R2-click/catalog.json -- skipped: scoped
- tests/golden/R2-click/context.json -- skipped: scoped
- tests/golden/R2-click/decision.json -- skipped: scoped
- tests/golden/R2-click/decision_1.json -- skipped: scoped
- tests/golden/R2-click/request.json -- skipped: scoped
- tests/golden/R2-click/response.json -- skipped: scoped
- tests/golden/R2-click/trace.json -- skipped: scoped
- tests/golden/R2-click/trace_1.json -- skipped: scoped
- tests/golden/R2-no-history/ballot.json -- skipped: scoped
- tests/golden/R2-no-history/case.json -- skipped: scoped
- tests/golden/R2-no-history/catalog.json -- skipped: scoped
- tests/golden/R2-no-history/context.json -- skipped: scoped
- tests/golden/R2-no-history/decision.json -- skipped: scoped
- tests/golden/R2-no-history/request.json -- skipped: scoped
- tests/golden/R2-no-history/response.json -- skipped: scoped
- tests/golden/R2-no-history/trace.json -- skipped: scoped
- tests/golden/R2/ballot.json -- skipped: scoped
- tests/golden/R2/case.json -- skipped: scoped
- tests/golden/R2/catalog.json -- skipped: scoped
- tests/golden/R2/context.json -- skipped: scoped
- tests/golden/R2/decision.json -- skipped: scoped
- tests/golden/R2/request.json -- skipped: scoped
- tests/golden/R2/response.json -- skipped: scoped
- tests/golden/R2/trace.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/ballot.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/case.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/catalog.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/context.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/context_2.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/decision.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/decision_1.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/request_1.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/request_2.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/response_1.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/response_2.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/trace.json -- skipped: scoped
- tests/golden/R3-TOCTOU-changed/trace_1.json -- skipped: scoped
- tests/golden/R3/ballot.json -- skipped: scoped
- tests/golden/R3/case.json -- skipped: scoped
- tests/golden/R3/catalog.json -- skipped: scoped
- tests/golden/R3/context.json -- skipped: scoped
- tests/golden/R3/decision.json -- skipped: scoped
- tests/golden/R3/request.json -- skipped: scoped
- tests/golden/R3/response.json -- skipped: scoped
- tests/golden/R3/trace.json -- skipped: scoped
- tests/golden/R4-widen/ballot.json -- skipped: scoped
- tests/golden/R4-widen/case.json -- skipped: scoped
- tests/golden/R4-widen/catalog.json -- skipped: scoped
- tests/golden/R4-widen/context.json -- skipped: scoped
- tests/golden/R4-widen/decision.json -- skipped: scoped
- tests/golden/R4-widen/request_1.json -- skipped: scoped
- tests/golden/R4-widen/request_2.json -- skipped: scoped
- tests/golden/R4-widen/request_3.json -- skipped: scoped
- tests/golden/R4-widen/response_1.json -- skipped: scoped
- tests/golden/R4-widen/response_2.json -- skipped: scoped
- tests/golden/R4-widen/response_3.json -- skipped: scoped
- tests/golden/R4/ballot.json -- skipped: scoped
- tests/golden/R4/case.json -- skipped: scoped
- tests/golden/R4/catalog.json -- skipped: scoped
- tests/golden/R4/context.json -- skipped: scoped
- tests/golden/R4/decision.json -- skipped: scoped
- tests/golden/R4/request.json -- skipped: scoped
- tests/golden/R4/response.json -- skipped: scoped
- tests/golden/R4/trace.json -- skipped: scoped
- tests/golden/R5/ballot.json -- skipped: scoped
- tests/golden/R5/case.json -- skipped: scoped
- tests/golden/R5/catalog.json -- skipped: scoped
- tests/golden/R5/context.json -- skipped: scoped
- tests/golden/R5/decision.json -- skipped: scoped
- tests/golden/R5/request.json -- skipped: scoped
- tests/golden/R5/response.json -- skipped: scoped
- tests/golden/R5/trace.json -- skipped: scoped
- tests/golden/R6-injection/ballot.json -- skipped: scoped
- tests/golden/R6-injection/case.json -- skipped: scoped
- tests/golden/R6-injection/catalog.json -- skipped: scoped
- tests/golden/R6-injection/context.json -- skipped: scoped
- tests/golden/R6-injection/decision.json -- skipped: scoped
- tests/golden/R6-injection/request.json -- skipped: scoped
- tests/golden/R6-injection/response.json -- skipped: scoped
- tests/golden/R6-injection/trace.json -- skipped: scoped
- tests/golden/R6-step1/ballot.json -- skipped: scoped
- tests/golden/R6-step1/case.json -- skipped: scoped
- tests/golden/R6-step1/catalog.json -- skipped: scoped
- tests/golden/R6-step1/context.json -- skipped: scoped
- tests/golden/R6-step1/decision.json -- skipped: scoped
- tests/golden/R6-step1/request.json -- skipped: scoped
- tests/golden/R6-step1/response.json -- skipped: scoped
- tests/golden/R6-step1/trace.json -- skipped: scoped
- tests/golden/R6-step2/ballot.json -- skipped: scoped
- tests/golden/R6-step2/case.json -- skipped: scoped
- tests/golden/R6-step2/catalog.json -- skipped: scoped
- tests/golden/R6-step2/context.json -- skipped: scoped
- tests/golden/R6-step2/decision.json -- skipped: scoped
- tests/golden/R6-step2/request.json -- skipped: scoped
- tests/golden/R6-step2/response.json -- skipped: scoped
- tests/golden/R6-step2/trace.json -- skipped: scoped
- tests/golden/R6/ballot.json -- skipped: scoped
- tests/golden/R6/case.json -- skipped: scoped
- tests/golden/R6/catalog.json -- skipped: scoped
- tests/golden/R6/context.json -- skipped: scoped
- tests/golden/R6/decision.json -- skipped: scoped
- tests/golden/R6/decision_1.json -- skipped: scoped
- tests/golden/R6/decision_2.json -- skipped: scoped
- tests/golden/R6/request_1.json -- skipped: scoped
- tests/golden/R6/request_2.json -- skipped: scoped
- tests/golden/R6/response_1.json -- skipped: scoped
- tests/golden/R6/response_2.json -- skipped: scoped
- tests/golden/R6/trace.json -- skipped: scoped
- tests/golden/R6/trace_1.json -- skipped: scoped
- tests/golden/R6/trace_2.json -- skipped: scoped
- tests/golden/R7/ballot.json -- skipped: scoped
- tests/golden/R7/case.json -- skipped: scoped
- tests/golden/R7/catalog.json -- skipped: scoped
- tests/golden/R7/context.json -- skipped: scoped
- tests/golden/R7/decision.json -- skipped: scoped
- tests/golden/R7/request.json -- skipped: scoped
- tests/golden/R7/response.json -- skipped: scoped
- tests/golden/R7/trace.json -- skipped: scoped
- tests/golden/README.md -- skipped: scoped
- tests/golden/budget-split/ballot.json -- skipped: scoped
- tests/golden/budget-split/case.json -- skipped: scoped
- tests/golden/budget-split/catalog.json -- skipped: scoped
- tests/golden/budget-split/context.json -- skipped: scoped
- tests/golden/budget-split/decision.json -- skipped: scoped
- tests/golden/budget-split/request_1.json -- skipped: scoped
- tests/golden/budget-split/request_2.json -- skipped: scoped
- tests/golden/budget-split/response_1.json -- skipped: scoped
- tests/golden/budget-split/response_2.json -- skipped: scoped
- tests/golden/budget-split/trace.json -- skipped: scoped
- tests/golden/cases.py -- skipped: scoped
- tests/golden/fixtures/files.json -- skipped: scoped
- tests/golden/test_golden.py -- skipped: scoped
- tests/kinds_support.py -- skipped: scoped
- tests/live/test_live.py -- skipped: scoped
- tests/loop/support.py -- skipped: scoped
- tests/loop/test_agent.py -- skipped: scoped
- tests/loop/test_entities.py -- skipped: scoped
- tests/loop/test_injection.py -- skipped: scoped
- tests/loop/test_observations.py -- skipped: scoped
- tests/loop/test_r6.py -- skipped: scoped
- tests/loop/test_support.py -- skipped: scoped
- tests/policy/test_matrix.py -- skipped: scoped
- tests/scenario/fixtures.py -- skipped: scoped
- tests/scenario/scripts.py -- skipped: scoped
- tests/scenario/support.py -- skipped: scoped
- tests/scenario/test_fixtures.py -- skipped: scoped
- tests/scenario/test_quickstart.py -- skipped: scoped
- tests/scenario/test_review_engine.py -- skipped: scoped
- tests/scenario/test_rounds.py -- skipped: scoped
- tests/scenario/test_simulator_scenarios.py -- skipped: scoped
- tests/scenario/test_walkthrough.py -- skipped: scoped
- tests/scenario_sources.py -- skipped: scoped
- tests/serve/support.py -- skipped: scoped
- tests/serve/test_app.py -- skipped: scoped
- tests/serve/test_config.py -- skipped: scoped
- tests/stubs.py -- skipped: scoped
- tests/support.py -- skipped: scoped
- tests/unit/test_app_domain_features.py -- skipped: scoped
- tests/unit/test_ballot.py -- skipped: scoped
- tests/unit/test_bench_regressions.py -- skipped: scoped
- tests/unit/test_budget.py -- skipped: scoped
- tests/unit/test_candidates.py -- skipped: scoped
- tests/unit/test_canonical.py -- skipped: scoped
- tests/unit/test_catalog.py -- skipped: scoped
- tests/unit/test_cli.py -- skipped: scoped
- tests/unit/test_compat.py -- skipped: scoped
- tests/unit/test_confidence.py -- skipped: scoped
- tests/unit/test_constraints.py -- skipped: scoped
- tests/unit/test_context.py -- skipped: scoped
- tests/unit/test_decision.py -- skipped: scoped
- tests/unit/test_decode.py -- skipped: scoped
- tests/unit/test_extract_numbers.py -- skipped: scoped
- tests/unit/test_extract_temporal.py -- skipped: scoped
- tests/unit/test_extract_text.py -- skipped: scoped
- tests/unit/test_fallback_impl.py -- skipped: scoped
- tests/unit/test_infer.py -- skipped: scoped
- tests/unit/test_kinds_base.py -- skipped: scoped
- tests/unit/test_kinds_composite.py -- skipped: scoped
- tests/unit/test_kinds_enum.py -- skipped: scoped
- tests/unit/test_kinds_ref.py -- skipped: scoped
- tests/unit/test_kinds_scalars.py -- skipped: scoped
- tests/unit/test_kinds_temporal.py -- skipped: scoped
- tests/unit/test_markers.py -- skipped: scoped
- tests/unit/test_plan.py -- skipped: scoped
- tests/unit/test_policy.py -- skipped: scoped
- tests/unit/test_prompts.py -- skipped: scoped
- tests/unit/test_qid.py -- skipped: scoped
- tests/unit/test_quantity_grids.py -- skipped: scoped
- tests/unit/test_review_engine.py -- skipped: scoped
- tests/unit/test_router.py -- skipped: scoped
- tests/unit/test_scenario_pools.py -- skipped: scoped
- tests/unit/test_schema.py -- skipped: scoped
- tests/unit/test_source_specs.py -- skipped: scoped
- tests/unit/test_sources.py -- skipped: scoped
- tests/unit/test_sources_extra.py -- skipped: scoped
- tests/unit/test_templates.py -- skipped: scoped
- tests/unit/test_trace.py -- skipped: scoped
- tests/unit/test_trust_followups.py -- skipped: scoped
- tests/unit/test_validate.py -- skipped: scoped
- tests/unit/test_verify.py -- skipped: scoped

</details>
