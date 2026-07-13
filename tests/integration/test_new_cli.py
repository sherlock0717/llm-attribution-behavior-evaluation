"""Integration tests for the transitional package CLI (FND-005).

These tests drive ``python -m freewill_attribution.cli`` as a subprocess and
verify parity with the legacy entry point. They never set PYTHONPATH manually
(the package must be importable because it is installed), never call the real
API, and never write the repository outputs/.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_OUTPUTS = REPO_ROOT / "outputs"
LEGACY_SCRIPT = REPO_ROOT / "src" / "run_simulated_study.py"

SEED = 20260425
CLI_MODULE = ["-m", "freewill_attribution.cli"]


def _env():
    import os

    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    return env


def run_cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, *CLI_MODULE, *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=_env(),
    )


def run_legacy(args, cwd=REPO_ROOT):
    return subprocess.run(
        [sys.executable, str(LEGACY_SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_env(),
    )


def _count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _outputs_manifest():
    manifest = {}
    if not REPO_OUTPUTS.exists():
        return manifest
    for p in REPO_OUTPUTS.rglob("*"):
        if p.is_file():
            rel = p.relative_to(REPO_OUTPUTS).as_posix()
            data = p.read_bytes()
            manifest[rel] = (len(data), hashlib.sha256(data).hexdigest())
    return manifest


def test_help_runs_from_outside_repo(tmp_path):
    result = run_cli(["--help"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "run" in result.stdout


def test_mock_run_writes_expected_outputs(tmp_path):
    run_dir = tmp_path / "new-cli"
    result = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert result.returncode == 0, result.stderr

    raw_path = run_dir / "raw_simulated_responses.jsonl"
    wide_path = run_dir / "simulated_responses_wide.csv"
    assert raw_path.exists()
    assert wide_path.exists()
    assert _count_jsonl(raw_path) == 12

    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            assert rec["short_reason"] == "mock synthetic response"


def test_new_cli_matches_legacy_bytewise(tmp_path):
    new_dir = tmp_path / "new-cli"
    legacy_dir = tmp_path / "legacy-cli"

    new = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", new_dir]
    )
    assert new.returncode == 0, new.stderr

    legacy = run_legacy(
        ["--mock", "--n-per-cell", "1", "--seed", SEED, "--out", legacy_dir]
    )
    assert legacy.returncode == 0, legacy.stderr

    for name in ["raw_simulated_responses.jsonl", "simulated_responses_wide.csv"]:
        assert (new_dir / name).read_bytes() == (legacy_dir / name).read_bytes(), name


def test_new_cli_without_out_exits_nonzero(tmp_path):
    before = _outputs_manifest()
    result = run_cli(["run", "--mock", "--n-per-cell", "1", "--seed", SEED])
    assert result.returncode != 0
    assert _outputs_manifest() == before


def test_new_cli_rejects_repo_outputs(tmp_path):
    before = _outputs_manifest()
    result = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", REPO_OUTPUTS]
    )
    assert result.returncode != 0
    assert _outputs_manifest() == before


def test_fresh_flag_is_forwarded(tmp_path):
    run_dir = tmp_path / "new-cli"
    first = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert first.returncode == 0, first.stderr

    sentinel = run_dir / "sentinel.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    second = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--fresh", "--out", run_dir]
    )
    assert second.returncode == 0, second.stderr

    assert (run_dir / "raw_simulated_responses.jsonl").exists()
    assert (run_dir / "simulated_responses_wide.csv").exists()
    assert sentinel.exists()
    assert sentinel.read_text(encoding="utf-8") == "keep me"


def test_new_cli_without_mock_fails_before_execution(tmp_path):
    before = _outputs_manifest()
    run_dir = tmp_path / "must-not-run"
    result = run_cli(
        ["run", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert result.returncode != 0
    assert "--mock" in result.stderr
    assert not run_dir.exists()
    assert not (run_dir / "raw_simulated_responses.jsonl").exists()
    assert not (run_dir / "simulated_responses_wide.csv").exists()
    assert _outputs_manifest() == before


def test_repo_outputs_unchanged_by_new_cli(tmp_path):
    before = _outputs_manifest()
    run_dir = tmp_path / "new-cli"
    result = run_cli(
        ["run", "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert result.returncode == 0, result.stderr
    assert _outputs_manifest() == before
