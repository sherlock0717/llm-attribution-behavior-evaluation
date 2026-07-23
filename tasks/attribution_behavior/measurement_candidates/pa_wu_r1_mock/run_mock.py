"""PA-Wu R1 English machine-only MOCK runner (NO real model, NO network).

This runner consumes the *static* mock fixtures in this directory and scores
them by DELEGATING to the P0 engine
(``freewill_attribution.measurement.pa_wu_p0``). It never generates model
output, never calls a network, never reads an API key, and never reads the
R2/R3 assets. All scoring/validation reuses the P0 contract; there is NO second
scoring implementation here.

R1 route boundary (fixed): language=en, target_identity=machine, machine-only,
no translation, not a construct adaptation, package_status=mock_only.

Outputs (see ``build_run_report``):
- package_manifest
- case_validation_results
- item_level_scores
- subscale_level_scores
- expected_vs_actual_comparison
- failure_codes
- deterministic_run_hash

No forbidden total (WU19_TOTAL / MACHINE_AGENCY_TOTAL / PA_WU_TOTAL) is ever
emitted; requesting one yields a ``forbidden_total`` failure code.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from freewill_attribution.measurement import pa_wu_p0 as p0

PACKAGE_DIR = Path(__file__).resolve().parent

# Fixed R1 boundary (mirrors mock_run_contract.yaml).
R1_LANGUAGE = "en"
R1_IDENTITY = "machine"

# Failure codes this runner can emit (closed set).
FAILURE_CODES = (
    "missing_items",
    "out_of_range",
    "unknown_item",
    "duplicate_item",
    "non_numeric_rating",
    "forbidden_total",
    "wrong_language",
    "wrong_identity",
    "unparseable_json",
    "missing_required_field",
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_input_cases() -> list[dict[str, Any]]:
    return _read_jsonl(PACKAGE_DIR / "mock_input_cases.jsonl")


def load_model_outputs() -> list[dict[str, Any]]:
    return _read_jsonl(PACKAGE_DIR / "mock_model_outputs.jsonl")


# ---------------------------------------------------------------------------
# Per-output classification (delegates to P0 for scale/id/scoring rules)
# ---------------------------------------------------------------------------


def classify_output(
    contract: p0.P0Contract,
    output: dict[str, Any],
) -> dict[str, Any]:
    """Validate a single static mock output; return a normalized result.

    Returns a dict with: output_id, case_id, output_kind, accepted (bool),
    failure_code (str|None), item_level_scores (dict), subscale_level_scores
    (dict), and the P0 validation/scoring warnings.
    """
    output_id = str(output.get("output_id"))
    case_id = str(output.get("case_id"))
    kind = str(output.get("output_kind"))
    form_id = str(output.get("form_id"))
    order_id = str(output.get("item_order_id"))

    result: dict[str, Any] = {
        "output_id": output_id,
        "case_id": case_id,
        "output_kind": kind,
        "accepted": False,
        "failure_code": None,
        "item_level_scores": {},
        "subscale_level_scores": {},
        "validation_warnings": [],
        "scoring_warnings": [],
    }

    # 1) Unparseable JSON payload -> cannot even parse ratings.
    if output.get("raw_item_ratings") is None and output.get("raw_text_payload") is not None:
        try:
            json.loads(str(output["raw_text_payload"]))
        except (ValueError, TypeError):
            result["failure_code"] = "unparseable_json"
            return result
        # If it *did* parse we fall through, but our fixture is intentionally broken.

    # 2) R1 boundary: wrong language / identity (checked before scoring).
    resp_lang = output.get("response_language")
    if resp_lang is not None and str(resp_lang) != R1_LANGUAGE:
        result["failure_code"] = "wrong_language"
        return result
    resp_identity = output.get("response_identity")
    if resp_identity is not None and str(resp_identity) != R1_IDENTITY:
        result["failure_code"] = "wrong_identity"
        return result

    # 3) Forbidden aggregate totals must never be produced.
    for key in ("extra_totals", "requested_scores"):
        blob = output.get(key)
        ids: list[str] = []
        if isinstance(blob, dict):
            ids = [str(k) for k in blob]
        elif isinstance(blob, list):
            ids = [str(k) for k in blob]
        if any(i in p0.FORBIDDEN_SCORE_IDS for i in ids):
            result["failure_code"] = "forbidden_total"
            return result

    ratings = output.get("raw_item_ratings")
    if not isinstance(ratings, list):
        result["failure_code"] = "unparseable_json"
        return result

    # 4) Delegate the hard scale/id/duplicate/missing rules to the P0 engine.
    try:
        warnings = p0.validate_response(contract, form_id, order_id, ratings)
    except p0.P0ContractError as exc:
        result["failure_code"] = _map_p0_error(str(exc))
        return result

    result["validation_warnings"] = warnings
    if any(w.startswith("missing_items") for w in warnings):
        result["failure_code"] = "missing_items"
        return result

    # 5) Accepted: derive P0 sub-scores (item + subscale level), no totals.
    rating_map = {str(e["item_id"]): e["rating"] for e in ratings}
    score = p0.derive_scores(contract, rating_map)
    for forbidden in p0.FORBIDDEN_SCORE_IDS:
        if forbidden in score.derived_scores:  # defensive; engine never emits these
            result["failure_code"] = "forbidden_total"
            return result

    result["accepted"] = True
    result["item_level_scores"] = {str(k): v for k, v in rating_map.items()}
    result["subscale_level_scores"] = dict(score.derived_scores)
    result["scoring_warnings"] = list(score.scoring_warnings)
    return result


def _map_p0_error(message: str) -> str:
    low = message.lower()
    if "duplicate item_id" in low:
        return "duplicate_item"
    if "unknown item_id" in low:
        return "unknown_item"
    if "out_of_range" in low or "out-of-range" in low:
        return "out_of_range"
    if "non-numeric" in low:
        return "non_numeric_rating"
    if "missing item_id/rating" in low:
        return "missing_required_field"
    return "unknown_item"


# ---------------------------------------------------------------------------
# Full run report
# ---------------------------------------------------------------------------


def _package_manifest(contract: p0.P0Contract) -> dict[str, Any]:
    return {
        "contract_id": "pa_wu_r1_mock.mock_run_contract.v1",
        "route_id": "R1",
        "language": R1_LANGUAGE,
        "target_identity": R1_IDENTITY,
        "human_parallel_version": False,
        "translation_used": False,
        "is_construct_adaptation": False,
        "real_model_execution": False,
        "package_status": "mock_only",
        "reuses_p0_scoring_version": p0.SCORING_VERSION,
        "forbidden_score_ids": sorted(p0.FORBIDDEN_SCORE_IDS),
    }


def build_run_report(contract: p0.P0Contract | None = None) -> dict[str, Any]:
    """Run the full deterministic mock and return the structured report."""
    contract = contract or p0.load_contract()
    outputs = load_model_outputs()

    case_results: list[dict[str, Any]] = []
    item_level_scores: dict[str, dict[str, Any]] = {}
    subscale_level_scores: dict[str, dict[str, Any]] = {}
    comparison: list[dict[str, Any]] = []
    failure_codes: dict[str, str | None] = {}

    for output in outputs:
        res = classify_output(contract, output)
        oid = res["output_id"]
        case_results.append(res)
        failure_codes[oid] = res["failure_code"]
        if res["accepted"]:
            item_level_scores[oid] = res["item_level_scores"]
            subscale_level_scores[oid] = res["subscale_level_scores"]

        expected_outcome = str(output.get("expected_outcome", ""))
        actual_outcome = "accept" if res["accepted"] else "reject"
        # "reject_or_warn" fixtures are satisfied by a warn-based rejection too.
        outcome_match = (
            actual_outcome == expected_outcome
            or (expected_outcome == "reject_or_warn" and actual_outcome == "reject")
        )
        expected_fc = output.get("failure_code_expected")
        comparison.append(
            {
                "output_id": oid,
                "expected_outcome": expected_outcome,
                "actual_outcome": actual_outcome,
                "outcome_match": outcome_match,
                "expected_failure_code": expected_fc,
                "actual_failure_code": res["failure_code"],
                "failure_code_match": (expected_fc is None or expected_fc == res["failure_code"]),
            }
        )

    report = {
        "package_manifest": _package_manifest(contract),
        "case_validation_results": case_results,
        "item_level_scores": item_level_scores,
        "subscale_level_scores": subscale_level_scores,
        "expected_vs_actual_comparison": comparison,
        "failure_codes": failure_codes,
    }
    report["deterministic_run_hash"] = compute_run_hash(report)
    return report


def compute_run_hash(report: dict[str, Any]) -> str:
    """Stable sha256[:16] over the report minus the hash field itself."""
    payload = {k: v for k, v in report.items() if k != "deterministic_run_hash"}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> None:  # pragma: no cover - convenience entry point
    report = build_run_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
