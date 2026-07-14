"""Read-only loading of benchmark / task / metric YAML contracts (FAST-001).

This module loads the declarative YAML contracts under ``configs/`` into the
benchmark object model. It performs no network I/O and reads no API keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ..paths import PROJECT_ROOT
from .models import BenchmarkSpec, TaskSpec

CONFIGS_DIR = PROJECT_ROOT / "configs"
BENCHMARK_YAML = CONFIGS_DIR / "benchmarks" / "llm_attribution_behavior.v1.yaml"
TASK_V1_YAML = CONFIGS_DIR / "tasks" / "freewill_attribution.v1.yaml"
TASK_V2_YAML = CONFIGS_DIR / "tasks" / "freewill_attribution.v2.yaml"
METRICS_YAML = CONFIGS_DIR / "metrics" / "attribution_metrics.v1.yaml"


class RegistryError(RuntimeError):
    """Raised when a contract YAML cannot be loaded or is inconsistent."""


def _load_mapping(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_file():
        raise RegistryError(f"Contract file not found: {resolved}")
    data = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise RegistryError(f"Contract top-level must be a mapping: {resolved}")
    return data


def load_benchmark_spec(path: str | Path = BENCHMARK_YAML) -> BenchmarkSpec:
    data = _load_mapping(path)
    return BenchmarkSpec.model_validate(data)


def load_task_spec(path: str | Path) -> TaskSpec:
    data = _load_mapping(path)
    return TaskSpec.model_validate(data)


def load_v2_task_spec() -> TaskSpec:
    return load_task_spec(TASK_V2_YAML)


def load_metric_registry(path: str | Path = METRICS_YAML) -> list[dict[str, Any]]:
    data = _load_mapping(path)
    metrics = data.get("metrics", [])
    if not isinstance(metrics, list):
        raise RegistryError("metrics must be a list")
    return metrics


def metric_ids(path: str | Path = METRICS_YAML) -> list[str]:
    return [str(m["metric_id"]) for m in load_metric_registry(path) if "metric_id" in m]


__all__ = [
    "CONFIGS_DIR",
    "BENCHMARK_YAML",
    "TASK_V1_YAML",
    "TASK_V2_YAML",
    "METRICS_YAML",
    "RegistryError",
    "load_benchmark_spec",
    "load_task_spec",
    "load_v2_task_spec",
    "load_metric_registry",
    "metric_ids",
]
