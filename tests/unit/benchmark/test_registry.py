"""Unit tests for the contract registry loader (FAST-001)."""

from __future__ import annotations

from freewill_attribution.benchmark import registry


def test_benchmark_spec_loads_and_maturity_is_split():
    bench = registry.load_benchmark_spec()
    assert bench.benchmark_id == "llm-attribution-behavior"
    assert bench.current_maturity_level == "pre-BMK-L1"
    assert bench.target_maturity_level == "BMK-L1"
    assert bench.current_maturity_level != bench.target_maturity_level


def test_v2_task_spec_loads_mock_executable():
    task = registry.load_v2_task_spec()
    assert task.task_id == "freewill-attribution-v2"
    # FAST-001: v2 is executable via the mock provider only.
    assert task.executable is True
    assert task.model_dump()["supported_providers"] == ["mock"]


def test_metric_ids_unique_and_nonempty():
    ids = registry.metric_ids()
    assert len(ids) == len(set(ids))
    assert len(ids) >= 39
