#!/usr/bin/env python
"""Build static showcase JSON data from repository source files (SITE-002).

This script is READ-ONLY with respect to research assets. It:
  - only reads repository source files;
  - never writes outputs/;
  - never calls the network or any API;
  - never runs research scripts and never re-estimates models;
  - only extracts, validates and organises already-produced results;
  - fails loudly when a required file, column, metric or cell is missing
    (it never guesses a missing value);
  - never uses AGENT_WORKLOG.md as a dynamic data source.

Usage:
    python scripts/build_site_data.py
    python scripts/build_site_data.py --out site/data
    python scripts/build_site_data.py --check

Output JSON files (UTF-8, indent=2, stable key order):
    site_summary.json
    roadmap.json
    version_history.json
    historical_results.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

STATUS_ENUM = {"completed", "current", "planned", "historical", "pending_verification"}

SELECTED_FIGURES = [
    ("mean-agency", "outputs/plots/mean_agency.png", "assets/figures/mean_agency.png",
     "Agency by process condition", "六个决策过程条件下 agency 均值的柱状图"),
    ("mean-free-will-attribution", "outputs/plots/mean_free_will_attribution.png",
     "assets/figures/mean_free_will_attribution.png",
     "Free-will attribution by process condition", "六个决策过程条件下自由意志归因均值的柱状图"),
    ("mean-subjective-process-completeness", "outputs/plots/mean_subjective_process_completeness.png",
     "assets/figures/mean_subjective_process_completeness.png",
     "Subjective process completeness by process condition",
     "六个决策过程条件下主观过程完整性均值的柱状图"),
]

FIGURE_BOUNDARY = "历史 DeepSeek API 模型输出；AI 模拟数据；非人类被试；单一模型。"

# The research data + design inputs that actually determine the site content.
# source_commit is the last commit that touched ANY of these, NOT the current
# HEAD. This keeps the committed site_summary.json stable when only site/ files
# change afterwards (so `--check` does not break on the next HEAD).
RESEARCH_SOURCE_PATHS = [
    "outputs/scale_scores.csv",
    "outputs/controlled_regression_summary.csv",
    "outputs/planned_contrasts.csv",
    "outputs/parallel_mediation_summary.json",
    "outputs/n30_stability_replication_report.md",
    "outputs/plots/mean_agency.png",
    "outputs/plots/mean_free_will_attribution.png",
    "outputs/plots/mean_subjective_process_completeness.png",
    "configs/study.default.yaml",
    "docs/audit/v1_provenance_statement.md",
]


class BuildError(RuntimeError):
    """Raised when a required source, column, metric or cell is missing."""


# ---------------------------------------------------------------------------
# Source readers
# ---------------------------------------------------------------------------


def _require(rel: str) -> Path:
    path = ROOT / rel
    if not path.is_file():
        raise BuildError(f"required source file missing: {rel}")
    return path


def _read_text(rel: str) -> str:
    return _require(rel).read_text(encoding="utf-8")


def _read_csv(rel: str) -> list[dict[str, str]]:
    with _require(rel).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(rel: str) -> str:
    digest = hashlib.sha256()
    with _require(rel).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(ROOT), capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        raise BuildError(f"git command failed: {' '.join(args)} ({exc})") from exc
    return result.stdout.strip()


def _latest_source_commit() -> str:
    """Last commit that changed any research data / design input.

    Not `git rev-parse HEAD`: using HEAD would make the committed
    site_summary.json go stale as soon as a site-only commit lands.
    """
    commit = _git(["log", "-1", "--format=%H", "--", *RESEARCH_SOURCE_PATHS])
    if not commit:
        raise BuildError("could not resolve latest research source commit")
    return commit


def _fmt_p(p: float) -> str:
    return "p < .001" if p < 0.001 else f"p = {p:.3f}"


def _find_md_table(text: str, required_headers: list[str]) -> tuple[list[str], list[list[str]]]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        headers = [c.strip() for c in stripped.strip("|").split("|")]
        if all(h in headers for h in required_headers):
            rows: list[list[str]] = []
            j = i + 2  # skip the markdown separator row
            while j < len(lines) and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            return headers, rows
    raise BuildError(
        "markdown table with headers "
        f"{required_headers} not found (source layout changed)"
    )


# ---------------------------------------------------------------------------
# site_summary.json
# ---------------------------------------------------------------------------


def build_site_summary() -> dict:
    pyproject = tomllib.loads(_read_text("pyproject.toml"))
    version = pyproject.get("project", {}).get("version")
    if not version:
        raise BuildError("pyproject.toml project.version missing")

    study = yaml.safe_load(_read_text("configs/study.default.yaml"))
    design = (study or {}).get("design", {})
    process_conditions = design.get("process_conditions")
    identity_labels = design.get("identity_labels")
    if not process_conditions or not identity_labels:
        raise BuildError("configs/study.default.yaml design conditions missing")

    scores = _read_csv("outputs/scale_scores.csv")
    if not scores:
        raise BuildError("outputs/scale_scores.csv has no data rows")
    if "identity_label" not in scores[0] or "process_condition" not in scores[0]:
        raise BuildError("scale_scores.csv missing identity_label/process_condition columns")

    cells: dict[tuple[str, str], int] = {}
    for row in scores:
        key = (row["identity_label"], row["process_condition"])
        cells[key] = cells.get(key, 0) + 1
    cell_sizes = set(cells.values())
    if len(cell_sizes) != 1:
        raise BuildError(f"cells are not balanced; per-cell counts = {sorted(cell_sizes)}")
    n_per_cell = cell_sizes.pop()

    provenance = _read_text("docs/audit/v1_provenance_statement.md")
    if "DeepSeek API" not in provenance:
        raise BuildError("provenance statement does not confirm DeepSeek API provider")

    commit = _latest_source_commit()
    commit_date = _git(["show", "-s", "--format=%cI", commit])[:10]
    if not commit or not commit_date:
        raise BuildError("could not resolve research source commit / commit date")

    design = _design_block(process_conditions, identity_labels, n_per_cell, len(scores))

    return {
        "project_version": version,
        "project_stage": "current",
        "local_engineering_status": "completed",
        "release_verification_status": "pending_verification",
        "source_commit": commit,
        "data_as_of_date": commit_date,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "historical_provider": "DeepSeek API",
        "historical_record_count": len(scores),
        "process_condition_count": len(process_conditions),
        "identity_condition_count": len(identity_labels),
        "n_per_cell": n_per_cell,
        "historical_data_type": "real_api_output",
        "mock_usage": "engineering_validation_only",
        "provenance_status": "incomplete_run_metadata",
        "benchmark_status": "planned",
        "token_usage_total": None,
        "estimated_cost_usd": None,
        "model_version_snapshot": None,
        "design": design,
    }


def _design_block(process_conditions: list[str], identity_labels: list[str],
                  n_per_cell: int, total_records: int) -> dict:
    """Structured 6x2 design metadata for the native design matrix.

    Condition keys come from configs/study.default.yaml (canonical order);
    the Chinese label/note come from the human-maintained manifest and are
    validated against the canonical keys. No number here is hand-written:
    n_per_cell and total_records are computed from outputs/scale_scores.csv.
    """
    ed = _manifest().get("experimental_design", {})
    pc_meta = {p.get("key"): p for p in ed.get("process_conditions", []) if isinstance(p, dict)}
    conditions = []
    for key in process_conditions:
        meta = pc_meta.get(key)
        if not meta or not meta.get("label_zh") or not meta.get("note_zh"):
            raise BuildError(
                f"site_manifest experimental_design missing label/note for '{key}'"
            )
        conditions.append({"key": key, "label": meta["label_zh"], "note": meta["note_zh"]})
    return {
        "process_conditions": conditions,
        "identity_labels": list(identity_labels),
        "n_per_cell": n_per_cell,
        "total_records": total_records,
    }


# ---------------------------------------------------------------------------
# roadmap.json / version_history.json (from manifest, validated)
# ---------------------------------------------------------------------------


def _manifest() -> dict:
    data = yaml.safe_load(_read_text("docs/showcase/site_manifest.yaml"))
    if not isinstance(data, dict):
        raise BuildError("site_manifest.yaml top-level must be a mapping")
    return data


def _validate_status(value: str, where: str) -> str:
    if value not in STATUS_ENUM:
        raise BuildError(f"invalid status '{value}' at {where}")
    return value


def build_roadmap() -> dict:
    manifest = _manifest()
    roadmap = manifest.get("roadmap")
    if not roadmap or "phases" not in roadmap or "track_s" not in roadmap:
        raise BuildError("site_manifest.yaml roadmap.phases/track_s missing")

    def _items(items: list[dict], group: str) -> list[dict]:
        out = []
        for it in items:
            for field in ("id", "name", "status", "summary_zh"):
                if not it.get(field):
                    raise BuildError(f"roadmap {group} item missing '{field}': {it.get('id')}")
            _validate_status(it["status"], f"roadmap {group} {it['id']}")
            if it["id"] in ("phase-6",) and it["status"] != "planned":
                raise BuildError("phase-6 (Benchmark Track) status must be 'planned'")
            entry = {
                "id": it["id"],
                "name": it["name"],
                "status": it["status"],
                "summary": it["summary_zh"],
                "depends_on": list(it.get("depends_on", [])),
                "evidence_ref": list(it.get("evidence_ref", [])),
            }
            if "local_status" in it:
                entry["local_status"] = _validate_status(it["local_status"], f"{it['id']}.local")
            if "release_status" in it:
                entry["release_status"] = _validate_status(
                    it["release_status"], f"{it['id']}.release"
                )
            out.append(entry)
        return out

    return {
        "phases": _items(roadmap["phases"], "phases"),
        "track_s": _items(roadmap["track_s"], "track_s"),
    }


def build_version_history() -> dict:
    manifest = _manifest()
    versions = manifest.get("version_history")
    if not versions:
        raise BuildError("site_manifest.yaml version_history missing")
    out = []
    for v in versions:
        for field in ("version", "title_zh", "highlights_zh"):
            if not v.get(field):
                raise BuildError(f"version_history item missing '{field}': {v.get('version')}")
        if "is_future" not in v:
            raise BuildError(f"version_history item missing 'is_future': {v.get('version')}")
        out.append({
            "version": v["version"],
            "title": v["title_zh"],
            "highlights": list(v["highlights_zh"]),
            "is_future": bool(v["is_future"]),
        })
    return {"versions": out}


# ---------------------------------------------------------------------------
# historical_results.json
# ---------------------------------------------------------------------------


def _controlled(dv: str) -> dict[str, float]:
    rows = _read_csv("outputs/controlled_regression_summary.csv")
    for row in rows:
        if row.get("dv") == dv and row.get("spec") == "control_both":
            return {"F": float(row["process_F"]), "p": float(row["process_p"])}
    raise BuildError(f"controlled_regression_summary.csv: dv={dv} spec=control_both not found")


def _agency_contrasts() -> list[dict]:
    rows = _read_csv("outputs/planned_contrasts.csv")
    wanted = {
        "reasons_concise_vs_direct_choice_long",
        "reflection_feedback_vs_direct_choice_long",
        "alternatives_vs_direct_choice",
    }
    out = []
    for row in rows:
        if row.get("dv") == "agency" and row.get("contrast") in wanted:
            out.append({
                "contrast": row["contrast"],
                "diff": float(row["diff_a_minus_b"]),
                "t": float(row["t"]),
                "p": float(row["p"]),
            })
    if len(out) != len(wanted):
        raise BuildError("planned_contrasts.csv: expected agency contrasts not all found")
    order = {c: i for i, c in enumerate(
        ["alternatives_vs_direct_choice",
         "reasons_concise_vs_direct_choice_long",
         "reflection_feedback_vs_direct_choice_long"])}
    out.sort(key=lambda r: order[r["contrast"]])
    return out


def _report_condition_map(required_col: str) -> dict[str, float]:
    text = _read_text("outputs/n30_stability_replication_report.md")
    headers, rows = _find_md_table(text, ["process_condition", required_col])
    idx_cond = headers.index("process_condition")
    idx_val = headers.index(required_col)
    result: dict[str, float] = {}
    for cells in rows:
        if len(cells) <= max(idx_cond, idx_val):
            continue
        cond = cells[idx_cond]
        try:
            result[cond] = float(cells[idx_val])
        except ValueError:
            continue
    if not result:
        raise BuildError(f"n30 report: no numeric values for column '{required_col}'")
    return result


def build_historical_results() -> dict:
    study = yaml.safe_load(_read_text("configs/study.default.yaml"))
    conditions = study["design"]["process_conditions"]

    # 1. factual manipulation check (extracted from report table)
    factual = _report_condition_map("factual_manipulation_check")
    for cond in conditions:
        if cond not in factual:
            raise BuildError(f"factual check value missing for condition '{cond}'")
    factual_metrics = [
        {
            "name": cond,
            "value": factual[cond],
            "display": f"{cond} = {factual[cond]:.2f}",
            "source_file": "outputs/n30_stability_replication_report.md",
            "source_field": f"factual check table / {cond}",
            "evidence_level": "descriptive",
        }
        for cond in conditions
    ]

    # 2. agency condition means (extracted from report means table)
    agency_means = _report_condition_map("agency")
    for cond in conditions:
        if cond not in agency_means:
            raise BuildError(f"agency mean missing for condition '{cond}'")
    agency_metrics = [
        {
            "name": cond,
            "value": agency_means[cond],
            "display": f"{cond} = {agency_means[cond]:.2f}",
            "source_file": "outputs/n30_stability_replication_report.md",
            "source_field": f"means table / agency / {cond}",
            "evidence_level": "descriptive",
        }
        for cond in conditions
    ]

    # 3. agency controlled regression
    agency_reg = _controlled("agency")
    agency_reg_metrics = [
        {"name": "process_F", "value": agency_reg["F"], "display": f"F = {agency_reg['F']:.2f}",
         "source_file": "outputs/controlled_regression_summary.csv",
         "source_field": "dv=agency, spec=control_both, process_F", "evidence_level": "derived"},
        {"name": "process_p", "value": agency_reg["p"], "display": _fmt_p(agency_reg["p"]),
         "source_file": "outputs/controlled_regression_summary.csv",
         "source_field": "dv=agency, spec=control_both, process_p", "evidence_level": "derived"},
    ]

    # 4. agency planned contrasts
    contrasts = _agency_contrasts()
    contrast_metrics = [
        {
            "name": c["contrast"],
            "value": c["diff"],
            "display": f"{c['contrast']}: Δ={c['diff']:.2f}, t={c['t']:.2f}, {_fmt_p(c['p'])}",
            "source_file": "outputs/planned_contrasts.csv",
            "source_field": f"dv=agency, contrast={c['contrast']}, diff_a_minus_b/t/p",
            "evidence_level": "planned_contrast",
        }
        for c in contrasts
    ]

    # 5. free_will_attribution controlled regression
    fw_reg = _controlled("free_will_attribution")
    fw_reg_metrics = [
        {"name": "process_F", "value": fw_reg["F"], "display": f"F = {fw_reg['F']:.2f}",
         "source_file": "outputs/controlled_regression_summary.csv",
         "source_field": "dv=free_will_attribution, spec=control_both, process_F",
         "evidence_level": "derived"},
        {"name": "process_p", "value": fw_reg["p"], "display": _fmt_p(fw_reg["p"]),
         "source_file": "outputs/controlled_regression_summary.csv",
         "source_field": "dv=free_will_attribution, spec=control_both, process_p",
         "evidence_level": "derived"},
    ]

    # 6. parallel mediation (exploratory path diagnostic)
    med = json.loads(_read_text("outputs/parallel_mediation_summary.json"))
    for key in ("indirect_agency", "agency_indirect_ci_2.5", "agency_indirect_ci_97.5",
                "indirect_intelligence", "intelligence_indirect_ci_2.5",
                "intelligence_indirect_ci_97.5"):
        if key not in med:
            raise BuildError(f"parallel_mediation_summary.json missing key '{key}'")
    def _med_metric(name, est, lo, hi, field, role):
        return {
            "name": name,
            "value": est,
            "estimate": est,
            "ci_low": lo,
            "ci_high": hi,
            "crosses_zero": bool(lo <= 0 <= hi),
            "path_role": role,
            "display": f"{name} = {est:.4f} [{lo:.4f}, {hi:.4f}]",
            "source_file": "outputs/parallel_mediation_summary.json",
            "source_field": field,
            "evidence_level": "exploratory_path_diagnostic",
        }

    med_metrics = [
        _med_metric("agency_indirect", med["indirect_agency"],
                    med["agency_indirect_ci_2.5"], med["agency_indirect_ci_97.5"],
                    "indirect_agency, agency_indirect_ci_2.5/97.5",
                    "primary_exploratory_path"),
        _med_metric("perceived_intelligence_indirect", med["indirect_intelligence"],
                    med["intelligence_indirect_ci_2.5"], med["intelligence_indirect_ci_97.5"],
                    "indirect_intelligence, intelligence_indirect_ci_2.5/97.5",
                    "secondary_exploratory_path"),
    ]

    claims = [
        {"id": "factual-check",
         "title": "操纵检验反映出低结构与高结构条件的整体差异",
         "summary": ("高结构条件的 factual manipulation check 整体高于低结构条件；"
                     "两个低结构诊断条件（direct_choice、direct_choice_long）不构成严格单调序列，"
                     "因此不宜说六类条件严格单调递增或两两显著不同。"),
         "metrics": factual_metrics,
         "source_refs": ["outputs/n30_stability_replication_report.md"],
         "figure_id": None,
         "evidence_level": "descriptive",
         "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。"},
        {"id": "agency-condition-means",
         "title": "行动者感（agency）按条件的均值",
         "summary": "agency 随结构总体上升，是最稳定的主结果。",
         "metrics": agency_metrics,
         "source_refs": ["outputs/n30_stability_replication_report.md", "outputs/scale_scores.csv"],
         "figure_id": "mean-agency",
         "evidence_level": "descriptive",
         "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。"},
        {"id": "agency-controlled-regression",
         "title": "控制感知智能与文本长度后，决策过程对 agency 仍显著",
         "summary": "同时控制 perceived_intelligence 与 char_len 后，process→agency 仍显著。",
         "metrics": agency_reg_metrics,
         "source_refs": ["outputs/controlled_regression_summary.csv"],
         "figure_id": "mean-agency",
         "evidence_level": "derived",
         "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。"},
        {"id": "agency-planned-contrasts",
         "title": "理由结构不是单纯的文本长度效应（agency 计划对比）",
         "summary": ("以下为 agency 的计划对比：理由权衡/反思反馈显著高于长文本直接选择；"
                     "仅列出候选方案不足以提高 agency。注意这些是 agency 而非 free_will_attribution 的对比。"),
         "metrics": contrast_metrics,
         "source_refs": ["outputs/planned_contrasts.csv"],
         "figure_id": "mean-agency",
         "evidence_level": "planned_contrast",
         "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。数值对应 agency。"},
        {"id": "freewill-controlled-regression",
         "title": "自由意志归因：直接 process 效应不稳定",
         "summary": "控制感知智能与文本长度后，process 对 free_will_attribution 的直接效应不稳定。",
         "metrics": fw_reg_metrics,
         "source_refs": ["outputs/controlled_regression_summary.csv"],
         "figure_id": "mean-free-will-attribution",
         "evidence_level": "derived",
         "boundary_note": "单一模型的历史 AI 模拟数据；非人类被试。"},
        {"id": "parallel-mediation",
         "title": "间接路径：process → agency → free_will_attribution",
         "summary": ("在该探索性分析中，agency 间接效应的区间未跨 0；"
                     "perceived_intelligence 间接效应区间跨 0。这是探索性路径诊断，不是机制证明，"
                     "不能据此断言因果中介。"),
         "metrics": med_metrics,
         "source_refs": ["outputs/parallel_mediation_summary.json"],
         "figure_id": None,
         "evidence_level": "exploratory_path_diagnostic",
         "boundary_note": "探索性路径诊断，非机制证明；单一模型的历史 AI 模拟数据。"},
        {"id": "responsibility-exploratory",
         "title": "责任归因（仅探索性）",
         "summary": "责任相关维度方向不如 agency 稳定，仅作为探索性结果呈现。",
         "metrics": [],
         "source_refs": ["outputs/n30_stability_replication_report.md",
                         "outputs/controlled_regression_summary.csv"],
         "figure_id": None,
         "evidence_level": "exploratory_path_diagnostic",
         "boundary_note": "探索性结果；单一模型的历史 AI 模拟数据；非人类被试。"},
    ]

    read_notes = _figure_read_notes()
    figures = []
    for fig_id, source_file, site_file, title, alt in SELECTED_FIGURES:
        note = read_notes.get(fig_id)
        if not note:
            raise BuildError(f"site_manifest figures_selected missing read_note_zh for '{fig_id}'")
        figures.append({
            "id": fig_id,
            "file": site_file,
            "source_file": source_file,
            "title": title,
            "alt": alt,
            "read_note": note,
            "evidence_level": "descriptive",
            "boundary_note": FIGURE_BOUNDARY,
            "sha256": _sha256(source_file),
        })

    return {"claims": claims, "figures": figures}


def _figure_read_notes() -> dict[str, str]:
    items = (_manifest().get("figures_selected", {}) or {}).get("items", [])
    notes: dict[str, str] = {}
    for it in items:
        if isinstance(it, dict) and it.get("id") and it.get("read_note_zh"):
            notes[it["id"]] = it["read_note_zh"]
    return notes


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def build_all() -> dict[str, dict]:
    return {
        "site_summary.json": build_site_summary(),
        "roadmap.json": build_roadmap(),
        "version_history.json": build_version_history(),
        "historical_results.json": build_historical_results(),
    }


def _dumps(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _comparable(name: str, obj: dict) -> dict:
    # generated_at is build metadata only, excluded from data-content equality.
    if name == "site_summary.json":
        obj = dict(obj)
        obj.pop("generated_at", None)
    return obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build static showcase JSON data.")
    parser.add_argument("--out", default="site/data", help="Output directory (default: site/data)")
    parser.add_argument("--check", action="store_true",
                        help="Rebuild in memory and compare to existing JSON; exit 1 if different.")
    args = parser.parse_args(argv)

    try:
        built = build_all()
    except BuildError as exc:
        print(f"build_site_data: ERROR: {exc}", file=sys.stderr)
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
            if _comparable(name, existing) != _comparable(name, obj):
                mismatched.append(name)
        if mismatched:
            print("site data is OUT OF DATE: " + ", ".join(mismatched), file=sys.stderr)
            return 1
        print("site data is up to date")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in built.items():
        (out_dir / name).write_text(_dumps(obj), encoding="utf-8")
        print(f"wrote {args.out}/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
