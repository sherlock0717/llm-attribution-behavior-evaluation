"""Benchmark object model, hashing, artifacts and registry (FAST-001).

Importing this package has no filesystem side effects and reads no API keys.
"""

from __future__ import annotations

from .models import (
    AggregateReport,
    ArtifactRef,
    AttemptParseStatus,
    AttemptValidationStatus,
    BenchmarkSpec,
    FailureRecord,
    ModelSpec,
    ResponseRecord,
    RunManifest,
    RunSpec,
    RunStatus,
    ScoreRecord,
    TaskSpec,
)

__all__ = [
    "AggregateReport",
    "ArtifactRef",
    "AttemptParseStatus",
    "AttemptValidationStatus",
    "BenchmarkSpec",
    "FailureRecord",
    "ModelSpec",
    "ResponseRecord",
    "RunManifest",
    "RunSpec",
    "RunStatus",
    "ScoreRecord",
    "TaskSpec",
]
