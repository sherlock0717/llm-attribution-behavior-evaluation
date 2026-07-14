"""Scoring and cell aggregation for the freewill-attribution task (FAST-001).

Scoring is an item-mean per construct (matching the historical aggregation
approach). Aggregation summarises construct means by process condition and by
identity, and computes predefined condition-sensitivity contrasts.

These are mock-pipeline computations used to validate the engineering chain.
They are NOT research findings and must never be presented as real-model results.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

from . import spec


def score_ratings(ratings: dict[str, int]) -> dict[str, float | None]:
    """Compute per-scale (construct) item means from a single record's ratings."""
    scores: dict[str, float | None] = {}
    for scale, item_ids in spec.SCALE_ITEMS.items():
        values = [ratings[i] for i in item_ids if i in ratings and ratings[i] is not None]
        scores[scale] = round(mean(values), 6) if values else None
    return scores


def aggregate_scores(
    scored_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-record construct scores into task metrics.

    ``scored_records`` is a list of dicts each with keys: ``condition``,
    ``identity`` and ``scores`` (the per-scale means).
    """
    by_condition: dict[str, dict[str, list[float]]] = {}
    by_identity: dict[str, dict[str, list[float]]] = {}
    overall: dict[str, list[float]] = {}

    for rec in scored_records:
        cond = rec["condition"]
        ident = rec["identity"]
        for scale, value in rec["scores"].items():
            if value is None:
                continue
            by_condition.setdefault(cond, {}).setdefault(scale, []).append(value)
            by_identity.setdefault(ident, {}).setdefault(scale, []).append(value)
            overall.setdefault(scale, []).append(value)

    def _means(table: dict[str, dict[str, list[float]]]) -> dict[str, dict[str, float]]:
        return {
            key: {scale: round(mean(vals), 6) for scale, vals in scales.items() if vals}
            for key, scales in table.items()
        }

    condition_means = _means(by_condition)
    identity_means = _means(by_identity)
    overall_means = {scale: round(mean(vals), 6) for scale, vals in overall.items() if vals}

    # Predefined condition-sensitivity contrasts on agency (primary construct).
    contrasts: dict[str, Any] = {}
    for high, low in spec.CONDITION_CONTRASTS:
        hi = condition_means.get(high, {}).get("agency")
        lo = condition_means.get(low, {}).get("agency")
        if hi is not None and lo is not None:
            contrasts[f"{high}_vs_{low}"] = round(hi - lo, 6)

    # Identity effect on free_will_attribution (AI vs human), if both present.
    identity_effect: dict[str, Any] = {}
    ai = identity_means.get("AI 决策者", {})
    hu = identity_means.get("人类决策者", {})
    for scale in ("agency", "free_will_attribution"):
        if scale in ai and scale in hu:
            identity_effect[scale] = round(hu[scale] - ai[scale], 6)

    return {
        "overall_means": overall_means,
        "condition_means": condition_means,
        "identity_means": identity_means,
        "condition_sensitivity_agency": contrasts,
        "identity_effect_human_minus_ai": identity_effect,
    }


__all__ = ["score_ratings", "aggregate_scores"]
