"""PA-Wu R1 English machine-only MOCK runner (NO real model, NO network).

This runner consumes the *static* mock fixtures in this directory and scores
them by DELEGATING to the P0 engine
(``freewill_attribution.measurement.pa_wu_p0``). It never generates model
output, never calls a network, never reads an API key, and never reads the
R2/R3 assets. All scoring/validation reuses the P0 contract; there is NO second
scoring implementation here, and the item-wording ``administration_hash`` is
computed by the P0 engine (never re-implemented).

R1 route boundary (fixed): language=en, target_identity=machine, machine-only,
no translation, not a construct adaptation, package_status=mock_only.

The runner separates INPUT-case validation from OUTPUT-fixture validation:
- ``validate_input_cases`` -> input_case_validation_results
- ``classify_output``      -> output_validation_results
``expected_scored_outputs.jsonl`` is the SINGLE static oracle for output
outcomes / failure codes / sub-scores.

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


class MockFixtureError(RuntimeError):
    """Raised when a static fixture file is structurally invalid (e.g. duplicate/empty id)."""

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
    "wrong_route",
    "item_set_version_mismatch",
    "selected_items_mismatch",
    "illegal_positive_control",
    "unknown_output_case",
    "output_contract_mismatch",
    "p0_contract_error",
)

INPUT_CASE_REQUIRED_FIELDS = (
    "case_id",
    "scenario_id",
    "source_route",
    "language",
    "target_identity",
    "condition_id",
    "choice_direction",
    "scenario_text",
    "item_set_version",
    "form_id",
    "item_order_id",
    "selected_item_ids",
    "expected_response_schema",
    "positive_control_provenance",
    "mock_only",
)

POSITIVE_CONTROL_LEVELS_ALLOWED = frozenset(
    {"body_fragment", "source_adapted_prototype", "none"}
)
FORBIDDEN_POSITIVE_CONTROL_LEVEL = "formal_calibrated_positive_control"


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


def _assert_unique_nonempty_ids(rows: list[dict[str, Any]], source: str) -> None:
    """Every row must carry a non-empty, unique output_id (no silent overwrite)."""
    seen: set[str] = set()
    for row in rows:
        oid = str(row.get("output_id", "")).strip()
        if not oid:
            raise MockFixtureError(f"{source}: empty/missing output_id in row {row!r}")
        if oid in seen:
            raise MockFixtureError(f"{source}: duplicate output_id {oid!r}")
        seen.add(oid)


def load_model_outputs() -> list[dict[str, Any]]:
    rows = _read_jsonl(PACKAGE_DIR / "mock_model_outputs.jsonl")
    _assert_unique_nonempty_ids(rows, "mock_model_outputs.jsonl")
    return rows


def load_expected_scored_outputs() -> dict[str, dict[str, Any]]:
    """Single static oracle: output_id -> expected record.

    Duplicate or empty output_ids raise (no dict-comprehension silent overwrite).
    """
    rows = _read_jsonl(PACKAGE_DIR / "expected_scored_outputs.jsonl")
    _assert_unique_nonempty_ids(rows, "expected_scored_outputs.jsonl")
    oracle: dict[str, dict[str, Any]] = {}
    for row in rows:
        oracle[str(row["output_id"])] = row
    return oracle


# ---------------------------------------------------------------------------
# INPUT-case validation (real validation chain, not a label-based skip)
# ---------------------------------------------------------------------------


def validate_input_case(contract: p0.P0Contract, case: dict[str, Any]) -> dict[str, Any]:
    """Validate a single input case; always returns a concrete result.

    Result keys: case_id, accepted, failure_codes, validation_errors, form_id,
    item_order_id, administration_hash, mock_only.
    """
    case_id = str(case.get("case_id", ""))
    form_id = str(case.get("form_id", ""))
    order_id = str(case.get("item_order_id", ""))
    errors: list[str] = []
    codes: list[str] = []

    # 1) required fields present
    for field_name in INPUT_CASE_REQUIRED_FIELDS:
        if field_name not in case:
            errors.append(f"missing_required_field:{field_name}")
            if "missing_required_field" not in codes:
                codes.append("missing_required_field")

    # 2) R1 route boundary (only checked when the field exists)
    if "source_route" in case and str(case["source_route"]) != "R1":
        errors.append(f"source_route!=R1:{case['source_route']}")
        codes.append("wrong_route")
    if "language" in case and str(case["language"]) != R1_LANGUAGE:
        errors.append(f"language!=en:{case['language']}")
        codes.append("wrong_language")
    if "target_identity" in case and str(case["target_identity"]) != R1_IDENTITY:
        errors.append(f"target_identity!=machine:{case['target_identity']}")
        codes.append("wrong_identity")
    if "mock_only" in case and case["mock_only"] is not True:
        errors.append("mock_only!=true")
        codes.append("missing_required_field")

    # 3) item_set_version == P0 scoring version
    if "item_set_version" in case and str(case["item_set_version"]) != p0.SCORING_VERSION:
        errors.append(f"item_set_version!={p0.SCORING_VERSION}:{case['item_set_version']}")
        codes.append("item_set_version_mismatch")

    # 4) form/order resolvable by P0 + selected_item_ids exactly equals P0 build
    admin_hash: str | None = None
    try:
        expected_ids = p0.build_form_item_ids(contract, form_id, order_id)
        if "selected_item_ids" in case:
            if [str(x) for x in case["selected_item_ids"]] != expected_ids:
                errors.append("selected_item_ids!=p0.build_form_item_ids (order-sensitive)")
                codes.append("selected_items_mismatch")
        # administration_hash reuses the P0 engine (never re-implemented here)
        admin_hash = administration_hash_for_case(contract, case)
    except p0.P0ContractError as exc:
        errors.append(f"p0:{exc}")
        codes.append(_map_p0_error(str(exc)))

    # 5) requested_scores must not contain a forbidden total
    requested = case.get("requested_scores")
    if isinstance(requested, list) and any(
        str(s) in p0.FORBIDDEN_SCORE_IDS for s in requested
    ):
        errors.append("requested_scores contains a forbidden total")
        codes.append("forbidden_total")

    # 6) positive-control enum + provenance
    prov = case.get("positive_control_provenance", {})
    level = str(prov.get("level", "none")) if isinstance(prov, dict) else "none"
    if level not in POSITIVE_CONTROL_LEVELS_ALLOWED or level == FORBIDDEN_POSITIVE_CONTROL_LEVEL:
        errors.append(f"illegal positive_control level:{level}")
        codes.append("illegal_positive_control")
    if level == "source_adapted_prototype" and isinstance(prov, dict):
        if prov.get("is_prototype") is not True or prov.get("is_full_script") is not False:
            errors.append("prototype must set is_prototype=true and is_full_script=false")
            codes.append("illegal_positive_control")

    accepted = not errors
    return {
        "case_id": case_id,
        "accepted": accepted,
        "failure_codes": codes,
        "failure_code": codes[0] if codes else None,
        "validation_errors": errors,
        "form_id": form_id,
        "item_order_id": order_id,
        "administration_hash": admin_hash,
        "mock_only": bool(case.get("mock_only", False)),
    }


def validate_input_cases(
    contract: p0.P0Contract, cases: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    cases = cases if cases is not None else load_input_cases()
    return [validate_input_case(contract, c) for c in cases]


def _identity_for_hash(case: dict[str, Any]) -> str:
    # target_identity maps to the P0 record `identity` field.
    return str(case.get("target_identity", ""))


def administration_hash_for_case(contract: p0.P0Contract, case: dict[str, Any]) -> str:
    """Reuse p0.administration_hash for a case (repeat_index=0, fixed material)."""
    material = {
        "scenario_id": str(case.get("scenario_id", "")),
        "condition_id": str(case.get("condition_id", "")),
        "identity": _identity_for_hash(case),
        "choice_direction": str(case.get("choice_direction", "")),
    }
    return p0.administration_hash(
        contract,
        str(case["form_id"]),
        str(case["item_order_id"]),
        material,
        0,
    )


# ---------------------------------------------------------------------------
# OUTPUT-fixture classification (delegates to P0 for scale/id/scoring rules)
# ---------------------------------------------------------------------------


def classify_output(
    contract: p0.P0Contract,
    output: dict[str, Any],
    valid_input_cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Validate a single static mock output; return a normalized result.

    ``valid_input_cases`` maps case_id -> the ACCEPTED input case dict. The
    output must reference an existing valid case AND its form_id/item_order_id
    must match that input case, or it is rejected with ``output_contract_mismatch``.
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

    # 0a) The output must reference an EXISTING, VALID input case.
    input_case = valid_input_cases.get(case_id)
    if input_case is None:
        result["failure_code"] = "unknown_output_case"
        return result

    # 0b) form_id / item_order_id MUST match the referenced input case.
    if form_id != str(input_case.get("form_id")) or order_id != str(
        input_case.get("item_order_id")
    ):
        result["failure_code"] = "output_contract_mismatch"
        return result

    # 1) response_language / response_identity are REQUIRED at the output layer.
    if "response_language" not in output or "response_identity" not in output:
        result["failure_code"] = "missing_required_field"
        return result
    if str(output["response_language"]) != R1_LANGUAGE:
        result["failure_code"] = "wrong_language"
        return result
    if str(output["response_identity"]) != R1_IDENTITY:
        result["failure_code"] = "wrong_identity"
        return result

    # 2) Unparseable JSON payload -> cannot even parse ratings.
    if output.get("raw_item_ratings") is None and output.get("raw_text_payload") is not None:
        try:
            json.loads(str(output["raw_text_payload"]))
        except (ValueError, TypeError):
            result["failure_code"] = "unparseable_json"
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
    """Map a P0ContractError message to a failure code.

    Unrecognized errors are NEVER silently mapped to ``unknown_item``; they
    surface as ``p0_contract_error`` so no misclassification is hidden.
    """
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
    if "unknown form_id" in low or "unknown item_order_id" in low:
        return "p0_contract_error"
    return "p0_contract_error"


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

    input_cases = load_input_cases()
    input_results = validate_input_cases(contract, input_cases)
    accepted_case_ids = {r["case_id"] for r in input_results if r["accepted"]}
    valid_input_cases = {
        str(c["case_id"]): c for c in input_cases if str(c["case_id"]) in accepted_case_ids
    }

    outputs = load_model_outputs()
    expected = load_expected_scored_outputs()

    output_results: list[dict[str, Any]] = []
    item_level_scores: dict[str, dict[str, Any]] = {}
    subscale_level_scores: dict[str, dict[str, Any]] = {}
    comparison: list[dict[str, Any]] = []
    failure_codes: dict[str, str | None] = {}

    output_ids = [str(o.get("output_id")) for o in outputs]

    for output in outputs:
        res = classify_output(contract, output, valid_input_cases)
        oid = res["output_id"]
        output_results.append(res)
        failure_codes[oid] = res["failure_code"]
        if res["accepted"]:
            item_level_scores[oid] = res["item_level_scores"]
            subscale_level_scores[oid] = res["subscale_level_scores"]

        exp = expected.get(oid, {})
        actual_outcome = "accept" if res["accepted"] else "reject"
        expected_outcome = str(exp.get("expected_outcome", ""))
        # STRICT: only "accept"/"reject" are valid; exact equality (no reject_or_warn).
        outcome_match = actual_outcome == expected_outcome
        # oracle.case_id must agree with the output's referenced case_id
        case_id_match = str(exp.get("case_id", "")) == res["case_id"]
        expected_fc = exp.get("expected_failure_code")
        actual_subscales = res["subscale_level_scores"]
        expected_subscales = exp.get("expected_subscale_level_scores", {})
        forbidden_present = any(
            f in actual_subscales for f in p0.FORBIDDEN_SCORE_IDS
        )
        comparison.append(
            {
                "output_id": oid,
                "expected_outcome": expected_outcome,
                "actual_outcome": actual_outcome,
                "outcome_match": outcome_match,
                "case_id_match": case_id_match,
                "expected_failure_code": expected_fc,
                "actual_failure_code": res["failure_code"],
                "failure_code_match": (expected_fc == res["failure_code"]),
                "expected_subscale_level_scores": expected_subscales,
                "actual_subscale_level_scores": actual_subscales,
                "subscale_match": (
                    {k: float(v) for k, v in expected_subscales.items()}
                    == {k: float(v) for k, v in actual_subscales.items()}
                ),
                "expected_forbidden_total_present": bool(exp.get("forbidden_total_present", False)),
                "actual_forbidden_total_present": forbidden_present,
                "forbidden_total_match": (
                    bool(exp.get("forbidden_total_present", False)) == forbidden_present
                ),
            }
        )

    report = {
        "package_manifest": _package_manifest(contract),
        "input_case_validation_results": input_results,
        "output_validation_results": output_results,
        "item_level_scores": item_level_scores,
        "subscale_level_scores": subscale_level_scores,
        "expected_vs_actual_comparison": comparison,
        "failure_codes": failure_codes,
        "oracle_coverage": {
            "output_ids": sorted(output_ids),
            "expected_ids": sorted(expected),
            "missing_from_expected": sorted(set(output_ids) - set(expected)),
            "extra_in_expected": sorted(set(expected) - set(output_ids)),
        },
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
