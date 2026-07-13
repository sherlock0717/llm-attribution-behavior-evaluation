"""Unit tests for the minimal Pydantic schemas (FND-006)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from freewill_attribution.schemas import (
    ErrorSeverity,
    ErrorType,
    ExtensibleModel,
    ItemsBatching,
    ModelConfig,
    NormalizedResponse,
    ParseStatus,
    RunManifest,
    StimulusReference,
    ValidationError,
    validate_normalized_response,
    validation_errors_from_pydantic,
)

VALID_STIMULUS_REF = {
    "scenario_id": "s1",
    "process_condition": "direct_choice",
    "identity_label": "AI",
}

VALID_NORMALIZED = {
    "participant_id": "p1",
    "stimulus_ref": dict(VALID_STIMULUS_REF),
    "ratings": {"q1": 3, "q2": None},
    "attention_check": "ok",
    "short_reason": "because reasons",
}

VALID_MODEL_CONFIG = {
    "provider": "mock",
    "model": "rule-based-v1",
    "temperature": 1.0,
    "max_tokens": 2800,
    "response_format": "json_object",
}

VALID_PROMPT_CONFIG = {
    "prompt_id": "legacy-inline-v1",
    "version": "v1",
    "items_batching": "all",
    "system_template": "legacy-inline-v1",
    "user_template": "legacy-inline-v1",
}

VALID_MANIFEST = {
    "run_id": "r1",
    "git_commit_sha": "abc123",
    "study_config_ref": "study.default.yaml",
    "model_config": dict(VALID_MODEL_CONFIG),
    "prompt_config": dict(VALID_PROMPT_CONFIG),
    "stimuli_version": "v1",
    "scales_version": "v1",
    "python_version": "3.12.10",
    "dependency_lock_hash": "deadbeef",
    "seed": 20260425,
    "started_at": "2026-07-13T10:00:00",
}


def _errors_for(payload) -> list[ValidationError]:
    with pytest.raises(PydanticValidationError) as excinfo:
        NormalizedResponse.model_validate(payload)
    return validation_errors_from_pydantic(excinfo.value)


def _manifest(**overrides):
    return RunManifest.model_validate({**VALID_MANIFEST, **overrides})


# 1-3 enums --------------------------------------------------------------


def test_error_type_members():
    assert {member.value for member in ErrorType} == {
        "api",
        "parse",
        "schema",
        "range",
        "missing",
        "runtime",
    }


def test_error_severity_members():
    assert {member.value for member in ErrorSeverity} == {"warn", "error"}


def test_parse_status_members():
    assert {member.value for member in ParseStatus} == {"ok", "repaired", "failed"}


def test_items_batching_members():
    assert {member.value for member in ItemsBatching} == {"all", "by_scale", "single"}


# 4-5 ValidationError ----------------------------------------------------


def test_validation_error_creates_and_serializes():
    err = ValidationError(type=ErrorType.MISSING, message="field required")
    dumped = err.model_dump()
    assert dumped["type"] == ErrorType.MISSING
    assert dumped["severity"] == ErrorSeverity.ERROR
    assert dumped["item_id"] is None
    assert dumped["context"] == {}
    assert isinstance(err.model_dump_json(), str)


def test_validation_error_preserves_extra_field():
    err = ValidationError(type=ErrorType.SCHEMA, message="bad", note="keep me")
    assert err.model_dump()["note"] == "keep me"


# 6-8 extensible models --------------------------------------------------


def test_normalized_response_valid_payload():
    model = NormalizedResponse.model_validate(VALID_NORMALIZED)
    assert model.participant_id == "p1"
    assert model.parse_status is ParseStatus.OK
    assert model.errors == []
    assert model.metadata == {}


def test_normalized_response_preserves_top_level_extra():
    payload = {**VALID_NORMALIZED, "provider_hint": "mock"}
    model = NormalizedResponse.model_validate(payload)
    assert model.model_dump()["provider_hint"] == "mock"


def test_stimulus_reference_preserves_extra():
    ref = StimulusReference.model_validate(
        {**VALID_STIMULUS_REF, "domain": "medical", "content_hash": "abc"}
    )
    dumped = ref.model_dump()
    assert dumped["domain"] == "medical"
    assert dumped["content_hash"] == "abc"


# 9-11 ratings -----------------------------------------------------------


def test_ratings_allow_int_and_none():
    model = NormalizedResponse.model_validate(VALID_NORMALIZED)
    assert model.ratings == {"q1": 3, "q2": None}


def test_ratings_reject_empty_key():
    payload = {**VALID_NORMALIZED, "ratings": {"": 1}}
    with pytest.raises(PydanticValidationError):
        NormalizedResponse.model_validate(payload)


@pytest.mark.parametrize("bad_value", ["3", 3.0, 1.5, [1, 2], {"nested": 1}])
def test_ratings_reject_non_int_values(bad_value):
    # bool is intentionally excluded (bool is a subclass of int).
    payload = {**VALID_NORMALIZED, "ratings": {"q1": bad_value}}
    with pytest.raises(PydanticValidationError):
        NormalizedResponse.model_validate(payload)


def test_ratings_do_not_coerce_numeric_string():
    payload = {**VALID_NORMALIZED, "ratings": {"q1": "3"}}
    with pytest.raises(PydanticValidationError) as excinfo:
        NormalizedResponse.model_validate(payload)
    assert any(err["type"] == "int_type" for err in excinfo.value.errors())


def test_ratings_do_not_coerce_integral_float():
    payload = {**VALID_NORMALIZED, "ratings": {"q1": 3.0}}
    with pytest.raises(PydanticValidationError) as excinfo:
        NormalizedResponse.model_validate(payload)
    assert any(err["type"] == "int_type" for err in excinfo.value.errors())


def test_ratings_accept_int_none_and_negative():
    model = NormalizedResponse.model_validate(
        {**VALID_NORMALIZED, "ratings": {"q1": 3, "q2": None, "q3": -1, "q4": 0}}
    )
    assert model.ratings == {"q1": 3, "q2": None, "q3": -1, "q4": 0}


def test_structured_error_preserves_full_location():
    payload = {**VALID_NORMALIZED, "ratings": {"q1": "3"}}
    errors = _errors_for(payload)
    matching = [e for e in errors if e.item_id == "q1"]
    assert len(matching) >= 1
    err = matching[0]
    assert err.context["loc"] == ["ratings", "q1"]
    assert err.context["pydantic_type"] == "int_type"


def test_missing_error_preserves_field_location():
    payload = {k: v for k, v in VALID_NORMALIZED.items() if k != "participant_id"}
    errors = _errors_for(payload)
    matching = [e for e in errors if e.context["loc"] == ["participant_id"]]
    assert len(matching) == 1
    assert matching[0].context["pydantic_type"] == "missing"
    assert matching[0].type is ErrorType.MISSING


def test_extensible_model_keeps_pydantic_protected_namespaces():
    with pytest.raises(ValueError, match="model_dump"):

        class InvalidExtensionModel(ExtensibleModel):
            model_dump: str


# 12-14 error classification --------------------------------------------


def test_missing_participant_id_classified_missing():
    payload = {k: v for k, v in VALID_NORMALIZED.items() if k != "participant_id"}
    errors = _errors_for(payload)
    assert any(e.type is ErrorType.MISSING for e in errors)


def test_negative_count_classified_range():
    with pytest.raises(PydanticValidationError) as excinfo:
        _manifest(n_records=-1)
    errors = validation_errors_from_pydantic(excinfo.value)
    assert any(e.type is ErrorType.RANGE for e in errors)


def test_ratings_as_list_classified_schema():
    payload = {**VALID_NORMALIZED, "ratings": [1, 2, 3]}
    errors = _errors_for(payload)
    assert any(e.type is ErrorType.SCHEMA for e in errors)


# 15-18 validate_normalized_response ------------------------------------


def test_validate_normalized_response_success():
    model, errors = validate_normalized_response(VALID_NORMALIZED)
    assert model is not None
    assert errors == []


def test_validate_normalized_response_failure_returns_all_errors():
    payload = {k: v for k, v in VALID_NORMALIZED.items() if k != "participant_id"}
    model, errors = validate_normalized_response(payload)
    assert model is None
    assert len(errors) >= 1


def test_multiple_missing_fields_produce_multiple_errors():
    payload = {"ratings": {"q1": 1}}  # missing participant_id and stimulus_ref
    model, errors = validate_normalized_response(payload)
    assert model is None
    missing = [e for e in errors if e.type is ErrorType.MISSING]
    assert len(missing) >= 2


def test_rating_item_id_is_extracted():
    payload = {**VALID_NORMALIZED, "ratings": {"q1": 1.5}}
    errors = _errors_for(payload)
    assert any(e.item_id == "q1" for e in errors)


# 19-26 RunManifest ------------------------------------------------------


def test_manifest_accepts_model_config_input_key():
    manifest = _manifest()
    assert manifest.model.provider == "mock"


def test_manifest_dump_by_alias_uses_model_config():
    manifest = _manifest()
    dumped = manifest.model_dump(by_alias=True)
    assert "model_config" in dumped
    assert dumped["model_config"]["provider"] == "mock"


def test_manifest_task_and_benchmark_ids_can_be_none():
    manifest = _manifest()
    assert manifest.task_id is None
    assert manifest.benchmark_id is None


def test_manifest_task_and_benchmark_ids_can_be_strings():
    manifest = _manifest(task_id="task-1", benchmark_id="bench-1")
    assert manifest.task_id == "task-1"
    assert manifest.benchmark_id == "bench-1"


def test_manifest_rejects_finished_before_started():
    with pytest.raises(PydanticValidationError):
        _manifest(
            started_at="2026-07-13T10:00:00",
            finished_at="2026-07-13T09:00:00",
        )


def test_manifest_token_and_cost_can_be_none():
    manifest = _manifest()
    assert manifest.token_usage_total is None
    assert manifest.estimated_cost_usd is None


@pytest.mark.parametrize(
    "overrides",
    [{"token_usage_total": -1}, {"estimated_cost_usd": -0.5}],
)
def test_manifest_rejects_negative_token_or_cost(overrides):
    with pytest.raises(PydanticValidationError):
        _manifest(**overrides)


def test_manifest_preserves_extra_field():
    manifest = _manifest(experimental_flag="reserved")
    assert manifest.model_dump()["experimental_flag"] == "reserved"


# 27 no DeepSeek-proprietary fields --------------------------------------


def test_schemas_have_no_deepseek_proprietary_fields():
    forbidden = ("deepseek_api_key", "deepseek_base_url", "deepseek_request_id")
    model_json = ModelConfig.model_validate(VALID_MODEL_CONFIG).model_dump_json()
    manifest_json = _manifest().model_dump_json(by_alias=True)
    schema_text = str(ModelConfig.model_json_schema()) + str(RunManifest.model_json_schema())
    for token in forbidden:
        assert token not in model_json
        assert token not in manifest_json
        assert token not in schema_text
