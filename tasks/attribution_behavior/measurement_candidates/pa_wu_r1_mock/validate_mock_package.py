"""Structural validator for the PA-Wu R1 MOCK package (NO real model, NO network).

Validates the static package assets and the deterministic mock run:
- package schema (required files + input/output case fields present)
- R1 route boundary is fixed (en / machine / mock_only, no translation/adaptation)
- positive_control_level uses ONLY the allowed enum; the forbidden
  ``formal_calibrated_positive_control`` never appears
- source-adapted prototypes are explicitly flagged as prototypes
- fixture determinism (same inputs -> identical run hash)
- every declared bad case is rejected with the expected failure code
- NO forbidden total is ever produced

This module is import-safe (no side effects) and is exercised by the unit test.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

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

INPUT_CASE_REQUIRED_FIELDS = (
    "case_id",
    "scenario_id",
    "source_route",
    "language",
    "target_identity",
    "scenario_text",
    "item_set_version",
    "selected_item_ids",
    "expected_response_schema",
    "positive_control_provenance",
    "mock_only",
)

POSITIVE_CONTROL_LEVELS_ALLOWED = frozenset(
    {"body_fragment", "source_adapted_prototype", "none"}
)
FORBIDDEN_POSITIVE_CONTROL_LEVEL = "formal_calibrated_positive_control"


class MockPackageError(RuntimeError):
    """Raised when the R1 mock package is structurally inconsistent."""


def check_required_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (PACKAGE_DIR / name).is_file()]
    if missing:
        raise MockPackageError(f"missing required package files: {missing}")


def check_input_cases() -> list[dict[str, Any]]:
    cases = run_mock.load_input_cases()
    if not cases:
        raise MockPackageError("no input cases found")
    for case in cases:
        for field_name in INPUT_CASE_REQUIRED_FIELDS:
            # A declared bad case may deliberately omit exactly one field.
            if field_name not in case and not str(case.get("_bad_case", "")).startswith(
                "missing_required_field"
            ):
                raise MockPackageError(
                    f"input case {case.get('case_id')} missing field {field_name}"
                )
        if "_bad_case" not in case:
            if str(case["source_route"]) != "R1":
                raise MockPackageError(f"{case['case_id']}: source_route must be R1")
            if str(case["language"]) != "en":
                raise MockPackageError(f"{case['case_id']}: language must be en")
            if str(case["target_identity"]) != "machine":
                raise MockPackageError(f"{case['case_id']}: target_identity must be machine")
        level = str(case.get("positive_control_provenance", {}).get("level", "none"))
        if level not in POSITIVE_CONTROL_LEVELS_ALLOWED:
            raise MockPackageError(f"{case['case_id']}: illegal positive_control level {level}")
    return cases


def check_positive_control_levels() -> None:
    """No asset may use the forbidden formal-calibrated positive-control label,
    and every source-adapted prototype must be explicitly flagged as prototype."""
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".jsonl", ".md", ".py"):
            continue
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_POSITIVE_CONTROL_LEVEL in text and "forbidden" not in text.lower():
            # allowed only when explicitly named as forbidden (contract/validator/docs)
            raise MockPackageError(
                f"forbidden positive-control label present unqualified in {path.name}"
            )
    for case in run_mock.load_input_cases():
        prov = case.get("positive_control_provenance", {})
        if str(prov.get("level")) == "source_adapted_prototype":
            if not prov.get("is_prototype"):
                raise MockPackageError(
                    f"{case['case_id']}: source_adapted_prototype must set is_prototype=true"
                )
            if prov.get("is_full_script") is not False:
                raise MockPackageError(
                    f"{case['case_id']}: prototype must set is_full_script=false"
                )


def check_determinism(contract: p0.P0Contract | None = None) -> str:
    """Run the mock twice and assert an identical deterministic hash."""
    contract = contract or p0.load_contract()
    r1 = run_mock.build_run_report(contract)
    r2 = run_mock.build_run_report(contract)
    if r1["deterministic_run_hash"] != r2["deterministic_run_hash"]:
        raise MockPackageError("mock run is non-deterministic (hash mismatch)")
    return r1["deterministic_run_hash"]


def check_no_forbidden_totals(report: dict[str, Any]) -> None:
    for scores in report["subscale_level_scores"].values():
        for forbidden in p0.FORBIDDEN_SCORE_IDS:
            if forbidden in scores:
                raise MockPackageError(f"forbidden total produced: {forbidden}")


def validate_package() -> dict[str, Any]:
    """Full package validation; returns the deterministic run report."""
    check_required_files()
    check_input_cases()
    check_positive_control_levels()
    contract = p0.load_contract()
    run_hash = check_determinism(contract)
    report = run_mock.build_run_report(contract)
    check_no_forbidden_totals(report)
    if report["deterministic_run_hash"] != run_hash:
        raise MockPackageError("run hash changed between determinism check and report")
    return report


def main() -> None:  # pragma: no cover - convenience entry point
    report = validate_package()
    print("R1 mock package OK; deterministic_run_hash =", report["deterministic_run_hash"])


if __name__ == "__main__":  # pragma: no cover
    main()
