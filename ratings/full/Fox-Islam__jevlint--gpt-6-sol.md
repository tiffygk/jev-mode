[← Summary](../Fox-Islam__jevlint--gpt-6-sol.md)

# jevlint: full rating

**Verdict 4, Use it** · library · rated 2026-10-06 at [`582c0b8`](https://github.com/Fox-Islam/jevlint/tree/582c0b8be072fb0d14fcaa5bd72b278205543ed7) · read: extract · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

jevlint imports hosted Jev to inspect query designs and returns lint findings and probe readings to its users. It combines static shape checks with bundled Jev questions and a probe for answer movement. Its measured evidence is uneven across checks, and several checks have no independent positive labels.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **yes.** Python client sends question batches through TypeSafe SDK System One ([`python/src/jevlint/typesafe/client.py:103`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/typesafe/client.py#L103)). |
| Pinned model version (F12) | **no.** Tuned triggers coexist with SDK's floating default model ([`python/src/jevlint/typesafe/client.py:86`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/typesafe/client.py#L86)). https://docs.typesafe.ai/models |
| Size limits respected (F14) | **no.** State guard counts characters, while model requests lack a total-token guard ([`python/src/jevlint/static_linter.py:65`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/static_linter.py#L65)). https://docs.typesafe.ai/models |
| Held-out result (F17) | **no.** Published corpus readings also guided wording and trigger revisions, without a distinct final holdout ([`docs/evidence.md:113`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L113)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Fair baseline (F18) | **no.** Answer arms compare original and repaired queries, but no alternative linter on the same task ([`docs/evidence.md:376`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L376)). https://docs.typesafe.ai/concepts/how-to-build-with-system-one |
| Data as fields, not templates, low (F20) | **no.** Two reviewed instructions are interpolated into one query-check instruction ([`python/src/jevlint/model_linter.py:203`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L203)). https://docs.typesafe.ai/primitives/advanced |

<details>
<summary><b>What passes (15) and doesn't apply (3)</b></summary>

| Fact | Finding |
|---|---|
| Atomic questions (F1) | yes. Catalogue checks isolate one defect per Jev question ([`checks/catalogue.json:314`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/checks/catalogue.json#L314)). |
| Right primitive (F2) | yes. Defect checks use Nouls; type comparison uses Choice with primitive labels ([`python/src/jevlint/model_linter.py:551`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L551)). |
| Structured state (F3) | yes. Reviewed questions travel as named instruction and criteria fields ([`python/src/jevlint/model_linter.py:433`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L433)). |
| Batching (F4) | yes. All checks for a reviewed question share one request; query pairs also share one ([`python/src/jevlint/model_linter.py:433`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L433)). |
| Thresholds in code (F5) | yes. Named catalogue triggers determine findings ([`checks/catalogue.json:314`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/checks/catalogue.json#L314)). |
| No invented values (F6) | yes. Jev judges query defects and returns typed probabilities or labels ([`python/src/jevlint/model_linter.py:743`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L743)). |
| Measured in the workflow (F7) | yes. Corpus reports check firing, answer impact, and 1,173 calls ([`docs/evidence.md:98`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L98)). |
| Options cover every case, no overlap (F8) | yes. Primitive comparison includes noul, choice, score and other ([`checks/catalogue.json:729`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/checks/catalogue.json#L729)). |
| An other option where needed (F9) | yes. Primitive comparison includes other; locators only annotate findings ([`checks/catalogue.json:729`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/checks/catalogue.json#L729)). |
| Evidence recorded evenly (F10) | n.a.. Each reviewed query is a single object, without per-answer evidence ([`python/src/jevlint/model_linter.py:433`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L433)). |
| Confidence drives action, low (F11) | n.a.. Findings and probe readings are returned for user review ([`corpus/README.md:48`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/corpus/README.md#L48)). |
| Choice order handled, low (F13) | n.a.. Low-stakes Choice findings are returned for review ([`python/src/jevlint/model_linter.py:892`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L892)). |
| Sample size adequate (F15) | yes. Claims give denominators and limit conclusions from small samples ([`docs/evidence.md:204`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L204)). |
| Independent labels (F16) | yes. Gold negatives cite TypeSafe prose; decision-v7 and SQuAD supply outside labels ([`corpus/README.md:7`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/corpus/README.md#L7)). |
| Typed answers read directly (F19) | yes. Noul probabilities and Choice labels are read from typed response wrappers ([`python/src/jevlint/model_linter.py:1042`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L1042)). |
| No instructions in the state (F21) | yes. Reviewed instructions appear as the object being judged, not directions to the checker ([`python/src/jevlint/model_linter.py:433`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/python/src/jevlint/model_linter.py#L433)). |
| Untrusted text treated as data, low (F22) | yes. Planted assessor-directed text was tested on 20 cases, all detected ([`docs/evidence.md:638`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L638)). |
| Non-English handled (F23) | yes. FLORES-200 language variants were tested against the irrelevant-field check ([`docs/evidence.md:745`](https://github.com/Fox-Islam/jevlint/blob/582c0b8be072fb0d14fcaa5bd72b278205543ed7/docs/evidence.md#L745)). |

</details>

## Scores

- Execution 3 of 3: atomic typed checks are batched over structured query state, and findings use catalogue thresholds (F1-F6, F8-F11, F19).
- Fit 3 of 3: the linter uses Noul and Choice where they fit and batches checks; probe reads typed variants (F2, F4, F19).
- Coverage 3 of 3: static and model checks plus probe cover its stated query-linting goal; limits are explicitly documented (F7, F23).
- Evidence 1 of 3: numerous labeled measurements are disclosed, but tuning used published corpus readings and no alternative linter baseline is shown (F7, F15-F18).

## Why this verdict

The hosted calls support a usable linter: typed checks are batched, thresholds produce reviewable findings, and the project measures several real failure modes. No execution or fit fact caps the verdict, so it reaches 4. It does not reach 5 because its evidence lacks a distinct final holdout and a fair alternative baseline. Floating model defaults and unguarded request size remain practical gaps.

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
