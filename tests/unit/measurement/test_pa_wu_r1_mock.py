"""Structural + behavioral tests for the PA-Wu R1 MOCK execution package.

NO real model, NO network, NO API key. All scoring is delegated to the P0
engine (freewill_attribution.measurement.pa_wu_p0); this test asserts the mock
package reuses that contract and never invents a second scoring path.

Covered (task section 9):
- package schema (required files present, input/output case fields)
- fixture determinism (same inputs -> identical run hash)
- a legal case is accepted and scored
- every bad-case kind is rejected with the expected failure code
- no forbidden total is ever produced
- no network call / no API key / no real model client in package sources
- the package does not read R2/R3 assets
- source-adapted prototype is never labeled a formal positive control
"""

from __future__ import annotations

import importlib.util
import re

import pytest

from freewill_attribution.measurement import pa_wu_p0 as p0
from freewill_attribution.paths import PROJECT_ROOT

PKG_DIR = (
    PROJECT_ROOT
    / "tasks"
    / "attribution_behavior"
    / "measurement_candidates"
    / "pa_wu_r1_mock"
)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PKG_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def run_mock():
    return _load_module("pa_wu_r1_mock_run_mock", "run_mock.py")


@pytest.fixture(scope="module")
def validator():
    return _load_module("pa_wu_r1_mock_validate", "validate_mock_package.py")


@pytest.fixture(scope="module")
def contract() -> p0.P0Contract:
    return p0.load_contract()


@pytest.fixture(scope="module")
def report(run_mock, contract):
    return run_mock.build_run_report(contract)


# --- 1: package schema --------------------------------------------------------


def test_required_files_present(validator) -> None:
    validator.check_required_files()  # raises if any missing


def test_input_cases_schema(validator) -> None:
    cases = validator.check_input_cases()
    assert len(cases) == 7
    good = [c for c in cases if "_bad_case" not in c]
    bad = [c for c in cases if "_bad_case" in c]
    assert len(good) == 4  # 2 neutral + 2 wu-cue
    assert len(bad) == 3


def test_manifest_route_boundary(report) -> None:
    m = report["package_manifest"]
    assert m["route_id"] == "R1"
    assert m["language"] == "en"
    assert m["target_identity"] == "machine"
    assert m["human_parallel_version"] is False
    assert m["translation_used"] is False
    assert m["is_construct_adaptation"] is False
    assert m["real_model_execution"] is False
    assert m["package_status"] == "mock_only"


# --- 2: fixture determinism ---------------------------------------------------


def test_run_is_deterministic(run_mock, contract) -> None:
    r1 = run_mock.build_run_report(contract)
    r2 = run_mock.build_run_report(contract)
    assert r1["deterministic_run_hash"] == r2["deterministic_run_hash"]
    assert r1 == r2


# --- 3: a legal case is accepted and scored -----------------------------------


def test_legal_case_accepted_and_scored(report) -> None:
    fc = report["failure_codes"]
    assert fc["out_complete_valid"] is None
    scores = report["subscale_level_scores"]["out_complete_valid"]
    # wu19_only form -> the four Wu sub-scores are present, PA is skipped-with-warning
    assert set(scores) == {"IN4", "GO4", "MSI6", "IC5"}
    for v in scores.values():
        assert isinstance(v, float)


# --- 4: every bad-case kind rejected with the expected failure code -----------


def test_bad_cases_rejected_with_expected_codes(report) -> None:
    expected = {
        "out_missing_item": "missing_items",
        "out_scale_out_of_range": "out_of_range",
        "out_msi_out_of_range": "out_of_range",
        "out_illegal_item_id": "unknown_item",
        "out_forbidden_total": "forbidden_total",
        "out_wrong_language": "wrong_language",
        "out_wrong_identity": "wrong_identity",
        "out_illegal_free_text": "non_numeric_rating",
        "out_duplicate_item": "duplicate_item",
        "out_unparseable_json": "unparseable_json",
    }
    fc = report["failure_codes"]
    for oid, code in expected.items():
        assert fc[oid] == code, f"{oid}: expected {code}, got {fc[oid]}"
    # none of the bad outputs was accepted
    accepted = {r["output_id"] for r in report["case_validation_results"] if r["accepted"]}
    assert accepted == {"out_complete_valid"}


def test_expected_vs_actual_all_match(report) -> None:
    for row in report["expected_vs_actual_comparison"]:
        assert row["outcome_match"], f"{row['output_id']} outcome mismatch"
        assert row["failure_code_match"], f"{row['output_id']} failure_code mismatch"


# --- 5: no forbidden totals ---------------------------------------------------


def test_no_forbidden_totals(report) -> None:
    for scores in report["subscale_level_scores"].values():
        for forbidden in p0.FORBIDDEN_SCORE_IDS:
            assert forbidden not in scores
    # the forbidden-total request is rejected, not scored
    assert report["failure_codes"]["out_forbidden_total"] == "forbidden_total"


def test_no_forbidden_total_markers_in_assets() -> None:
    markers = ("WU19_TOTAL", "MACHINE_AGENCY_TOTAL", "PA_WU_TOTAL")
    # These markers may appear ONLY in guard/forbidden contexts (contract lists,
    # validator, the deliberate bad-case). Assert they never appear as a produced
    # derived score by checking the run report instead (done above); here we just
    # ensure data files that are NOT the forbidden fixture do not emit a total key.
    for path in PKG_DIR.glob("expected_scored_outputs.jsonl"):
        text = path.read_text(encoding="utf-8")
        for m in markers:
            # allowed only inside an expected_subscale_level_scores? never.
            assert f'"{m}":' not in text, f"{m} appears as an emitted score in {path.name}"


# --- 6: no network / no api key / no real model client in sources -------------


def test_no_network_or_api_or_model_client() -> None:
    # Real client / network usage patterns (not bare substrings, so honest
    # NEGATIVE declarations like `no_api_key: true` never trip the guard).
    banned_patterns = (
        re.compile(r"\bimport\s+(openai|anthropic|httpx|socket|requests)\b", re.IGNORECASE),
        re.compile(r"\bfrom\s+(openai|anthropic|httpx|urllib)\b", re.IGNORECASE),
        re.compile(r"requests\.(get|post)\s*\(", re.IGNORECASE),
        re.compile(r"urllib\.request", re.IGNORECASE),
        re.compile(r"chat\.completions", re.IGNORECASE),
        re.compile(r"\bdeepseek\b", re.IGNORECASE),
        re.compile(r"api_key\s*[:=]\s*[\"'][^\"'\s]", re.IGNORECASE),  # assigned a real value
    )
    key_literal = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)
    for path in PKG_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".jsonl", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        for pat in banned_patterns:
            assert not pat.search(text), f"banned pattern {pat.pattern!r} in {path.name}"
        assert not key_literal.search(text), f"API key literal in {path.name}"


# --- 7: package does not read R2/R3 assets ------------------------------------


def test_no_r2_r3_asset_reads() -> None:
    forbidden_refs = (
        "pa_wu_p1_prep", "provisional", "zh-cn", "zh_cn",
        "adaptation_candidates", "ai_human", "ai/human",
    )
    for path in PKG_DIR.rglob("*.py"):
        low = path.read_text(encoding="utf-8").lower()
        for ref in forbidden_refs:
            assert ref not in low, f"R2/R3 asset reference '{ref}' in {path.name}"


# --- 8: prototype never labeled a formal positive control ---------------------


def test_prototype_not_formal_positive_control(validator, run_mock) -> None:
    validator.check_positive_control_levels()  # raises on violation
    cases = run_mock.load_input_cases()
    proto = [
        c for c in cases
        if str(c.get("positive_control_provenance", {}).get("level"))
        == "source_adapted_prototype"
    ]
    assert proto, "expected at least one source_adapted_prototype case"
    for c in proto:
        prov = c["positive_control_provenance"]
        assert prov["is_prototype"] is True
        assert prov["is_full_script"] is False
    # The forbidden label may appear ONLY inside a "forbidden" context (e.g. a
    # positive_control_levels_forbidden list or a doc line naming it as banned),
    # never as an actually-assigned level. Checked at file scope.
    for path in PKG_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".jsonl", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        if "formal_calibrated_positive_control" in text:
            low = text.lower()
            assert "forbidden" in low or "禁止" in text, (
                f"formal_calibrated_positive_control used unqualified in {path.name}"
            )
            # and it must never be assigned as an active positive_control_level
            assert '"level": "formal_calibrated_positive_control"' not in text
            assert "level: formal_calibrated_positive_control" not in text


# --- 9: full package validation entrypoint passes -----------------------------


def test_validate_package_passes(validator) -> None:
    report = validator.validate_package()
    assert report["deterministic_run_hash"]
    assert report["package_manifest"]["package_status"] == "mock_only"
