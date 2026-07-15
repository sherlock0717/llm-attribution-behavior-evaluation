"""Benchmark object model (FAST-001).

Implements the versioned contract objects defined in
``docs/benchmark/BENCHMARK_SPEC.md``:

    BenchmarkSpec, TaskSpec, ModelSpec, RunSpec, RunManifest,
    ResponseRecord, ScoreRecord, AggregateReport, ArtifactRef, FailureRecord

Design rules:
- Built on the existing ``ExtensibleModel`` base (``extra="allow"``) so
  forward-looking fields are preserved rather than dropped.
- Every object carries an explicit ``schema_version``.
- **No object contains an API key** (there is no ``api_key`` field anywhere).
  ``ModelSpec`` is a generic, version-able provider description.
- ``RunManifest`` records what actually happened (counts, hashes, artifacts,
  failures), not a plan. Token usage / cost are nullable.
- This module performs no I/O.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from ..schemas import ExtensibleModel, NonEmptyStr

SCHEMA_VERSION = "0.1"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class AttemptParseStatus(str, Enum):
    OK = "ok"
    EMPTY = "empty"
    MALFORMED_JSON = "malformed_json"
    PARSE_FAILURE = "parse_failure"


class AttemptValidationStatus(str, Enum):
    OK = "ok"
    SCHEMA_FAILURE = "schema_failure"
    MISSING_ITEM = "missing_item"
    OUT_OF_RANGE = "out_of_range"
    DUPLICATE_ITEM = "duplicate_item"
    UNKNOWN_ITEM = "unknown_item"
    NOT_VALIDATED = "not_validated"


# ---------------------------------------------------------------------------
# Artifact + failure primitives
# ---------------------------------------------------------------------------


class ArtifactRef(ExtensibleModel):
    """Reference to a run artifact on disk (path + integrity metadata)."""

    path: NonEmptyStr
    sha256: NonEmptyStr
    size_bytes: int = Field(ge=0)
    media_type: NonEmptyStr
    record_count: int | None = Field(default=None, ge=0)
    role: NonEmptyStr


class FailureRecord(ExtensibleModel):
    """A structured failure, referencing a code from FAILURE_TAXONOMY.md."""

    failure_code: NonEmptyStr
    stage: NonEmptyStr
    failure_scope: NonEmptyStr
    terminal_scope: NonEmptyStr
    severity: NonEmptyStr = "error"
    record_id: str | None = None
    attempt: int | None = Field(default=None, ge=1)
    message: NonEmptyStr
    context: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Spec objects
# ---------------------------------------------------------------------------


class BenchmarkSpec(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    benchmark_id: NonEmptyStr
    benchmark_version: NonEmptyStr
    title: NonEmptyStr
    description: NonEmptyStr
    task_ids: list[NonEmptyStr]
    metric_ids: list[NonEmptyStr]
    current_maturity_level: NonEmptyStr
    target_maturity_level: NonEmptyStr
    release_status: NonEmptyStr
    license_status: str | None = None
    created_at: str | None = None
    source_commit: str | None = None


class TaskSpec(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    task_id: NonEmptyStr
    task_version: NonEmptyStr
    protocol_ref: NonEmptyStr
    constructs: list[NonEmptyStr]
    condition_schema: dict[str, Any]
    identity_schema: dict[str, Any]
    stimulus_set: dict[str, Any]
    prompt_config: dict[str, Any]
    response_schema: dict[str, Any]
    scoring_config: dict[str, Any]
    aggregation_config: dict[str, Any]
    evidence_boundary: NonEmptyStr
    status: NonEmptyStr
    executable: bool


class ModelSpec(ExtensibleModel):
    """Generic provider/model description. Contains NO API key."""

    schema_version: NonEmptyStr = SCHEMA_VERSION
    provider: NonEmptyStr
    model_id: NonEmptyStr
    model_version_snapshot: str | None = None
    sampling_parameters: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    endpoint_type: NonEmptyStr = "mock"


class RunSpec(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    benchmark_id: NonEmptyStr
    task_id: NonEmptyStr
    model_spec: ModelSpec
    seed: int
    n_per_cell: int = Field(ge=1)
    max_repair_attempts: int = Field(default=1, ge=0)
    budget: dict[str, Any] | None = None
    concurrency: int = Field(default=1, ge=1)
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    resume_policy: dict[str, Any] = Field(default_factory=dict)
    artifact_root: NonEmptyStr


# ---------------------------------------------------------------------------
# Response / score records
# ---------------------------------------------------------------------------


class ResponseRecord(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    record_id: NonEmptyStr
    run_id: NonEmptyStr
    task_id: NonEmptyStr
    condition: NonEmptyStr
    identity: NonEmptyStr
    stimulus_id: NonEmptyStr
    scenario_id: NonEmptyStr
    request_index: int = Field(ge=0)
    batch_id: str | None = None
    attempt: int = Field(ge=1)
    parent_attempt_id: str | None = None
    persona_ref: str | None = None
    prompt_ref: str | None = None
    request_ref: str | None = None
    raw_response_ref: str | None = None
    parsed_response: dict[str, Any] | None = None
    parse_status: AttemptParseStatus
    validation_status: AttemptValidationStatus
    latency_ms: float | None = Field(default=None, ge=0)
    usage: dict[str, Any] | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreRecord(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    record_id: NonEmptyStr
    metric_id: NonEmptyStr
    raw_value: float | None = None
    normalized_value: float | None = None
    validity: NonEmptyStr = "ok"
    evidence: dict[str, Any] = Field(default_factory=dict)
    scoring_version: NonEmptyStr = "0.1"


class AggregateReport(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    run_id: NonEmptyStr
    benchmark_id: NonEmptyStr
    task_id: NonEmptyStr
    data_source: NonEmptyStr = "mock_engineering_validation"
    execution_quality: dict[str, Any] = Field(default_factory=dict)
    output_quality: dict[str, Any] = Field(default_factory=dict)
    task_metrics: dict[str, Any] = Field(default_factory=dict)
    reliability_metrics: dict[str, Any] = Field(default_factory=dict)
    comparative_metrics: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    figure_refs: list[str] = Field(default_factory=list)
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# RunManifest (records what actually happened)
# ---------------------------------------------------------------------------


class RunManifest(ExtensibleModel):
    schema_version: NonEmptyStr = SCHEMA_VERSION
    run_id: NonEmptyStr
    status: RunStatus
    started_at: datetime
    finished_at: datetime | None = None
    git_commit: str | None = None
    benchmark_version: NonEmptyStr
    task_version: NonEmptyStr

    # Detailed content hashes (canonical serialization).
    resolved_config_hash: NonEmptyStr
    task_spec_hash: NonEmptyStr
    model_spec_hash: NonEmptyStr
    prompt_template_hash: NonEmptyStr
    prompt_snapshot_set_hash: NonEmptyStr
    stimulus_set_hash: NonEmptyStr
    scoring_spec_hash: NonEmptyStr

    provider: NonEmptyStr
    model_id: NonEmptyStr
    model_snapshot: str | None = None

    planned_records: int = Field(ge=0)
    completed_records: int = Field(ge=0)
    failed_records: int = Field(ge=0)
    retry_count: int = Field(default=0, ge=0)
    parse_failure_count: int = Field(default=0, ge=0)
    schema_failure_count: int = Field(default=0, ge=0)

    token_usage: dict[str, Any] | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0)

    artifacts: list[ArtifactRef] = Field(default_factory=list)
    errors: list[FailureRecord] = Field(default_factory=list)

    # FAST-001.1: manifest.json is the integrity index for the run. It records
    # every OTHER artifact's hash but is deliberately excluded from its own
    # ``artifacts`` list; its digest is written separately to ``manifest.sha256``
    # so there is no self-referential hash cycle.
    integrity_note: NonEmptyStr = (
        "manifest.json is the integrity index and is excluded from its own "
        "artifact list; its SHA-256 is written separately to manifest.sha256."
    )
    # Free-form provenance notes (e.g. when git_commit could not be determined).
    provenance_notes: list[str] = Field(default_factory=list)


__all__ = [
    "SCHEMA_VERSION",
    "RunStatus",
    "AttemptParseStatus",
    "AttemptValidationStatus",
    "ArtifactRef",
    "FailureRecord",
    "BenchmarkSpec",
    "TaskSpec",
    "ModelSpec",
    "RunSpec",
    "ResponseRecord",
    "ScoreRecord",
    "AggregateReport",
    "RunManifest",
]
