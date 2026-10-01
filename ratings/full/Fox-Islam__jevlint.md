[← Summary](../Fox-Islam__jevlint.md)

# jevlint: full rating

**Verdict 4, Use it** · library · rated 2026-09-30 at [`582c0b8`](https://github.com/Fox-Islam/jevlint/tree/582c0b8be0) · read: extract · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

A linter that sends a user's Jev query to Jev as state and asks 25 calibrated yes/no checks about it, reporting findings by severity.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Builds and sends System One calls through the TypeSafe SDK for every model check and probe ([`python/src/jevlint/typesafe/client.py:103`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/typesafe/client.py#L103)) |
| Pinned model version (F12) | **no.** Default is the SDK's `jev-latest` though triggers were tuned for jev-1.13; a `--model` pin is optional ([`python/src/jevlint/typesafe/client.py:96`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/typesafe/client.py#L96)). docs.typesafe.ai/models |
| Held-out result (F17) | **no.** Wordings and triggers were changed after reading the same corpus tiers whose rates are then reported ([`docs/evidence.md:322`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L322)). docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Fair baseline (F18) | **no.** Arms compare a check with its repaired query or a coin flip; no rules or LLM baseline ([`docs/evidence.md:944`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L944)). docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Data as fields, not templates (F20) | **no.** The pair check splices both question texts into the Noul instruction, and the field check a field name ([`python/src/jevlint/model_linter.py:210`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L210)). docs.typesafe.ai/primitives/advanced |
| Untrusted text treated as data (F22) | **no.** Reviewed question text and user state go in with no source marker or injection test of its calls ([`python/src/jevlint/model_linter.py:452`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L452)). docs.typesafe.ai/model-jaggedness/jev-1.13 |
| Non-English handled (F23) | **no.** Only the spare-field check was tried across languages; reviewed questions and gold items are English ([`docs/evidence.md:743`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L743)). docs.typesafe.ai/models |

<details>
<summary><b>What passes (15) and doesn't apply (2)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Each of the 31 check wordings asks one property of the reviewed query, with its standard in the criteria ([`checks/catalogue.json:316`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L316)) |
| Right primitive (F2) | yes. Defect presence is a Noul, the type check a Choice over noul/choice/score/other, locators Choice or Noul ([`checks/catalogue.json:714`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L714)) |
| Structured state (F3) | yes. The reviewed question goes in as `{instructions, criteria}` and questions point at those paths; the pair call sends a list ([`python/src/jevlint/model_linter.py:431`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L431)) |
| Batching (F4) | yes. Every question-scoped check for one reviewed question rides in one request, state-scoped ones in another ([`python/src/jevlint/model_linter.py:430`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L430)) |
| Thresholds in code (F5) | yes. Each check's trigger lives in the catalogue, the near and worth-seeing bands as class constants ([`checks/catalogue.json:384`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L384), [`python/src/jevlint/model_linter.py:54`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L54)) |
| No invented values (F6) | yes. Jev only judges whether a defect is present; means, spreads, trigger comparison and patches are computed in code ([`python/src/jevlint/model_linter.py:743`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L743)) |
| Measured in the workflow (F7) | yes. Per-check tables with counts on docs, SQuAD, decision-v7 and planted-defect corpora, including a Brier score ([`docs/evidence.md:94`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L94)) |
| Options cover every case, no overlap (F8) | yes. The type check's four options are exclusive and each is described, with the boundary between choice and score spelled out ([`checks/catalogue.json:714`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L714)) |
| An "other" option where needed (F9) | yes. The type check carries an `other` option for answers a reader would write down ([`checks/catalogue.json:714`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L714)) |
| Evidence recorded evenly (F10) | n.a.. One reviewed question or one user-supplied state is judged, with no per-answer evidence list ([`python/src/jevlint/model_linter.py:431`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L431)) |
| Confidence drives action, low (F11) | yes. A finding is raised only above the check's trigger; readings within 0.05 are re-asked and may report undecided ([`python/src/jevlint/model_linter.py:743`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L743)) |
| Choice order handled, low (F13) | n.a.. Always n.a. ([`python/src/jevlint/model_linter.py:887`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L887)) |
| Size limits respected (F14) | yes. A static rule warns above 20000 state characters and pair checks stop above 12 questions, though sending continues ([`python/src/jevlint/static_linter.py:151`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/static_linter.py#L151)) |
| Sample size adequate (F15) | yes. Counts are stated per cell, a denominator of 1 is called out, and the gold set is called small ([`corpus/README.md:197`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/corpus/README.md#L197)) |
| Independent labels (F16) | yes. Labels come from the TypeSafe docs, decision-v7, SQuAD and Quora; four written-from-definition gold items are disclosed ([`docs/evidence.md:146`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/docs/evidence.md#L146)) |
| Typed answers read directly (F19) | yes. Code reads the typed `noul` probability and Choice `probabilities`, never reasoning text ([`python/src/jevlint/model_linter.py:981`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L981)) |
| No instructions in the state (F21) | yes. The state holds the reviewed question's own fields and the user's state; directions sit in the check wordings ([`python/src/jevlint/model_linter.py:431`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/python/src/jevlint/model_linter.py#L431)) |

</details>

## Scores

- Execution 3 of 3: every question is atomic, typed, fielded, batched and gated by a trigger in the catalogue, with the type check carrying an other option (F1-F6, F8, F9, F11, F19).
- Fit 3 of 3: each decision uses the fitting primitive, the probability gates every finding and exit code, and one request carries each question's checks (F2, F4, F11).
- Coverage 3 of 3: the README promises checks against each documented failure mode and the catalogue holds a model check for each of them ([`checks/catalogue.json:316`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be0/checks/catalogue.json#L316)).
- Evidence 2 of 3: measured on labels from others with stated samples, but wordings were adjusted on the same corpus and no plain-LLM or rules baseline was run (F15, F16, F17, F18).

## Why this verdict

4, Use it. No capping failure: F1-F6, F8-F11, F19 and F21 all hold, F13, F20 and F22 sit on low decisions, and Fit is 3. It is not a 5 because Evidence is 2, with F17 (wordings changed after reading the corpus) and F18 (no rules or plain-LLM baseline) failing. Every decision stays with the person linting their own query and a patch is offered, never applied.

## Fixes (from reading the code; not tested against it)

1. F17: hold out a slice of the gold and docs tiers that no wording or trigger change ever sees, and report that slice. Source: [`cookbooks/classification_using_confidence`](https://docs.typesafe.ai/cookbooks/classification_using_confidence).
2. F18: run a keyword-rules linter and a plain-LLM prompt over the same gold set and report both beside the checks. Source: [`cookbooks/consistency_choice_cookbook`](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook).
3. F12: default the client to a versioned `jev-1.13.x` ID, since triggers were tuned for that build, and log the `model` each response names. Source: [`models`](https://docs.typesafe.ai/models).
4. F20 and F22 (fix-only at low stakes): pass the pair and element text as state fields, and test whether a planted instruction in a reviewed question moves the pair or locator readings. Confirmed only with data. Source: [`primitives/advanced`](https://docs.typesafe.ai/primitives/advanced); [`model-jaggedness/jev-1.13`](https://docs.typesafe.ai/model-jaggedness/jev-1.13).

<details>
<summary><b>Files read (13; 230 skipped)</b></summary>

- README.md -- read
- checks/catalogue.json -- read
- checks/fixtures.json -- skipped: scoped
- composer.json -- skipped: scoped
- corpus/README.md -- read
- corpus/advice.py -- skipped: scoped
- corpus/answers.py -- read
- corpus/arms/cc-sample.json -- skipped: scoped
- corpus/arms/dn-sample.json -- skipped: scoped
- corpus/arms/score-sample.json -- skipped: scoped
- corpus/arms/wq-sample.json -- skipped: scoped
- corpus/borderline.py -- skipped: scoped
- corpus/boundary.py -- skipped: scoped
- corpus/build.py -- skipped: scoped
- corpus/contradiction.py -- skipped: scoped
- corpus/decision.py -- skipped: scoped
- corpus/docs-examples.json -- skipped: scoped
- corpus/dogfood.py -- skipped: scoped
- corpus/drift.py -- skipped: scoped
- corpus/encoded.py -- skipped: scoped
- corpus/external.py -- skipped: scoped
- corpus/families.py -- skipped: scoped
- corpus/field.json -- skipped: scoped
- corpus/fields.py -- skipped: scoped
- corpus/flores.py -- skipped: scoped
- corpus/gold.json -- read
- corpus/harvest.py -- skipped: scoped
- corpus/labels.json -- skipped: scoped
- corpus/labels.py -- skipped: scoped
- corpus/levels.py -- skipped: scoped
- corpus/locators.py -- skipped: scoped
- corpus/measure.py -- skipped: scoped
- corpus/mechanical.py -- skipped: scoped
- corpus/pages.py -- skipped: scoped
- corpus/planted.py -- skipped: scoped
- corpus/position.py -- skipped: scoped
- corpus/rewrite.py -- skipped: scoped
- corpus/scores.json -- skipped: scoped
- corpus/second.py -- skipped: scoped
- corpus/sibling.py -- skipped: scoped
- corpus/squad.py -- skipped: scoped
- corpus/states.py -- skipped: scoped
- corpus/sums.py -- skipped: scoped
- corpus/undetermined.py -- skipped: scoped
- corpus/unread.py -- skipped: scoped
- corpus/wording.py -- skipped: scoped
- docs/behaviour.md -- skipped: scoped
- docs/evidence.md -- read
- docs/javascript.md -- skipped: scoped
- docs/languages.md -- skipped: scoped
- docs/library.md -- skipped: scoped
- docs/output.md -- skipped: scoped
- docs/python.md -- skipped: scoped
- examples/broken-triage.json -- skipped: scoped
- examples/support-triage.json -- skipped: scoped
- js/bin/jevlint.ts -- skipped: scoped
- js/src/catalogue/catalogue.ts -- skipped: scoped
- js/src/catalogue/check.ts -- skipped: scoped
- js/src/catalogue/wording.ts -- skipped: scoped
- js/src/config/config.ts -- skipped: scoped
- js/src/console/application.ts -- skipped: scoped
- js/src/console/args.ts -- skipped: scoped
- js/src/console/commands/checkCommand.ts -- skipped: scoped
- js/src/console/commands/checksCommand.ts -- skipped: scoped
- js/src/console/commands/probeCommand.ts -- skipped: scoped
- js/src/console/commands/selfTestCommand.ts -- skipped: scoped
- js/src/console/flags.ts -- skipped: scoped
- js/src/exceptions/jevLintError.ts -- skipped: scoped
- js/src/format/colour.ts -- skipped: scoped
- js/src/format/numbers.ts -- skipped: scoped
- js/src/format/probeFormatter.ts -- skipped: scoped
- js/src/format/selfTestFormatter.ts -- skipped: scoped
- js/src/format/textFormatter.ts -- skipped: scoped
- js/src/i18n/checkText.ts -- skipped: scoped
- js/src/i18n/text.ts -- skipped: scoped
- js/src/index.ts -- skipped: scoped
- js/src/lang/en.ts -- skipped: scoped
- js/src/lint/clientFactory.ts -- skipped: scoped
- js/src/lint/linter.ts -- skipped: scoped
- js/src/lint/modelLinter.ts -- skipped: scoped
- js/src/lint/rules.ts -- skipped: scoped
- js/src/lint/staticLinter.ts -- skipped: scoped
- js/src/probe/probe.ts -- skipped: scoped
- js/src/probe/questionBuilder.ts -- skipped: scoped
- js/src/probe/questionProbe.ts -- skipped: scoped
- js/src/probe/variant.ts -- skipped: scoped
- js/src/probe/variants.ts -- skipped: scoped
- js/src/query/query.ts -- skipped: scoped
- js/src/query/reviewedQuestion.ts -- skipped: scoped
- js/src/report/finding.ts -- skipped: scoped
- js/src/report/patch.ts -- skipped: scoped
- js/src/report/report.ts -- skipped: scoped
- js/src/selftest/checkScore.ts -- skipped: scoped
- js/src/selftest/selfTest.ts -- skipped: scoped
- js/src/support/cause.ts -- skipped: scoped
- js/src/support/env.ts -- skipped: scoped
- js/src/support/json.ts -- skipped: scoped
- js/src/support/ordered.ts -- skipped: scoped
- js/src/support/phpJson.ts -- skipped: scoped
- js/src/typesafe/answers.ts -- skipped: scoped
- js/src/typesafe/client.ts -- skipped: scoped
- js/src/typesafe/errors.ts -- skipped: scoped
- js/src/typesafe/questions.ts -- skipped: scoped
- js/test/anotherLanguage.test.ts -- skipped: scoped
- js/test/catalogue.test.ts -- skipped: scoped
- js/test/helpers/fake.ts -- skipped: scoped
- js/test/icu.test.ts -- skipped: scoped
- js/test/linter.test.ts -- skipped: scoped
- js/test/numbers.test.ts -- skipped: scoped
- js/test/ordered.test.ts -- skipped: scoped
- js/test/package.test.ts -- skipped: scoped
- js/test/parity.test.ts -- skipped: scoped
- js/test/patch.test.ts -- skipped: scoped
- js/test/probe.test.ts -- skipped: scoped
- js/test/query.test.ts -- skipped: scoped
- js/test/stateFieldChecks.test.ts -- skipped: scoped
- js/test/staticLinter.test.ts -- skipped: scoped
- package.json -- skipped: scoped
- php/lang/en.php -- skipped: scoped
- php/src/Catalogue/Catalogue.php -- skipped: scoped
- php/src/Catalogue/Check.php -- skipped: scoped
- php/src/Catalogue/SecondQuestion.php -- skipped: scoped
- php/src/Catalogue/Wording.php -- skipped: scoped
- php/src/Config/Config.php -- skipped: scoped
- php/src/Console/Application.php -- skipped: scoped
- php/src/Console/Args.php -- skipped: scoped
- php/src/Console/Commands/CheckCommand.php -- skipped: scoped
- php/src/Console/Commands/ChecksCommand.php -- skipped: scoped
- php/src/Console/Commands/ProbeCommand.php -- skipped: scoped
- php/src/Console/Commands/SelfTestCommand.php -- skipped: scoped
- php/src/Console/Flags.php -- skipped: scoped
- php/src/Exceptions/JevLintException.php -- skipped: scoped
- php/src/Format/ProbeFormatter.php -- skipped: scoped
- php/src/Format/SelfTestFormatter.php -- skipped: scoped
- php/src/Format/TextFormatter.php -- skipped: scoped
- php/src/I18n/CheckText.php -- skipped: scoped
- php/src/Lint/ClientFactory.php -- skipped: scoped
- php/src/Lint/Linter.php -- skipped: scoped
- php/src/Lint/ModelLinter.php -- skipped: scoped
- php/src/Lint/StaticLinter.php -- skipped: scoped
- php/src/Probe/Probe.php -- skipped: scoped
- php/src/Probe/QuestionBuilder.php -- skipped: scoped
- php/src/Probe/QuestionProbe.php -- skipped: scoped
- php/src/Probe/Reading.php -- skipped: scoped
- php/src/Probe/Variant.php -- skipped: scoped
- php/src/Probe/Variants/CriteriaStripped.php -- skipped: scoped
- php/src/Probe/Variants/KeysHidden.php -- skipped: scoped
- php/src/Probe/Variants/LevelsReversed.php -- skipped: scoped
- php/src/Probe/Variants/NoulAsChoice.php -- skipped: scoped
- php/src/Probe/Variants/OptionsReversed.php -- skipped: scoped
- php/src/Probe/Variants/Reworded.php -- skipped: scoped
- php/src/Probe/Variants/Unchanged.php -- skipped: scoped
- php/src/Query/Query.php -- skipped: scoped
- php/src/Query/ReviewedQuestion.php -- skipped: scoped
- php/src/Report/Finding.php -- skipped: scoped
- php/src/Report/Patch.php -- skipped: scoped
- php/src/Report/Report.php -- skipped: scoped
- php/src/SelfTest/SelfTest.php -- skipped: scoped
- php/src/Support/Cause.php -- skipped: scoped
- php/tests/AnotherLanguageTest.php -- skipped: scoped
- php/tests/AskedDigestTest.php -- skipped: scoped
- php/tests/CatalogueLintsCleanTest.php -- skipped: scoped
- php/tests/CatalogueTest.php -- skipped: scoped
- php/tests/DeclaredExtensionsTest.php -- skipped: scoped
- php/tests/DocumentationMatchesCatalogueTest.php -- skipped: scoped
- php/tests/EveryStateFieldCheckReportsItselfTest.php -- skipped: scoped
- php/tests/EvidenceCountsMatchTheDataTest.php -- skipped: scoped
- php/tests/FindingCarriesEveryFieldTest.php -- skipped: scoped
- php/tests/GuardsTest.php -- skipped: scoped
- php/tests/InconclusiveChecksSpeakEitherWayTest.php -- skipped: scoped
- php/tests/LinterFacadeTest.php -- skipped: scoped
- php/tests/LostCallsAreNotAPassTest.php -- skipped: scoped
- php/tests/ModelLinterTest.php -- skipped: scoped
- php/tests/PatchNeverEmptiesTheQueryTest.php -- skipped: scoped
- php/tests/PatchTest.php -- skipped: scoped
- php/tests/PatchesKeepWhatTheyClaimTest.php -- skipped: scoped
- php/tests/ProbeNumbersMatchTheDocumentationTest.php -- skipped: scoped
- php/tests/ProbeTest.php -- skipped: scoped
- php/tests/QuickstartWorksTest.php -- skipped: scoped
- php/tests/ReportContractTest.php -- skipped: scoped
- php/tests/StaticChecksApplyWhereTheySayTest.php -- skipped: scoped
- php/tests/StaticLinterTest.php -- skipped: scoped
- php/tests/StaticRulesAreBoundTest.php -- skipped: scoped
- pyproject.toml -- skipped: scoped
- python/src/jevlint/__init__.py -- skipped: scoped
- python/src/jevlint/__main__.py -- skipped: scoped
- python/src/jevlint/catalogue.py -- skipped: scoped
- python/src/jevlint/config.py -- skipped: scoped
- python/src/jevlint/console/__init__.py -- skipped: scoped
- python/src/jevlint/console/application.py -- skipped: scoped
- python/src/jevlint/console/args.py -- skipped: scoped
- python/src/jevlint/console/commands.py -- skipped: scoped
- python/src/jevlint/console/flags.py -- skipped: scoped
- python/src/jevlint/errors.py -- skipped: scoped
- python/src/jevlint/formatting.py -- skipped: scoped
- python/src/jevlint/icu.py -- skipped: scoped
- python/src/jevlint/lang/en.py -- skipped: scoped
- python/src/jevlint/linter.py -- skipped: scoped
- python/src/jevlint/model_linter.py -- read
- python/src/jevlint/probe.py -- read
- python/src/jevlint/probe_formatter.py -- skipped: scoped
- python/src/jevlint/query.py -- skipped: scoped
- python/src/jevlint/report.py -- skipped: scoped
- python/src/jevlint/rules.py -- skipped: scoped
- python/src/jevlint/self_test_formatter.py -- skipped: scoped
- python/src/jevlint/selftest.py -- skipped: scoped
- python/src/jevlint/static_linter.py -- read
- python/src/jevlint/support.py -- skipped: scoped
- python/src/jevlint/text.py -- skipped: scoped
- python/src/jevlint/text_formatter.py -- skipped: scoped
- python/src/jevlint/typesafe/__init__.py -- skipped: scoped
- python/src/jevlint/typesafe/answers.py -- read
- python/src/jevlint/typesafe/client.py -- read
- python/src/jevlint/typesafe/errors.py -- skipped: scoped
- python/src/jevlint/typesafe/questions.py -- read
- python/src/jevlint/variants.py -- read
- python/tests/conftest.py -- skipped: scoped
- python/tests/test_catalogue.py -- skipped: scoped
- python/tests/test_documentation.py -- skipped: scoped
- python/tests/test_icu.py -- skipped: scoped
- python/tests/test_linter.py -- skipped: scoped
- python/tests/test_numbers.py -- skipped: scoped
- python/tests/test_package.py -- skipped: scoped
- python/tests/test_parity.py -- skipped: scoped
- python/tests/test_patch.py -- skipped: scoped
- python/tests/test_probe.py -- skipped: scoped
- python/tests/test_query.py -- skipped: scoped
- python/tests/test_state_field_checks.py -- skipped: scoped
- python/tests/test_static_linter.py -- skipped: scoped
- site/behaviour.html -- skipped: scoped
- site/corpus.html -- skipped: scoped
- site/evidence.html -- skipped: scoped
- site/examples.html -- skipped: scoped
- site/index.html -- skipped: scoped
- site/javascript.html -- skipped: scoped
- site/languages.html -- skipped: scoped
- site/library.html -- skipped: scoped
- site/output.html -- skipped: scoped
- site/python.html -- skipped: scoped
- site/spec/query.schema.json -- skipped: scoped
- site/spec/report.schema.json -- skipped: scoped
- spec/query.schema.json -- skipped: scoped
- spec/report.schema.json -- skipped: scoped

</details>
