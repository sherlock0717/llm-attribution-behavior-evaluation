"""Offline dry-run planner tests (REAL-SETUP-001).

The dry-run plans a future real run WITHOUT any network or API-key access and
WITHOUT generating responses/scores/cost. Sockets are disabled and the
environment is stripped of the key to prove neither is touched.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from freewill_attribution import runner
from freewill_attribution.benchmark import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_OUTPUTS = REPO_ROOT / "outputs"


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    def _blocked(*args, **kwargs):  # pragma: no cover - only on violation
        raise AssertionError("network access attempted in a dry-run test")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    # Prove the key is never read: set a sentinel and assert it is never used.
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-should-never-be-read")


def _outputs_snapshot():
    import hashlib

    manifest = {}
    if not REPO_OUTPUTS.exists():
        return manifest
    for p in REPO_OUTPUTS.rglob("*"):
        if p.is_file():
            manifest[p.relative_to(REPO_OUTPUTS).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return manifest


def test_dry_run_smoke_plans_12_records(tmp_path):
    result = runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="smoke", seed=20260425, artifact_root=tmp_path,
    )
    assert result.planned_records == 12
    requests = [json.loads(line) for line in (result.plan_dir / "request_plan.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(requests) == 12


def test_dry_run_pilot_plans_60_records(tmp_path):
    result = runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="pilot", seed=20260425, artifact_root=tmp_path,
    )
    assert result.planned_records == 60


def test_dry_run_generates_no_response_or_score_files(tmp_path):
    result = runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="smoke", seed=20260425, artifact_root=tmp_path,
    )
    for banned in ("raw_responses.jsonl", "normalized_responses.jsonl",
                   "scores.jsonl", "aggregate_report.json"):
        assert not (result.plan_dir / banned).exists(), banned
    # planning artifacts DO exist
    for expected in ("plan.json", "resolved_config.json", "task_spec.json",
                     "model_config_snapshot.json", "prompt_template.txt",
                     "stimuli_plan.jsonl", "request_plan.jsonl", "readiness_report.json"):
        assert (result.plan_dir / expected).is_file(), expected


def test_dry_run_readiness_reports_not_run_and_no_key(tmp_path):
    result = runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="smoke", seed=20260425, artifact_root=tmp_path,
    )
    r = result.readiness
    assert r["provider_adapter_status"] == "offline_validated"
    assert r["live_api_status"] == "not_run"
    assert r["real_smoke_status"] == "not_run"
    assert r["real_pilot_status"] == "not_run"
    assert r["pricing_status"] == "requires_runtime_verification"
    assert r["network_calls_made"] == 0
    assert r["api_key_read"] is False
    assert r["cost_estimate"]["cost_estimate_status"] == "unavailable_until_pricing_verified"
    assert r["live_run_blockers"], "example config must have live-run blockers"


def test_dry_run_snapshot_contains_no_key(tmp_path):
    result = runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="smoke", seed=20260425, artifact_root=tmp_path,
    )
    for name in ("model_config_snapshot.json", "resolved_config.json",
                 "plan.json", "readiness_report.json"):
        blob = (result.plan_dir / name).read_text(encoding="utf-8")
        assert "sk-should-never-be-read" not in blob
        assert "sk-" not in blob


def test_dry_run_leaves_outputs_unchanged(tmp_path):
    before = _outputs_snapshot()
    runner.plan_dry_run(
        model_config=registry.MODEL_DEEPSEEK_EXAMPLE_YAML,
        run_profile="pilot", seed=20260425, artifact_root=tmp_path,
    )
    assert _outputs_snapshot() == before
