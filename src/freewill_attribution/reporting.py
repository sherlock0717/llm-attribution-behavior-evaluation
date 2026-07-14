"""Metric computation and Aggregate Report builder (FAST-001).

Computes the execution-integrity and output-quality metrics implemented this
round from the run's response records, plus task metrics from the scored
records. Metrics whose formulas are not yet frozen remain ``planned_without_formula``
and are NOT fabricated here.

Every value produced here is a MOCK engineering-validation measurement of the
pipeline, never a real-model research result.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

from .benchmark.models import (
    AggregateReport,
    ArtifactRef,
    AttemptParseStatus,
    AttemptValidationStatus,
    ResponseRecord,
)
from .tasks.freewill_attribution import spec

# Metrics implemented this round (others in the registry stay planned).
IMPLEMENTED_METRICS = [
    "planned_record_count",
    "completed_record_count",
    "failed_record_count",
    "completion_rate",
    "first_attempt_parse_success_rate",
    "final_parse_success_rate",
    "first_attempt_schema_compliance_rate",
    "final_schema_compliance_rate",
    "missing_item_rate",
    "range_validity_rate",
    "repair_trigger_rate",
    "repair_success_rate",
    "response_length_chars",
    "agency",
    "free_will_attribution",
    "subjective_process_completeness",
    "condition_sensitivity",
    "identity_effect",
]

PLANNED_WITHOUT_FORMULA = [
    "repeat_run_stability",
    "model_version_sensitivity",
    "provenance_completeness",
]


def _group_by_record(records: list[ResponseRecord]) -> dict[str, list[ResponseRecord]]:
    grouped: dict[str, list[ResponseRecord]] = {}
    for rec in records:
        grouped.setdefault(rec.record_id, []).append(rec)
    for rid in grouped:
        grouped[rid].sort(key=lambda r: r.attempt)
    return grouped


def compute_metrics(
    *,
    planned: int,
    records: list[ResponseRecord],
    scored_records: list[dict[str, Any]],
    aggregate_scores: dict[str, Any],
    raw_text_lengths: dict[str, int],
) -> dict[str, dict[str, Any]]:
    """Compute the implemented metrics grouped by report section."""
    grouped = _group_by_record(records)
    n_items = len(spec.ITEM_IDS)

    first_parse_ok = 0
    final_parse_ok = 0
    first_schema_ok = 0
    final_schema_ok = 0
    completed = 0
    repair_triggered = 0
    repair_succeeded = 0
    total_expected = 0
    total_valid = 0
    total_missing = 0
    lengths: list[int] = []

    for rid, attempts in grouped.items():
        first = attempts[0]
        final = attempts[-1]
        if first.parse_status == AttemptParseStatus.OK:
            first_parse_ok += 1
        if final.parse_status == AttemptParseStatus.OK:
            final_parse_ok += 1
        if first.validation_status == AttemptValidationStatus.OK:
            first_schema_ok += 1
        if final.validation_status == AttemptValidationStatus.OK:
            final_schema_ok += 1
        if final.validation_status == AttemptValidationStatus.OK:
            completed += 1
        if len(attempts) > 1:
            repair_triggered += 1
            if final.validation_status == AttemptValidationStatus.OK:
                repair_succeeded += 1

        # Range validity / missing computed on the FINAL attempt's parsed items.
        total_expected += n_items
        parsed = final.parsed_response or {}
        valid_count = 0
        if isinstance(parsed.get("items"), list):
            seen = set()
            for entry in parsed["items"]:
                if not isinstance(entry, dict):
                    continue
                iid = str(entry.get("item_id", ""))
                if iid in spec.ITEM_RANGE and iid not in seen:
                    seen.add(iid)
                    rating = entry.get("rating")
                    if isinstance(rating, int) and not isinstance(rating, bool):
                        low, high = spec.ITEM_RANGE[iid]
                        if low <= rating <= high:
                            valid_count += 1
            total_valid += valid_count
            total_missing += max(0, n_items - valid_count)
        else:
            total_missing += n_items

        length = raw_text_lengths.get(rid)
        if length is not None:
            lengths.append(length)

    def _rate(num: int, den: int) -> float | None:
        return round(num / den, 6) if den else None

    execution_quality = {
        "planned_record_count": planned,
        "completed_record_count": completed,
        "failed_record_count": planned - completed,
        "completion_rate": _rate(completed, planned),
    }

    output_quality = {
        "first_attempt_parse_success_rate": _rate(first_parse_ok, planned),
        "final_parse_success_rate": _rate(final_parse_ok, planned),
        "first_attempt_schema_compliance_rate": _rate(first_schema_ok, planned),
        "final_schema_compliance_rate": _rate(final_schema_ok, planned),
        "missing_item_rate": _rate(total_missing, total_expected),
        "range_validity_rate": _rate(total_valid, total_expected),
        "repair_trigger_rate": _rate(repair_triggered, planned),
        "repair_success_rate": _rate(repair_succeeded, repair_triggered),
        "response_length_chars": round(mean(lengths), 3) if lengths else None,
    }

    overall = aggregate_scores.get("overall_means", {})
    task_metrics = {
        "agency": overall.get("agency"),
        "free_will_attribution": overall.get("free_will_attribution"),
        "subjective_process_completeness": overall.get("subjective_process_completeness"),
        "factual_process_check": overall.get("factual_manipulation_check"),
        "condition_sensitivity": aggregate_scores.get("condition_sensitivity_agency", {}),
        "identity_effect": aggregate_scores.get("identity_effect_human_minus_ai", {}),
        "condition_means": aggregate_scores.get("condition_means", {}),
        "identity_means": aggregate_scores.get("identity_means", {}),
    }

    return {
        "execution_quality": execution_quality,
        "output_quality": output_quality,
        "task_metrics": task_metrics,
    }


def build_aggregate_report(
    *,
    run_id: str,
    benchmark_id: str,
    task_id: str,
    metrics: dict[str, dict[str, Any]],
    artifact_refs: list[ArtifactRef],
    figure_refs: list[str],
) -> AggregateReport:
    limitations = [
        "All values are MOCK engineering-validation measurements of the pipeline; "
        "they are NOT real-model results and must not be interpreted as research findings.",
        "Reliability metrics (repeat_run_stability, model_version_sensitivity) and "
        "provenance_completeness remain planned_without_formula and are not scored here.",
        "current_maturity_level is pre-BMK-L1; a real-model pilot (RUN-003) has not run.",
    ]
    return AggregateReport(
        run_id=run_id,
        benchmark_id=benchmark_id,
        task_id=task_id,
        data_source="mock_engineering_validation",
        execution_quality=metrics["execution_quality"],
        output_quality=metrics["output_quality"],
        task_metrics=metrics["task_metrics"],
        reliability_metrics={m: "planned_without_formula" for m in PLANNED_WITHOUT_FORMULA},
        comparative_metrics={},
        limitations=limitations,
        figure_refs=figure_refs,
        artifact_refs=artifact_refs,
    )


__all__ = [
    "IMPLEMENTED_METRICS",
    "PLANNED_WITHOUT_FORMULA",
    "compute_metrics",
    "build_aggregate_report",
]
