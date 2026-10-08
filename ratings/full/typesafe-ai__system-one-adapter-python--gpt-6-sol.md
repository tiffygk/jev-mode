[← Summary](../typesafe-ai__system-one-adapter-python--gpt-6-sol.md)

# system-one-adapter-python: full rating

**Not rated yet: replaces Jev** · jev replacement · rated 2026-10-06 at [`e1d4cc9`](https://github.com/typesafe-ai/system-one-adapter-python/tree/e1d4cc938204b22fc5a3c3aca7044072fe3f712d) · read: extract · rubric 2026-09-29.2 · gpt-6-sol, medium effort

## Summary

The adapter accepts TypeSafe `system_one` questions and produces TypeSafe-shaped answers using other LLM providers. It supports probability and discrete answers, schema validation, and provider error traces. Its replacement design falls under the pending replacement track rather than the Jev integration scores.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** src/system_one_adapter/_response.py,src/system_one_adapter/_schema.py,src/system_one_adapter/_utils/error_handling.py,src/system_one_adapter/providers/anthropic.py,src/system_one_adapter/providers/base.py,src/system_one_adapter/providers/gemini.py,src/system_one_adapter/providers/openai.py are SDK references, not hosted calls ([`src/system_one_adapter/_client.py:496`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc938204b22fc5a3c3aca7044072fe3f712d/src/system_one_adapter/_client.py#L496), [`src/system_one_adapter/providers/openai.py:153`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc938204b22fc5a3c3aca7044072fe3f712d/src/system_one_adapter/providers/openai.py#L153)). Docs: https://docs.typesafe.ai/introduction/quickstart.md, https://docs.typesafe.ai/sdk.md |

## Scores

- Execution n.a.; Fit n.a.; Coverage n.a.; Evidence n.a. (routed replacement).

## Why this verdict

The README explicitly describes a drop-in replacement backed by LLM APIs instead of TypeSafe ([`README.md:3`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc938204b22fc5a3c3aca7044072fe3f712d/README.md#L3)). The code routes evaluations through provider requests, so verdict code 1r applies pending a replacement rubric.

<details>
<summary><b>Files read (9; 62 skipped)</b></summary>

- .github/scripts/check_installed_distribution.py -- skipped: scoped
- .github/scripts/release_notes.py -- skipped: scoped
- .github/workflows/publish.yml -- skipped: scoped
- LICENSE -- skipped: scoped
- README.md -- read
- docs/changelog.md -- skipped: scoped
- pyproject.toml -- skipped: scoped
- src/system_one_adapter/__init__.py -- skipped: scoped
- src/system_one_adapter/_client.py -- read
- src/system_one_adapter/_response.py -- skipped: scoped
- src/system_one_adapter/_schema.py -- read
- src/system_one_adapter/_utils/__init__.py -- skipped: scoped
- src/system_one_adapter/_utils/confidence_metrics.py -- read
- src/system_one_adapter/_utils/error_handling.py -- skipped: scoped
- src/system_one_adapter/_utils/probability_normalization.py -- read
- src/system_one_adapter/providers/__init__.py -- skipped: scoped
- src/system_one_adapter/providers/anthropic.py -- skipped: scoped
- src/system_one_adapter/providers/base.py -- read
- src/system_one_adapter/providers/gemini.py -- skipped: scoped
- src/system_one_adapter/providers/openai.py -- read
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-native-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-native-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-native-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-prompted-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-prompted-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[discrete-prompted-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-native-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-native-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-native-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-prompted-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-prompted-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_models_follow_question_instructions_and_criteria[probabilities-prompted-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-native-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-native-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-native-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-prompted-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-prompted-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[discrete-prompted-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-native-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-native-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-native-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-prompted-anthropic].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-prompted-gemini].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_responses_match_reference_shape[probabilities-prompted-openai].json -- skipped: scoped
- tests/cassettes/test_client_with_live_apis/test_live_typesafe_response_matches_reference_shape.json -- skipped: scoped
- tests/conftest.py -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-native-anthropic].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-native-gemini].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-native-openai].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-prompted-anthropic].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-prompted-gemini].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[discrete-prompted-openai].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-native-anthropic].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-native-gemini].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-native-openai].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-prompted-anthropic].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-prompted-gemini].json -- skipped: scoped
- tests/expected_responses/test_live_responses_match_reference_shape[probabilities-prompted-openai].json -- skipped: scoped
- tests/expected_responses/test_live_typesafe_response_matches_reference_shape.json -- skipped: scoped
- tests/test_client_with_fake_model.py -- read
- tests/test_client_with_live_apis.py -- skipped: scoped
- tests/test_gemini_transports.py -- skipped: scoped
- tests/test_openai_transports.py -- skipped: scoped
- tests/test_provider_lifecycle.py -- skipped: scoped
- tests/test_provider_nonanswers.py -- read
- tests/test_provider_requests.py -- skipped: scoped
- tests/test_provider_retries.py -- skipped: scoped
- tests/test_schema.py -- skipped: scoped
- tests/utils/test_confidence_metrics.py -- skipped: scoped
- tests/utils/test_error_handling.py -- skipped: scoped
- tests/utils/test_probability_normalization.py -- skipped: scoped

</details>
