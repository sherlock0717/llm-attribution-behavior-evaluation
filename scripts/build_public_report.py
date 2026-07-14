#!/usr/bin/env python
"""Build standardized public-report JSON for the showcase data layer (FAST-001).

This script is READ-ONLY with respect to research assets. It:
  - reads historical results only through the validated extractors in
    ``build_site_data`` (so it never re-estimates or hand-writes numbers);
  - runs the DETERMINISTIC mock benchmark vertical slice in a temporary
    directory to obtain reproducible engineering-quality metrics (no API calls,
    no writes to outputs/, artifacts written to a temp dir only);
  - reads provenance facts from the v1 task contract / source map;
  - never mixes historical DeepSeek results with mock engineering metrics.

Output JSON files (UTF-8, indent=2, stable key order):
    site/data/evaluation_summary.json
    site/data/evidence_matrix.json
    site/data/engineering_status.json

Every mock value is explicitly namespaced as ``mock_engineering_validation`` and
must never be read as a real-model result.

Usage:
    python scripts/build_public_report.py
    python scripts/build_public_report.py --out site/data
    python scripts/build_public_report.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _p in (str(ROOT / "scripts"), str(SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_site_data as bsd  # noqa: E402  (sibling script, validated extractors)
import yaml  # noqa: E402

from freewill_attribution import runner  # noqa: E402
from freewill_attribution.benchmark import registry  # noqa: E402

MOCK_ACCEPTANCE_N = 2
MOCK_SEED = 20260425

# Provenance dimensions and whether the repository can verify them (source map §11).
PROVENANCE_DIMENSIONS = [
    ("record_count", "direct_file_evidence"),
    ("condition_design_6x2x30", "reconstructed_from_outputs"),
    ("scale_item_definitions", "direct_file_evidence"),
    ("historical_provider_is_deepseek", "historical_documentation"),
    ("exact_model_server_snapshot", "unknown"),
    ("exact_prompt_snapshot", "unknown"),
    ("prompt_hash", "unknown"),
    ("stimulus_hash", "reconstructed_from_code"),
    ("request_timestamp", "unknown"),
    ("provider_request_id", "unknown"),
    ("token_usage", "unknown"),
    ("estimated_cost_usd", "unknown"),
    ("retry_information", "unknown"),
    ("item_level_missingness", "unknown"),
    ("raw_response_public_availability", "unknown"),
]


class ReportError(RuntimeError):
    """Raised when a required source is missing."""


def _mock_metrics() -> dict:
    """Run the deterministic mock acceptance slice and return stable metric values."""
    with tempfile.TemporaryDirectory(prefix="fast_public_report_") as tmp:
        result = runner.run_benchmark(
            seed=MOCK_SEED, n_per_cell=MOCK_ACCEPTANCE_N, artifact_root=tmp, fresh=True
        )
        report = result.aggregate_report
        manifest = result.manifest
        artifact_roles = sorted({a.role for a in manifest.artifacts})
        return {
            "run_profile": "mock_acceptance",
            "n_per_cell": MOCK_ACCEPTANCE_N,
            "seed": MOCK_SEED,
            "provider": manifest.provider,
            "model_id": manifest.model_id,
            "planned_records": manifest.planned_records,
            "completed_records": manifest.completed_records,
            "failed_records": manifest.failed_records,
            "status": manifest.status.value,
            "execution_quality": report.execution_quality,
            "output_quality": report.output_quality,
            "task_metrics_mock": report.task_metrics,
            "artifact_roles": artifact_roles,
            "hash_fields": [
                "resolved_config_hash", "task_spec_hash", "model_spec_hash",
                "prompt_template_hash", "prompt_snapshot_set_hash",
                "stimulus_set_hash", "scoring_spec_hash",
            ],
        }


def build_engineering_status() -> dict:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject.get("project", {}).get("version")
    bench = registry.load_benchmark_spec()
    v2 = registry.load_v2_task_spec()
    mock = _mock_metrics()
    return {
        "project_version": version,
        "reproducible_core": "implemented_mock",
        "benchmark_id": bench.benchmark_id,
        "current_maturity_level": bench.current_maturity_level,
        "target_maturity_level": bench.target_maturity_level,
        "release_status": bench.release_status,
        "v2_task_status": v2.status,
        "v2_executable_scope": "mock_provider_only",
        "real_model_pilot": "planned_not_run",
        "pages_deployed": False,
        "artifact_lifecycle": mock["artifact_roles"],
        "mock_execution_quality": mock["execution_quality"],
        "mock_output_quality": mock["output_quality"],
        "data_source": "mock_engineering_validation",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def build_evaluation_summary() -> dict:
    summary = bsd.build_site_summary()
    mock = _mock_metrics()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "historical_deepseek": {
            "data_source": "historical_deepseek",
            "provider": summary["historical_provider"],
            "record_count": summary["historical_record_count"],
            "process_condition_count": summary["process_condition_count"],
            "identity_condition_count": summary["identity_condition_count"],
            "n_per_cell": summary["n_per_cell"],
            "data_type": "real_api_output",
            "boundary": "单一模型历史 AI 模拟数据；非人类被试；缺完整运行 provenance。",
        },
        "mock_engineering_validation": {
            "data_source": "mock_engineering_validation",
            "provider": mock["provider"],
            "model_id": mock["model_id"],
            "planned_records": mock["planned_records"],
            "completed_records": mock["completed_records"],
            "failed_records": mock["failed_records"],
            "completion_rate": mock["execution_quality"]["completion_rate"],
            "final_parse_success_rate": mock["output_quality"]["final_parse_success_rate"],
            "final_schema_compliance_rate": mock["output_quality"]["final_schema_compliance_rate"],
            "missing_item_rate": mock["output_quality"]["missing_item_rate"],
            "repair_trigger_rate": mock["output_quality"]["repair_trigger_rate"],
            "boundary": "确定性 mock 工程验证；非真实模型结果；不可解释为研究发现。",
        },
        "planned_real_pilot": {
            "data_source": "planned_real_pilot",
            "status": "planned_not_run",
            "real_smoke_n_per_cell": 1,
            "real_pilot_n_per_cell": 5,
            "provider_model": "decided_in_RUN-003",
            "boundary": "尚未运行；无任何真实模型结果；需单独授权。",
        },
    }


def build_evidence_matrix() -> dict:
    historical = bsd.build_historical_results()
    # Only claim id + evidence level (numbers stay in historical_results.json).
    historical_evidence = [
        {"id": c["id"], "title": c["title"], "evidence_level": c["evidence_level"]}
        for c in historical["claims"]
    ]
    provenance = [
        {"dimension": name, "evidence_type": etype,
         "verifiable": etype != "unknown"}
        for name, etype in PROVENANCE_DIMENSIONS
    ]
    known = sum(1 for _n, e in PROVENANCE_DIMENSIONS if e != "unknown")
    benchmark_objects = [
        "BenchmarkSpec", "TaskSpec", "ModelSpec", "RunSpec", "RunManifest",
        "ResponseRecord", "ScoreRecord", "AggregateReport", "ArtifactRef", "FailureRecord",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "historical_evidence_levels": historical_evidence,
        "provenance_completeness": {
            "dimensions": provenance,
            "known_count": known,
            "total_count": len(PROVENANCE_DIMENSIONS),
            "note": "unknown 维度不得补写为确定事实（source map §11）。",
        },
        "benchmark_object_model": {
            "implemented_objects": benchmark_objects,
            "count": len(benchmark_objects),
            "data_source": "contract_and_mock_implementation",
        },
    }


def build_all() -> dict[str, dict]:
    return {
        "evaluation_summary.json": build_evaluation_summary(),
        "evidence_matrix.json": build_evidence_matrix(),
        "engineering_status.json": build_engineering_status(),
    }


def _dumps(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _comparable(obj: dict) -> dict:
    obj = dict(obj)
    obj.pop("generated_at", None)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build public-report JSON data.")
    parser.add_argument("--out", default="site/data")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        built = build_all()
    except (bsd.BuildError, ReportError) as exc:
        print(f"build_public_report: ERROR: {exc}", file=sys.stderr)
        return 2

    out_dir = (ROOT / args.out).resolve()

    if args.check:
        mismatched = []
        for name, obj in built.items():
            existing_path = out_dir / name
            if not existing_path.is_file():
                mismatched.append(f"{name} (missing)")
                continue
            try:
                existing = json.loads(existing_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                mismatched.append(f"{name} (invalid JSON)")
                continue
            if _comparable(existing) != _comparable(obj):
                mismatched.append(name)
        if mismatched:
            print("public report data is OUT OF DATE: " + ", ".join(mismatched), file=sys.stderr)
            return 1
        print("public report data is up to date")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in built.items():
        (out_dir / name).write_text(_dumps(obj), encoding="utf-8")
        print(f"wrote {args.out}/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
