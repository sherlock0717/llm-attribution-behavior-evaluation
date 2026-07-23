"""Structural validator for the PA-Wu R1 MOCK package (NO real model, NO network).

Validates the static package assets, the manifest, and the deterministic mock
run:
- package schema (required files + input/output case fields)
- R1 route boundary is fixed (en / machine / mock_only, no translation/adaptation)
- INPUT cases run through the real validation chain (validate_input_cases)
- OUTPUT fixtures reference an existing, VALID input case; output-layer faults
- expected_scored_outputs.jsonl is the SINGLE oracle: one-to-one with outputs,
  outcome / failure_code / sub-scores / forbidden_total all match
- manifest is actually loaded and cross-checked (counts, enums, versions, hash)
- positive_control_level uses ONLY the allowed enum; the forbidden
  ``formal_calibrated_positive_control`` never appears as an active level
- fixture determinism (same inputs -> identical run hash)
- NO forbidden total is ever produced

This module is import-safe (no side effects) and is exercised by the unit test.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml

from freewill_attribution.measurement import pa_wu_p0 as p0

PACKAGE_DIR = Path(__file__).resolve().parent


def _load_run_mock():
    """Load the sibling run_mock.py by path (this dir is not an installed package)."""
    spec = importlib.util.spec_from_file_location(
        "pa_wu_r1_mock_run_mock", PACKAGE_DIR / "run_mock.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError("cannot load run_mock.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_mock = _load_run_mock()

REQUIRED_FILES = (
    "README.md",
    "mock_run_contract.yaml",
    "mock_input_cases.jsonl",
    "mock_model_outputs.jsonl",
    "expected_scored_outputs.jsonl",
    "mock_manifest.yaml",
    "run_mock.py",
    "validate_mock_package.py",
)

POSITIVE_CONTROL_LEVELS_ALLOWED = frozenset(
    {"body_fragment", "source_adapted_prototype", "none"}
)
FORBIDDEN_POSITIVE_CONTROL_LEVEL = "formal_calibrated_positive_control"


class MockPackageError(RuntimeError):
    """Raised when the R1 mock package is structurally inconsistent."""


def load_manifest() -> dict[str, Any]:
    with (PACKAGE_DIR / "mock_manifest.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def check_required_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (PACKAGE_DIR / name).is_file()]
    if missing:
        raise MockPackageError(f"missing required package files: {missing}")


def check_input_cases(contract: p0.P0Contract) -> list[dict[str, Any]]:
    """Run the real input validation chain; assert good/bad split is honest."""
    cases = run_mock.load_input_cases()
    if not cases:
        raise MockPackageError("no input cases found")
    results = run_mock.validate_input_cases(contract, cases)
    for case, res in zip(cases, results, strict=True):
        is_bad = "_bad_case" in case
        if is_bad and res["accepted"]:
            raise MockPackageError(f"bad input case {res['case_id']} was accepted")
        if not is_bad and not res["accepted"]:
            raise MockPackageError(
                f"good input case {res['case_id']} rejected: {res['validation_errors']}"
            )
    return results


def check_positive_control_levels() -> None:
    """The forbidden formal-calibrated label may appear only in a forbidden
    context; source-adapted prototypes must be explicitly flagged as prototype."""
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".jsonl", ".md", ".py"):
            continue
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_POSITIVE_CONTROL_LEVEL in text and "forbidden" not in text.lower():
            raise MockPackageError(
                f"forbidden positive-control label present unqualified in {path.name}"
            )
        if f'"level": "{FORBIDDEN_POSITIVE_CONTROL_LEVEL}"' in text:
            raise MockPackageError(f"forbidden level assigned as active level in {path.name}")
    for case in run_mock.load_input_cases():
        prov = case.get("positive_control_provenance", {})
        if str(prov.get("level")) == "source_adapted_prototype":
            if not prov.get("is_prototype") or prov.get("is_full_script") is not False:
                raise MockPackageError(
                    f"{case['case_id']}: prototype must set is_prototype=true, is_full_script=false"
                )


ALLOWED_OUTCOMES = frozenset({"accept", "reject"})


def check_oracle_one_to_one(report: dict[str, Any]) -> None:
    # Loading the oracle already rejects duplicate/empty ids (run_mock loader).
    cov = report["oracle_coverage"]
    if cov["missing_from_expected"]:
        raise MockPackageError(f"outputs missing from oracle: {cov['missing_from_expected']}")
    if cov["extra_in_expected"]:
        raise MockPackageError(f"oracle has extra ids: {cov['extra_in_expected']}")
    for row in report["expected_vs_actual_comparison"]:
        # STRICT: expected_outcome must be exactly accept/reject (no reject_or_warn).
        if str(row["expected_outcome"]) not in ALLOWED_OUTCOMES:
            raise MockPackageError(
                f"{row['output_id']}: illegal expected_outcome {row['expected_outcome']!r}"
            )
        for key in (
            "outcome_match",
            "case_id_match",
            "failure_code_match",
            "subscale_match",
            "forbidden_total_match",
        ):
            if not row[key]:
                raise MockPackageError(f"{row['output_id']}: {key} failed")


def check_output_contract_linkage_enforced(contract: p0.P0Contract) -> None:
    """Actively prove the runner rejects form/order-mismatched outputs.

    Runs classify_output on synthetic outputs that reference a VALID input case
    but carry a wrong form_id / item_order_id, so the enforcement path is
    covered by the validate_package call chain (not just by pytest fixtures).
    """
    cases = run_mock.load_input_cases()
    input_results = run_mock.validate_input_cases(contract, cases)
    accepted = {r["case_id"] for r in input_results if r["accepted"]}
    valid_input_cases = {
        str(c["case_id"]): c for c in cases if str(c["case_id"]) in accepted
    }
    ref = next(c for c in cases if c["case_id"] == "r1_neutral_02")  # wu19_only/wu_only

    wrong_form = dict(ref)
    wrong_form.update(
        {"output_id": "_synthetic_wrong_form", "response_language": "en",
         "response_identity": "machine", "form_id": "pa13_wu19_combined",
         "item_order_id": "wu_only", "raw_item_ratings": []}
    )
    res = run_mock.classify_output(contract, wrong_form, valid_input_cases)
    if res["failure_code"] != "output_contract_mismatch":
        raise MockPackageError("wrong form_id output was not rejected as output_contract_mismatch")

    wrong_order = dict(ref)
    wrong_order.update(
        {"output_id": "_synthetic_wrong_order", "response_language": "en",
         "response_identity": "machine", "form_id": "wu19_only",
         "item_order_id": "pa_first", "raw_item_ratings": []}
    )
    res = run_mock.classify_output(contract, wrong_order, valid_input_cases)
    if res["failure_code"] != "output_contract_mismatch":
        raise MockPackageError("wrong item_order_id output was not rejected as output_contract_mismatch")


def check_no_forbidden_totals(report: dict[str, Any]) -> None:
    for scores in report["subscale_level_scores"].values():
        for forbidden in p0.FORBIDDEN_SCORE_IDS:
            if forbidden in scores:
                raise MockPackageError(f"forbidden total produced: {forbidden}")


def check_determinism(contract: p0.P0Contract | None = None) -> str:
    contract = contract or p0.load_contract()
    r1 = run_mock.build_run_report(contract)
    r2 = run_mock.build_run_report(contract)
    if r1["deterministic_run_hash"] != r2["deterministic_run_hash"]:
        raise MockPackageError("mock run is non-deterministic (hash mismatch)")
    return r1["deterministic_run_hash"]


def check_manifest(report: dict[str, Any]) -> None:
    """Actually load the manifest and cross-check its declarations."""
    m = load_manifest()

    # files
    if set(m["files"]) != set(REQUIRED_FILES):
        raise MockPackageError("manifest file list does not match required files")

    # input counts
    cases = run_mock.load_input_cases()
    good = [c for c in cases if "_bad_case" not in c]
    bad = [c for c in cases if "_bad_case" in c]
    ic = m["input_cases"]
    if ic["total"] != len(cases) or ic["good_total"] != len(good) or ic["bad_total"] != len(bad):
        raise MockPackageError("manifest input_cases counts mismatch")
    if len(m["input_cases"]["bad_cases"]) != len(bad):
        raise MockPackageError("manifest bad_cases list length mismatch")

    # output counts + kinds
    outputs = run_mock.load_model_outputs()
    if m["model_output_fixtures"]["total"] != len(outputs):
        raise MockPackageError("manifest output total mismatch")
    manifest_kinds = set(m["model_output_fixtures"]["kinds"])
    actual_kinds = {str(o["output_kind"]) for o in outputs}
    if manifest_kinds != actual_kinds:
        raise MockPackageError(f"manifest output kinds mismatch: {manifest_kinds ^ actual_kinds}")

    # failure code closed set
    if set(m["failure_codes"]) != set(run_mock.FAILURE_CODES):
        raise MockPackageError("manifest failure_codes do not match runner FAILURE_CODES")

    # P0 scoring version + forbidden score ids
    if str(m["reuses"]["p0_scoring_version"]) != p0.SCORING_VERSION:
        raise MockPackageError("manifest p0_scoring_version mismatch")
    if set(m["forbidden_score_ids"]) != set(p0.FORBIDDEN_SCORE_IDS):
        raise MockPackageError("manifest forbidden_score_ids mismatch")

    # positive-control enums
    if set(m["positive_control_levels_allowed"]) != POSITIVE_CONTROL_LEVELS_ALLOWED:
        raise MockPackageError("manifest allowed positive-control enum mismatch")
    if FORBIDDEN_POSITIVE_CONTROL_LEVEL not in m["positive_control_levels_forbidden"]:
        raise MockPackageError("manifest must forbid formal_calibrated_positive_control")

    # deterministic hash reference MUST equal the actual run hash
    if str(m["deterministic_run_hash_reference"]) != report["deterministic_run_hash"]:
        raise MockPackageError(
            "manifest deterministic_run_hash_reference != actual run hash "
            f"({m['deterministic_run_hash_reference']} != {report['deterministic_run_hash']})"
        )


def validate_package() -> dict[str, Any]:
    """Full package validation; returns the deterministic run report."""
    check_required_files()
    contract = p0.load_contract()
    check_input_cases(contract)
    check_positive_control_levels()
    check_output_contract_linkage_enforced(contract)
    run_hash = check_determinism(contract)
    report = run_mock.build_run_report(contract)
    if report["deterministic_run_hash"] != run_hash:
        raise MockPackageError("run hash changed between determinism check and report")
    check_oracle_one_to_one(report)
    check_no_forbidden_totals(report)
    check_manifest(report)
    return report


def main() -> None:  # pragma: no cover - convenience entry point
    report = validate_package()
    print("R1 mock package OK; deterministic_run_hash =", report["deterministic_run_hash"])


if __name__ == "__main__":  # pragma: no cover
    main()
