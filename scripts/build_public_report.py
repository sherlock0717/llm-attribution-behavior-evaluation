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

from freewill_attribution import runner  # noqa: E402
from freewill_attribution.benchmark import registry  # noqa: E402

MOCK_ACCEPTANCE_N = 2
MOCK_SEED = 20260425

# Provenance dimensions with a FOUR-state verification status (FAST-001.1 §6).
# We must NOT collapse "author attested" or "reconstructed from code" into
# "repository verified". The four states are:
#   repository_verified : directly checkable from repository content
#   author_attested     : stated by the author; not independently verifiable here
#   reconstructed        : rebuilt from current code, not a historical artifact
#   unknown              : no evidence; must never be back-filled as fact
VERIFICATION_STATES = (
    "repository_verified",
    "author_attested",
    "reconstructed",
    "unknown",
)
# Each dimension: (name, verification_status, chinese_label, chinese_group).
# The Chinese label/group are display metadata so the public matrix renders in
# Chinese without hardcoding text in HTML. Statuses are never softened.
G_DESIGN = "历史数据与设计"
G_RUN = "历史运行元数据"
G_REAL = "真实接入与运行"
PROVENANCE_DIMENSIONS = [
    ("record_count", "repository_verified", "历史记录数", G_DESIGN),
    ("condition_design_6x2x30", "repository_verified", "实验设计（6×2×30）", G_DESIGN),
    ("scale_item_definitions", "repository_verified", "量表题项定义", G_DESIGN),
    ("current_stimulus_definition", "reconstructed", "当前刺激定义", G_DESIGN),
    ("historical_provider_is_deepseek", "author_attested", "历史 Provider 为 DeepSeek", G_RUN),
    ("exact_model_server_snapshot", "unknown", "历史精确模型快照", G_RUN),
    ("exact_prompt_snapshot", "unknown", "历史精确 Prompt", G_RUN),
    ("historical_stimulus_hash", "unknown", "历史刺激哈希", G_RUN),
    ("request_timestamp", "unknown", "历史请求时间戳", G_RUN),
    ("provider_request_id", "unknown", "历史请求 ID", G_RUN),
    ("token_usage", "unknown", "历史 token 用量", G_RUN),
    ("estimated_cost_usd", "unknown", "历史费用估计", G_RUN),
    ("retry_information", "unknown", "历史 retry 信息", G_RUN),
    ("item_level_missingness", "unknown", "逐题缺失情况", G_RUN),
    ("raw_response_public_availability", "unknown", "原始响应公开可得性", G_RUN),
    # REAL-SETUP-001: real-provider readiness dimensions. Only the adapter code
    # is repository-verifiable; nothing about a real run exists yet.
    ("provider_adapter_code", "repository_verified", "离线 Provider 代码", G_REAL),
    ("provider_live_connectivity", "unknown", "真实连接", G_REAL),
    ("actual_model_id", "unknown", "真实模型 ID", G_REAL),
    ("actual_model_snapshot", "unknown", "真实模型快照", G_REAL),
    ("actual_pricing", "unknown", "真实价格", G_REAL),
    ("actual_request_ids", "unknown", "真实请求 ID", G_REAL),
    ("actual_token_usage", "unknown", "真实 token 用量", G_REAL),
    ("actual_cost", "unknown", "真实费用", G_REAL),
    ("actual_smoke_run", "unknown", "真实 smoke 运行", G_REAL),
    ("actual_pilot_run", "unknown", "真实 pilot 运行", G_REAL),
]

# Real-provider readiness status block. Unrun real metrics MUST be null /
# not_run / not_applicable — never 0, 0.0 or false.
REAL_PROVIDER_READINESS = {
    "adapter_status": "offline_validated",
    "credential_status": "not_configured",
    "live_api_status": "not_run",
    "smoke_status": "not_run",
    "pilot_status": "not_run",
    "model_id_status": "requires_runtime_verification",
    "pricing_status": "requires_runtime_verification",
    "actual_token_usage": None,
    "actual_cost_usd": None,
    "actual_latency_ms": None,
    "actual_completion_rate": None,
    "actual_parse_success_rate": None,
    "result_analysis_status": "not_applicable",
    "dry_run_planning": "available",
    "network_calls_made": 0,
    "real_smoke": "not_run",
    "real_pilot": "not_run",
}


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
        "real_provider_readiness": dict(REAL_PROVIDER_READINESS),
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
            "provider_model": "verify_on_run_day",
            "boundary": "尚未运行；无任何真实模型结果；需单独授权。",
        },
        "real_provider_readiness": dict(REAL_PROVIDER_READINESS),
    }


def build_evidence_matrix() -> dict:
    historical = bsd.build_historical_results()
    # Only claim id + evidence level (numbers stay in historical_results.json).
    historical_evidence = [
        {"id": c["id"], "title": c["title"], "evidence_level": c["evidence_level"]}
        for c in historical["claims"]
    ]
    provenance = [
        {"dimension": name, "verification_status": status,
         "label": label, "group": group}
        for name, status, label, group in PROVENANCE_DIMENSIONS
    ]
    counts = {
        state: sum(1 for _n, st, _l, _g in PROVENANCE_DIMENSIONS if st == state)
        for state in VERIFICATION_STATES
    }
    benchmark_objects = [
        "BenchmarkSpec", "TaskSpec", "ModelSpec", "RunSpec", "RunManifest",
        "ResponseRecord", "ScoreRecord", "AggregateReport", "ArtifactRef", "FailureRecord",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "historical_evidence_levels": historical_evidence,
        "provenance_completeness": {
            "dimensions": provenance,
            "repository_verified_count": counts["repository_verified"],
            "author_attested_count": counts["author_attested"],
            "reconstructed_count": counts["reconstructed"],
            "unknown_count": counts["unknown"],
            "total_count": len(PROVENANCE_DIMENSIONS),
            "status_legend": {
                "repository_verified": "可由仓库内容直接验证",
                "author_attested": "作者说明，仓库无法独立验证",
                "reconstructed": "由当前代码重建，非历史运行产物",
                "unknown": "无证据；不得补写为确定事实（source map §11）",
            },
            "note": "四种状态互不等价；author_attested / reconstructed 不得显示为已验证。",
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
