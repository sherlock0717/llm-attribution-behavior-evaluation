"""Real-provider readiness gate tests via the CLI (REAL-SETUP-001).

Confirms the CLI refuses a live deepseek run this round, plans offline dry-runs,
and never reads the API key or touches the network.
"""

from __future__ import annotations

import json
import socket

import pytest

from freewill_attribution import cli


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    def _blocked(*args, **kwargs):  # pragma: no cover - only on violation
        raise AssertionError("network access attempted in a readiness test")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-should-never-be-read")


def test_cli_refuses_live_deepseek_run(tmp_path, capsys):
    rc = cli.main([
        "benchmark-run", "--provider", "deepseek",
        "--real-api", "--confirm-paid-run",
        "--artifact-root", str(tmp_path),
    ])
    assert rc == 2
    out = capsys.readouterr().out
    assert "refused" in out
    assert "sk-should-never-be-read" not in out


def test_cli_dry_run_deepseek_smoke(tmp_path, capsys):
    rc = cli.main([
        "benchmark-run", "--provider", "deepseek", "--dry-run",
        "--run-profile", "smoke", "--artifact-root", str(tmp_path),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "planned_records=12" in out
    assert "network_calls_made=0" in out
    plan_dir = tmp_path / "plans" / "dryrun-deepseek-smoke-seed20260425"
    readiness = json.loads((plan_dir / "readiness_report.json").read_text(encoding="utf-8"))
    assert readiness["live_api_status"] == "not_run"
    assert readiness["api_key_read"] is False


def test_cli_dry_run_deepseek_pilot(tmp_path, capsys):
    rc = cli.main([
        "benchmark-run", "--provider", "deepseek", "--dry-run",
        "--run-profile", "pilot", "--artifact-root", str(tmp_path),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "planned_records=60" in out


def test_mock_still_default_and_runs(tmp_path, capsys):
    rc = cli.main([
        "benchmark-run", "--mock", "--artifact-root", str(tmp_path),
        "--n-per-cell", "1", "--fresh",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "status=completed" in out
