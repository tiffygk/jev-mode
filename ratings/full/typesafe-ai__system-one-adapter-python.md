[← Summary](../typesafe-ai__system-one-adapter-python.md)

# system-one-adapter-python: full rating

**Verdict 1, Replaces Jev, not yet rated** · jev replacement · rated 2026-09-30 at [`e1d4cc9`](https://github.com/typesafe-ai/system-one-adapter-python/tree/e1d4cc9382) · read: extract · rubric 2026-09-29 · claude-sonnet-5-5, medium effort

## Summary

This Python package imitates TypeSafe's `system_one` API by sending the same Noul, Choice and Score questions to OpenAI, Anthropic or Gemini models and returning typed answers. It validates output against a per-request schema, retries malformed output, normalizes probabilities and derives confidence, and its README says it is for comparing TypeSafe against an LLM. It never calls hosted Jev and does not claim to, so it is routed 1r until a replacement track exists.

## What fails

| Fact | Finding |
|---|---|
| Calls hosted Jev (F0) | **no.** Requests go to LLM provider SDKs, never TypeSafe ([`src/system_one_adapter/providers/openai.py:153`](https://github.com/typesafe-ai/system-one-adapter-python/blob/e1d4cc9382/src/system_one_adapter/providers/openai.py#L153)). Flagged files `src/system_one_adapter/__init__.py` `src/system_one_adapter/_client.py` `src/system_one_adapter/_response.py` `src/system_one_adapter/_schema.py` `src/system_one_adapter/providers/anthropic.py` `src/system_one_adapter/providers/base.py` `src/system_one_adapter/providers/gemini.py` `src/system_one_adapter/providers/openai.py` `tests/test_gemini_transports.py` `tests/test_openai_transports.py` `tests/test_provider_nonanswers.py` `tests/test_provider_retries.py` `tests/utils/test_error_handling.py` import only SDK types and errors, no client. https://docs.typesafe.ai/llms.txt |

## Scores

- n.a. for all four: a project routed 1r has no Jev call to score.

## Why this verdict

Verdict 1, code 1r: the package offers others Jev-style answers through an LLM and its README describes it as a drop-in replacement for the `system_one` API, not as calling Jev. It makes no hosted Jev call and makes no claim to, so 1a does not apply. The code routes by type, not by quality, so no score or fix list applies.

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
