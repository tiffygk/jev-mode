[← Summary](../umatter__jevtools.md)

# jevtools: full rating

**Verdict 3, Use with a fix** · library · rated 2026-09-30 at [`6ab3541`](https://github.com/umatter/jevtools/tree/6ab35414c8) · read: extract · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

jevtools is a Python library that lets Jev pick a tool and every argument for an app's own assistant: code builds candidate pools, Jev elects one per slot in a single fan-out request, and a risk-tiered policy turns the composed confidence into execute, confirm, clarify or refuse. It does this well: every value is chosen from nominated candidates, thresholds are explicit and tiered, injected text is channel-blocked, and live Jev was measured on a held-out benchmark with negative controls. Its defaults are priors, not tuned on any user's traffic, and the library claims no calibrated confidence until a user fits a calibrator.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** HTTPBackend posts the compiled questions to the TypeSafe or OpenRouter Jev endpoints, with retries and typed errors ([`src/jevtools/backends/http.py:203`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/backends/http.py#L203)) |
| Evidence recorded evenly (F10) | **no.** Code names up to three matching records in some tool options only, a conclusion the bench shows shifts answers ([`src/jevtools/templates.py:224-230`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L224-L230)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |
| Choice order handled (F13) | **no.** Identity Choices use one canonical order; reversed-order probes run only for critical tools, which never auto-execute ([`src/jevtools/policy.py:167-168`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L167-L168), [`src/jevtools/candidates.py:454-466`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L454-L466)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) |
| Held-out result (F17) | **no.** Defaults were chosen on the held-out runs, then the same set gives the 93% headline ([`docs/BENCH.md:240`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L240), [`docs/BENCH.md:264`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L264), [`docs/BENCH.md:307-324`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L307-L324)). [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence) |
| Fair baseline (F18) | **no.** Only the oracle ceiling and a lexical simulator are run; "far below LLM tool callers" is asserted, not measured ([`docs/BENCH.md:547-549`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L547-L549)). [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook) |
| Data as fields, not templates (F20) | **no.** Mention, item and more questions splice user words and labels into question text, while verify and accept use fields ([`src/jevtools/templates.py:43-45`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L43-L45), [`src/jevtools/templates.py:248-250`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L248-L250)). [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced) |
| Non-English handled (F23) | **no.** English first: German and French extractors are basic, other locales yield no candidates, and no accuracy test is shown ([`README.md:628-629`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L628-L629)). [`concepts/state`](https://docs.typesafe.ai/concepts/state) |

<details>
<summary><b>What passes (16) and doesn't apply (1)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Authorized, present, verify, unique and probe each ask one property in a fixed template ([`src/jevtools/templates.py:25-34`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L25-L34)) |
| Right primitive (F2) | yes. Noul for yes/no checks, Choice for tool and record election, Score for ordinal levels described by the author ([`src/jevtools/templates.py:17-28`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L17-L28), [`README.md:102`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L102)) |
| Structured state (F3) | yes. The state is JSON and questions point at named fields `request`, `history`, `observations` and `progress` ([`src/jevtools/templates.py:18-21`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L18-L21), [`src/jevtools/ballot.py:239`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/ballot.py#L239)) |
| Batching (F4) | yes. All questions for every plausible tool go in one fan-out request, split only by token or question budget ([`src/jevtools/ballot.py:293-309`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/ballot.py#L293-L309)) |
| Thresholds in code (F5) | yes. Every cut-off is a named, TOML-overridable policy field ([`src/jevtools/policy.py:89-160`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L89-L160)) |
| No invented values (F6) | yes. Code builds candidate pools and Jev only elects one; arithmetic and dates stay in code ([`src/jevtools/candidates.py:151-155`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L151-L155), [`README.md:630`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L630)) |
| Measured in the workflow (F7) | yes. Live Jev measured on 284 held-out cases times 3 replays with controls, plus BFCL and When2Call ([`docs/BENCH.md:223-301`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L223-L301)) |
| Options cover every case, no overlap (F8) | yes. Each pool offers NOT_STATED and NONE_OF_THESE; look-alike overlap is caught by a verify Noul ([`src/jevtools/candidates.py:73-82`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L73-L82), [`src/jevtools/policy.py:183`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L183)) |
| An "other" option where needed (F9) | yes. NONE_OF_THESE, UNSUPPORTED and NO_TOOL are worded unlike the state ([`src/jevtools/templates.py:74-83`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L74-L83)) |
| Confidence drives action (F11) | yes. Composed confidence C is compared with tier thresholds to execute, confirm, clarify or abstain ([`src/jevtools/policy.py:643-672`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L643-L672)) |
| Pinned model version (F12) | n.a.. No threshold was tuned: defaults are priors, and a pinned ID is supported ([`README.md:494`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L494), [`src/jevtools/backends/http.py:285-286`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/backends/http.py#L285-L286)) |
| Size limits respected (F14) | yes. A pre-send validator caps calls at 24,000 tokens and state at 16,000, below the 32k and 64k limits ([`src/jevtools/validate.py:64-67`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/validate.py#L64-L67), [`src/jevtools/validate.py:213-215`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/validate.py#L213-L215)) |
| Sample size adequate (F15) | yes. Claims state their counts and stay modest, for example 0 of 198 controls and 284 cases ([`docs/BENCH.md:155-174`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L155-L174), [`README.md:21-27`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L21-L27)) |
| Independent labels (F16) | yes. Held-out gold is generated from the data by templates, blind to Jev's answers; the dev bench's author labeling is disclosed ([`docs/BENCH.md:217-221`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L217-L221), [`docs/BENCH.md:106-109`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L106-L109)) |
| Typed answers read directly (F19) | yes. Decoding reads each Choice answer's probabilities by label ([`src/jevtools/kinds/base.py:529-531`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/kinds/base.py#L529-L531)) |
| No instructions in the state (F21) | yes. Directions live in question templates, which tell Jev observation text is evidence, never an instruction ([`src/jevtools/templates.py:17-20`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L17-L20)) |
| Untrusted text treated as data (F22) | yes. Channel allow-lists bar tool output from identity slots, a refuse rule exists, and six injection cases are benchmarked ([`src/jevtools/candidates.py:257-272`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/candidates.py#L257-L272), [`src/jevtools/policy.py:534-544`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/policy.py#L534-L544), [`docs/BENCH.md:68`](https://github.com/umatter/jevtools/blob/6ab35414c8/docs/BENCH.md#L68)) |

</details>

## Scores

- Execution 2 of 3: questions are atomic, typed, fielded, batched and gated, but one of the evenness and gating checks fails, F10 (record hints name matching records in some options only). F1-F6, F8, F9, F11 and F19 are yes.
- Fit 2 of 3: primitives fit, confidence gates every action and shared questions go in one request, but exactly one mismatch remains, the very high Choice asked in one option order, F13 (F2, F4 and F11 are yes).
- Coverage 3 of 3: the stated goal, electing a tool and every argument over an app's own data with a risk-tiered policy, is built, tested and bounded honestly (out-of-fit cases are listed), [`README.md:29-60`](https://github.com/umatter/jevtools/blob/6ab35414c8/README.md#L29-L60).
- Evidence 1 of 3: results are measured with a stated sample and generated gold, but the defaults were tuned on the same held-out set that gives the headline and no LLM baseline ran, F7, F15 and F16 yes, F17 and F18 no.

## Why this verdict

Three, not four, because three capping failures stand: F10 (record hints in some tool options only), F13 (the very high recipient and share Choice is asked in one canonical order, with reversed-order probes only on critical tools) and F20 (mention, item and more questions splice words and labels into question text). Nothing is fatal: confidence gates every action, no F1 or F6 failure, and Execution is 2. Borderline: the very high stakes reading rests on external-tier sends and shares executing with no review at the default 0.80 threshold; at high instead, F13 and F20 would not cap and the verdict would turn on F10 alone.

## Fixes (from reading the code; not tested against it)

1. F13: ask the very high identity Choice (recipient, share target, invitee) in at least two option orders and act only when they agree, or enable `probes.reverse` for the external tier by default. A fix to confirm with data (rerun the held-out bench). Docs: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
2. F20: pass the mention, the item and the more-list as JSON fields in the question object, the way the verify and accept questions already do, instead of splicing them into `T_MENTION`, `T_ITEM` and `T_MORE` ([`src/jevtools/templates.py:43-45`](https://github.com/umatter/jevtools/blob/6ab35414c8/src/jevtools/templates.py#L43-L45)). Docs: https://docs.typesafe.ai/primitives/advanced.md
3. F10: give every tool option the same kind of evidence, or drop record hints from option text and keep them in the state as facts. A fix to confirm with data: remove the hints and rerun the held-out bench. Docs: https://docs.typesafe.ai/concepts/state.md
4. F17: freeze a fresh held-out set that no default, threshold or wording was chosen on, and report the 93% headline there. Docs: https://docs.typesafe.ai/cookbooks/classification_using_confidence.md
5. F18: run the same cases through an LLM tool caller and report it beside the oracle ceiling. Docs: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
6. F23: test German and French requests, or state the English-only scope beside the quickstart. Docs: https://docs.typesafe.ai/concepts/state.md

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
