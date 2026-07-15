"""Integration tests for the explicit, safe output-path pipeline (FND-004).

These tests drive the legacy scripts as subprocesses using tmp_path only. They
verify that:
- generation fails fast without --out and never writes the repository outputs/;
- generation refuses the historical outputs/ directory;
- mock generation writes exactly to the explicit directory (no API calls);
- --fresh only removes the known run files and preserves other files;
- material validation and analysis honor explicit --input/--out;
- importing the modules has no filesystem side effects;
- report scripts expose --help and fail fast without --input/--out.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
REPO_OUTPUTS = REPO_ROOT / "outputs"

RUN_SCRIPT = SRC / "run_simulated_study.py"
ANALYZE_SCRIPT = SRC / "analyze_results.py"
VALIDATE_SCRIPT = SRC / "validate_materials.py"
REPORT_SCRIPTS = [
    SRC / "generate_pilot_report.py",
    SRC / "generate_n20_construct_validation_report.py",
    SRC / "generate_n30_stability_replication_report.py",
]

SEED = 20260425


def _env():
    import os

    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    return env


def run_script(args, cwd=None):
    return subprocess.run(
        [sys.executable, *[str(a) for a in args]],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=_env(),
    )


def _snapshot(directory: Path):
    if not directory.exists():
        return set()
    return {p.relative_to(directory).as_posix() for p in directory.rglob("*")}


def _count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def test_generation_without_out_fails_fast():
    before = _snapshot(REPO_OUTPUTS)
    result = run_script([RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED])
    assert result.returncode != 0
    after = _snapshot(REPO_OUTPUTS)
    assert before == after


def test_generation_rejects_historical_outputs():
    before = _snapshot(REPO_OUTPUTS)
    result = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", REPO_OUTPUTS]
    )
    assert result.returncode != 0
    after = _snapshot(REPO_OUTPUTS)
    assert before == after


def test_mock_generation_writes_to_explicit_dir(tmp_path):
    run_dir = tmp_path / "run"
    result = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert result.returncode == 0, result.stderr

    raw_path = run_dir / "raw_simulated_responses.jsonl"
    wide_path = run_dir / "simulated_responses_wide.csv"
    assert raw_path.exists()
    assert wide_path.exists()
    assert _count_jsonl(raw_path) == 12

    # No API mode: every record is a synthetic mock response.
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            assert rec["synthetic"] is True
            assert rec["short_reason"] == "mock synthetic response"


def test_fresh_only_removes_known_run_files(tmp_path):
    run_dir = tmp_path / "run"
    first = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert first.returncode == 0, first.stderr

    sentinel = run_dir / "sentinel.txt"
    sentinel.write_text("keep me", encoding="utf-8")

    second = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED, "--fresh", "--out", run_dir]
    )
    assert second.returncode == 0, second.stderr

    assert (run_dir / "raw_simulated_responses.jsonl").exists()
    assert (run_dir / "simulated_responses_wide.csv").exists()
    assert sentinel.exists()
    assert sentinel.read_text(encoding="utf-8") == "keep me"


def test_material_validation_writes_preview(tmp_path):
    run_dir = tmp_path / "run"
    result = run_script([VALIDATE_SCRIPT, "--out", run_dir])
    assert result.returncode == 0, result.stderr
    assert (run_dir / "materials_preview.csv").exists()


def test_analysis_pipeline_writes_outputs(tmp_path):
    run_dir = tmp_path / "run"
    analysis_dir = tmp_path / "analysis"
    gen = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "2", "--seed", SEED, "--out", run_dir]
    )
    assert gen.returncode == 0, gen.stderr

    result = run_script([ANALYZE_SCRIPT, "--input", run_dir, "--out", analysis_dir])
    assert result.returncode == 0, result.stderr

    for name in [
        "scale_scores.csv",
        "reliability_summary.csv",
        "anova_summary.csv",
        "mediation_summary.json",
        "method_revision_report.md",
        "measurement_and_construct_revision_report.md",
    ]:
        assert (analysis_dir / name).exists(), name
    plots_dir = analysis_dir / "plots"
    assert plots_dir.is_dir()
    assert list(plots_dir.glob("*.png"))


def test_analysis_missing_out_fails_fast(tmp_path):
    run_dir = tmp_path / "run"
    gen = run_script(
        [RUN_SCRIPT, "--mock", "--n-per-cell", "1", "--seed", SEED, "--out", run_dir]
    )
    assert gen.returncode == 0, gen.stderr

    result = run_script([ANALYZE_SCRIPT, "--input", run_dir])
    assert result.returncode != 0


def test_import_has_no_filesystem_side_effects(tmp_path):
    before = _snapshot(REPO_OUTPUTS)
    code = (
        "import sys;"
        f"sys.path.insert(0, r'{SRC}');"
        "import run_simulated_study, analyze_results, validate_materials,"
        " generate_pilot_report, generate_n20_construct_validation_report,"
        " generate_n30_stability_replication_report, path_safety"
    )
    work = tmp_path / "cwd"
    work.mkdir()
    result = run_script(["-c", code], cwd=work)
    assert result.returncode == 0, result.stderr
    # Importing must not create files in the working directory.
    assert _snapshot(work) == set()
    # Importing must not touch the protected historical outputs.
    assert _snapshot(REPO_OUTPUTS) == before


@pytest.mark.parametrize("script", REPORT_SCRIPTS)
def test_report_scripts_help_succeeds(script):
    result = run_script([script, "--help"])
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--out" in result.stdout


@pytest.mark.parametrize("script", REPORT_SCRIPTS)
def test_report_scripts_fail_fast_without_args(script):
    before = _snapshot(REPO_OUTPUTS)
    result = run_script([script])
    assert result.returncode != 0
    assert _snapshot(REPO_OUTPUTS) == before
