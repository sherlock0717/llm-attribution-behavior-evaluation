"""Unit tests for benchmark object models (FAST-001)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from freewill_attribution.benchmark import models


def _artifact():
    return models.ArtifactRef(
        path="artifacts/runs/x/manifest.json",
        sha256="0" * 64,
        size_bytes=10,
        media_type="application/json",
        role="manifest",
    )


def test_all_core_objects_have_schema_version():
    ms = models.ModelSpec(provider="mock", model_id="rule-based-v2")
    assert ms.schema_version == models.SCHEMA_VERSION


def test_no_object_defines_api_key_field():
    # None of the versioned objects may carry a credential field.
    for cls in (
        models.BenchmarkSpec,
        models.TaskSpec,
        models.ModelSpec,
        models.RunSpec,
        models.RunManifest,
        models.ResponseRecord,
        models.ScoreRecord,
        models.AggregateReport,
    ):
        fields = set(cls.model_fields)
        assert "api_key" not in fields
        assert "authorization" not in fields
        assert "access_token" not in fields


def test_model_spec_round_trips_json():
    ms = models.ModelSpec(provider="mock", model_id="rule-based-v2", sampling_parameters={"temperature": 0.0})
    dumped = ms.model_dump(mode="json")
    text = json.dumps(dumped)
    restored = models.ModelSpec.model_validate(json.loads(text))
    assert restored.provider == "mock"
    assert restored.model_id == "rule-based-v2"


def test_extra_fields_are_preserved():
    ms = models.ModelSpec.model_validate(
        {"provider": "mock", "model_id": "rule-based-v2", "future_field": 123}
    )
    assert ms.model_dump()["future_field"] == 123


def test_run_manifest_requires_detailed_hashes():
    with pytest.raises(ValidationError):
        models.RunManifest(
            run_id="r1",
            status=models.RunStatus.COMPLETED,
            started_at="2026-07-14T00:00:00Z",
            benchmark_version="0.1-draft",
            task_version="2.0-mock",
            provider="mock",
            model_id="rule-based-v2",
            planned_records=12,
            completed_records=12,
            failed_records=0,
            # intentionally missing the *_hash fields
        )


def test_artifact_ref_negative_size_rejected():
    with pytest.raises(ValidationError):
        models.ArtifactRef(
            path="p", sha256="0" * 64, size_bytes=-1, media_type="application/json", role="x"
        )
