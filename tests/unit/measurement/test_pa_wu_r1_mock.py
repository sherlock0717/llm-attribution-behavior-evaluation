"""Structural + behavioral tests for the PA-Wu R1 MOCK execution package.

NO real model, NO network, NO API key. All scoring is delegated to the P0
engine (freewill_attribution.measurement.pa_wu_p0); the item-wording
administration_hash is computed by the P0 engine (never re-implemented). The
package separates INPUT-case validation from OUTPUT-fixture validation and uses
expected_scored_outputs.jsonl as the SINGLE static oracle (this test does NOT
hard-code a second failure-code map).

Covered (task section 8):
 1. every legal input case is accepted
 2. every bad input case is rejected (real chain, not label skip)
 3. input results are separated from output results
 4. each output case_id exists and points to a valid input case
 5. form/order match the input case
 6. missing response_language is rejected
 7. missing response_identity is rejected
 8. PA13/PA8/PA5 actually scored
 9. Wu four sub-scales actually scored
10. selected_item_ids exactly equal P0 order
11. P0 administration_hash determinism + sensitivity
12. expected_scored_outputs one-to-one full comparison
13. manifest counts and hash consistent
14. no forbidden totals
15. no network / no API key / no real model client
16. no R2/R3 asset reads
17. prototype never labeled a formal positive control
"""

from __future__ import annotations

import importlib.util
import re
import shutil

import pytest
import yaml

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


# --- 1 & 2: input-case validation (real chain) -------------------------------


def test_legal_input_cases_accepted(run_mock, contract) -> None:
    cases = run_mock.load_input_cases()
    results = {r["case_id"]: r for r in run_mock.validate_input_cases(contract, cases)}
    good = [c for c in cases if "_bad_case" not in c]
    assert len(good) == 4
    for c in good:
        r = results[c["case_id"]]
        assert r["accepted"] is True, (c["case_id"], r["validation_errors"])
        assert r["failure_codes"] == []
        assert r["administration_hash"]  # a P0 hash was computed


def test_bad_input_cases_rejected_with_real_codes(run_mock, contract) -> None:
    cases = run_mock.load_input_cases()
    results = {r["case_id"]: r for r in run_mock.validate_input_cases(contract, cases)}
    expected = {
        "r1_bad_missing_field": "missing_required_field",
        "r1_bad_forbidden_total": "forbidden_total",
        "r1_bad_wrong_language": "wrong_language",
        "r1_bad_wrong_identity": "wrong_identity",
    }
    for cid, code in expected.items():
        r = results[cid]
        assert r["accepted"] is False, cid
        assert code in r["failure_codes"], (cid, r["failure_codes"])


# --- 3: input vs output separation -------------------------------------------


def test_input_and_output_results_separated(report) -> None:
    assert "input_case_validation_results" in report
    assert "output_validation_results" in report
    assert "case_validation_results" not in report  # old conflated name is gone
    assert len(report["input_case_validation_results"]) == 8
    assert len(report["output_validation_results"]) == 14


# --- 4 & 5: outputs reference valid inputs with matching form/order ----------


def test_outputs_reference_valid_inputs(run_mock, report) -> None:
    cases = {c["case_id"]: c for c in run_mock.load_input_cases()}
    valid_ids = {r["case_id"] for r in report["input_case_validation_results"] if r["accepted"]}
    for output in run_mock.load_model_outputs():
        cid = str(output["case_id"])
        assert cid in cases, f"{output['output_id']} references missing case {cid}"
        assert cid in valid_ids, f"{output['output_id']} references INVALID case {cid}"
        case = cases[cid]
        assert str(output["form_id"]) == str(case["form_id"])
        assert str(output["item_order_id"]) == str(case["item_order_id"])


def _valid_input_case_map(run_mock, contract):
    cases = run_mock.load_input_cases()
    results = run_mock.validate_input_cases(contract, cases)
    accepted = {r["case_id"] for r in results if r["accepted"]}
    return {str(c["case_id"]): c for c in cases if str(c["case_id"]) in accepted}


def test_output_wrong_form_rejected(run_mock, contract) -> None:
    vmap = _valid_input_case_map(run_mock, contract)
    ref = vmap["r1_neutral_02"]  # wu19_only / wu_only
    bad = dict(ref)
    bad.update({
        "output_id": "_t_wrong_form", "response_language": "en",
        "response_identity": "machine", "form_id": "pa13_wu19_combined",
        "item_order_id": "wu_only", "raw_item_ratings": [],
    })
    res = run_mock.classify_output(contract, bad, vmap)
    assert res["accepted"] is False
    assert res["failure_code"] == "output_contract_mismatch"


def test_output_wrong_order_rejected(run_mock, contract) -> None:
    vmap = _valid_input_case_map(run_mock, contract)
    ref = vmap["r1_neutral_02"]
    bad = dict(ref)
    bad.update({
        "output_id": "_t_wrong_order", "response_language": "en",
        "response_identity": "machine", "form_id": "wu19_only",
        "item_order_id": "pa_first", "raw_item_ratings": [],
    })
    res = run_mock.classify_output(contract, bad, vmap)
    assert res["accepted"] is False
    assert res["failure_code"] == "output_contract_mismatch"


def test_validate_package_covers_linkage(validator, contract) -> None:
    # the enforcement path is exercised by the validate_package call chain
    validator.check_output_contract_linkage_enforced(contract)  # raises on failure


# --- 6 & 7: missing response language / identity rejected --------------------


def test_missing_response_language_rejected(report) -> None:
    assert report["failure_codes"]["out_missing_response_language"] == "missing_required_field"


def test_missing_response_identity_rejected(report) -> None:
    assert report["failure_codes"]["out_missing_response_identity"] == "missing_required_field"


# --- 8 & 9: PA and Wu sub-scores actually derived via P0 members -------------


def test_pa_and_wu_subscores_derived(report, contract) -> None:
    combined = report["subscale_level_scores"]["out_complete_valid_combined"]
    assert combined == {
        "PA13": 3.0, "PA8": 3.0, "PA5": 3.0,
        "IN4": 4.0, "GO4": 4.0, "MSI6": 3.0, "IC5": 4.0,
    }
    # PA13/8/5 must be derived over the ACTUAL P0 members (not just counts):
    item_scores = report["item_level_scores"]["out_complete_valid_combined"]
    for version, expected_mean in (("pa13", 3.0), ("pa8", 3.0), ("pa5", 3.0)):
        members = contract.pa_version_members(version)
        assert all(m in item_scores for m in members)
        mean = sum(item_scores[m] for m in members) / len(members)
        assert mean == expected_mean
    for construct, expected_mean in (
        ("perceived_machine_independence", 4.0),
        ("perceived_machine_goal_orientation", 4.0),
        ("mental_state_inference", 3.0),
        ("influential_capacity_judgment", 4.0),
    ):
        members = contract.wu_construct_members(construct)
        mean = sum(item_scores[m] for m in members) / len(members)
        assert mean == expected_mean


# --- 10: selected_item_ids exactly equal P0 order ----------------------------


def test_selected_item_ids_equal_p0_order(run_mock, contract) -> None:
    for case in run_mock.load_input_cases():
        if "_bad_case" in case:
            continue
        expected = p0.build_form_item_ids(
            contract, str(case["form_id"]), str(case["item_order_id"])
        )
        assert [str(x) for x in case["selected_item_ids"]] == expected


# --- 11: P0 administration_hash determinism + sensitivity --------------------


def test_administration_hash_reused_from_p0(run_mock, contract, tmp_path) -> None:
    case = next(c for c in run_mock.load_input_cases() if c["case_id"] == "r1_neutral_01")

    # (a) deterministic reproduction against the P0 engine directly
    material = {
        "scenario_id": case["scenario_id"],
        "condition_id": case["condition_id"],
        "identity": case["target_identity"],
        "choice_direction": case["choice_direction"],
    }
    direct = p0.administration_hash(
        contract, case["form_id"], case["item_order_id"], material, 0
    )
    via_pkg = run_mock.administration_hash_for_case(contract, case)
    assert direct == via_pkg
    assert via_pkg == run_mock.administration_hash_for_case(contract, case)  # stable

    # (b) changing item wording changes the P0 hash (mutate a temp contract)
    dst = tmp_path / "pa_wu_p0"
    shutil.copytree(p0.CANDIDATE_DIR, dst)
    pa_path = dst / "items_pa_2024.yaml"
    data = yaml.safe_load(pa_path.read_text(encoding="utf-8"))
    data["items"][0]["text"] = data["items"][0]["text"] + " (reworded)"
    pa_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    mutated = p0.load_contract(dst)
    mutated_hash = run_mock.administration_hash_for_case(mutated, case)
    assert mutated_hash != via_pkg, "P0 hash must change when item wording changes"


def test_administration_hash_sensitive_to_order(contract) -> None:
    # combined form has two legal orders (pa_first / wu_first); order changes hash.
    material = {
        "scenario_id": "neutral_help_directions", "condition_id": "neutral",
        "identity": "machine", "choice_direction": "none",
    }
    h_pa_first = p0.administration_hash(contract, "pa13_wu19_combined", "pa_first", material, 0)
    h_wu_first = p0.administration_hash(contract, "pa13_wu19_combined", "wu_first", material, 0)
    assert h_pa_first != h_wu_first, "P0 hash must change when item order changes"


def test_administration_hash_sensitive_to_scale(run_mock, tmp_path) -> None:
    case = next(c for c in run_mock.load_input_cases() if c["case_id"] == "r1_neutral_01")
    base = run_mock.administration_hash_for_case(p0.load_contract(), case)

    dst = tmp_path / "pa_wu_p0"
    shutil.copytree(p0.CANDIDATE_DIR, dst)
    pa_path = dst / "items_pa_2024.yaml"
    data = yaml.safe_load(pa_path.read_text(encoding="utf-8"))
    data["response_scale"]["max"] = int(data["response_scale"]["max"]) + 1  # 5 -> 6
    pa_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    mutated = p0.load_contract(dst)
    mutated_hash = run_mock.administration_hash_for_case(mutated, case)
    assert mutated_hash != base, "P0 hash must change when a response scale boundary changes"


def test_package_has_no_second_wording_hash() -> None:
    # The package must not re-implement an item-wording hash: run_mock only calls
    # p0.administration_hash and never builds its own sha over item texts.
    src = (PKG_DIR / "run_mock.py").read_text(encoding="utf-8")
    assert "p0.administration_hash(" in src
    # its only hashlib use is the run-report hash over the assembled report,
    # never over item texts/ids directly.
    assert "_item_text_map" not in src
    assert "left_anchor_text" not in src


# --- 12: expected_scored_outputs is the SINGLE oracle ------------------------


def test_oracle_one_to_one_full_comparison(validator, report) -> None:
    validator.check_oracle_one_to_one(report)  # raises on any mismatch
    cov = report["oracle_coverage"]
    assert cov["missing_from_expected"] == []
    assert cov["extra_in_expected"] == []
    for row in report["expected_vs_actual_comparison"]:
        assert row["outcome_match"]
        assert row["case_id_match"]
        assert row["failure_code_match"]
        assert row["subscale_match"]
        assert row["forbidden_total_match"]
        # STRICT: expected_outcome is exactly accept/reject (no reject_or_warn)
        assert row["expected_outcome"] in ("accept", "reject")


def test_model_outputs_carry_no_answers(run_mock) -> None:
    # inputs/outputs must not embed their own answers (answers live in the oracle)
    for output in run_mock.load_model_outputs():
        assert "expected_outcome" not in output
        assert "failure_code_expected" not in output


def test_duplicate_model_output_id_rejected(run_mock) -> None:
    rows = [{"output_id": "dup"}, {"output_id": "dup"}]
    with pytest.raises(run_mock.MockFixtureError):
        run_mock._assert_unique_nonempty_ids(rows, "mock_model_outputs.jsonl")


def test_duplicate_expected_output_id_rejected(run_mock) -> None:
    rows = [{"output_id": "e1"}, {"output_id": "e1"}]
    with pytest.raises(run_mock.MockFixtureError):
        run_mock._assert_unique_nonempty_ids(rows, "expected_scored_outputs.jsonl")


def test_empty_output_id_rejected(run_mock) -> None:
    with pytest.raises(run_mock.MockFixtureError):
        run_mock._assert_unique_nonempty_ids([{"output_id": ""}], "src")
    with pytest.raises(run_mock.MockFixtureError):
        run_mock._assert_unique_nonempty_ids([{}], "src")


def test_real_output_and_oracle_ids_unique(run_mock) -> None:
    outs = run_mock.load_model_outputs()  # raises if duplicate/empty
    oracle = run_mock.load_expected_scored_outputs()  # raises if duplicate/empty
    out_ids = [str(o["output_id"]) for o in outs]
    assert len(out_ids) == len(set(out_ids))
    assert len(oracle) == len(out_ids)


def _write_jsonl(path, rows) -> None:
    import json

    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_load_model_outputs_rejects_duplicate_id(run_mock, tmp_path, monkeypatch) -> None:
    # Exercise the FORMAL loader path (not just the helper): a duplicate
    # output_id in mock_model_outputs.jsonl must raise MockFixtureError.
    monkeypatch.setattr(run_mock, "PACKAGE_DIR", tmp_path)
    _write_jsonl(
        tmp_path / "mock_model_outputs.jsonl",
        [{"output_id": "dup", "output_kind": "x"}, {"output_id": "dup", "output_kind": "y"}],
    )
    with pytest.raises(run_mock.MockFixtureError):
        run_mock.load_model_outputs()


def test_load_model_outputs_rejects_empty_id(run_mock, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(run_mock, "PACKAGE_DIR", tmp_path)
    _write_jsonl(
        tmp_path / "mock_model_outputs.jsonl",
        [{"output_id": "", "output_kind": "x"}],
    )
    with pytest.raises(run_mock.MockFixtureError):
        run_mock.load_model_outputs()


def test_load_expected_scored_outputs_rejects_duplicate_id(
    run_mock, tmp_path, monkeypatch
) -> None:
    # Exercise the FORMAL oracle loader path: a duplicate output_id in
    # expected_scored_outputs.jsonl must raise (no silent dict overwrite).
    monkeypatch.setattr(run_mock, "PACKAGE_DIR", tmp_path)
    _write_jsonl(
        tmp_path / "expected_scored_outputs.jsonl",
        [
            {"output_id": "e1", "expected_outcome": "reject"},
            {"output_id": "e1", "expected_outcome": "accept"},
        ],
    )
    with pytest.raises(run_mock.MockFixtureError):
        run_mock.load_expected_scored_outputs()


def test_load_expected_scored_outputs_rejects_empty_id(
    run_mock, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(run_mock, "PACKAGE_DIR", tmp_path)
    _write_jsonl(
        tmp_path / "expected_scored_outputs.jsonl",
        [{"output_id": "", "expected_outcome": "reject"}],
    )
    with pytest.raises(run_mock.MockFixtureError):
        run_mock.load_expected_scored_outputs()


# --- 13: manifest counts + hash consistency ----------------------------------


def test_manifest_checked_and_consistent(validator, report) -> None:
    validator.check_manifest(report)  # raises on any mismatch
    m = validator.load_manifest()
    assert m["input_cases"]["total"] == 8
    assert m["model_output_fixtures"]["total"] == 14
    assert str(m["deterministic_run_hash_reference"]) == report["deterministic_run_hash"]


# --- 14: no forbidden totals -------------------------------------------------


def test_no_forbidden_totals(report) -> None:
    for scores in report["subscale_level_scores"].values():
        for forbidden in p0.FORBIDDEN_SCORE_IDS:
            assert forbidden not in scores
    assert report["failure_codes"]["out_forbidden_total"] == "forbidden_total"


# --- 15: no network / no api key / no real model client ----------------------


def test_no_network_or_api_or_model_client() -> None:
    banned_patterns = (
        re.compile(r"\bimport\s+(openai|anthropic|httpx|socket|requests)\b", re.IGNORECASE),
        re.compile(r"\bfrom\s+(openai|anthropic|httpx|urllib)\b", re.IGNORECASE),
        re.compile(r"requests\.(get|post)\s*\(", re.IGNORECASE),
        re.compile(r"urllib\.request", re.IGNORECASE),
        re.compile(r"chat\.completions", re.IGNORECASE),
        re.compile(r"\bdeepseek\b", re.IGNORECASE),
        re.compile(r"api_key\s*[:=]\s*[\"'][^\"'\s]", re.IGNORECASE),
    )
    key_literal = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)
    for path in PKG_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".jsonl", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        for pat in banned_patterns:
            assert not pat.search(text), f"banned pattern {pat.pattern!r} in {path.name}"
        assert not key_literal.search(text), f"API key literal in {path.name}"


# --- 16: no R2/R3 asset reads ------------------------------------------------


def test_no_r2_r3_asset_reads() -> None:
    forbidden_refs = (
        "pa_wu_p1_prep", "provisional", "zh-cn", "zh_cn",
        "adaptation_candidates", "ai_human", "ai/human",
    )
    for path in PKG_DIR.rglob("*.py"):
        low = path.read_text(encoding="utf-8").lower()
        for ref in forbidden_refs:
            assert ref not in low, f"R2/R3 asset reference '{ref}' in {path.name}"


# --- 17: prototype never labeled a formal positive control -------------------


def test_prototype_not_formal_positive_control(validator, run_mock) -> None:
    validator.check_positive_control_levels()  # raises on violation
    proto = [
        c for c in run_mock.load_input_cases()
        if str(c.get("positive_control_provenance", {}).get("level"))
        == "source_adapted_prototype"
    ]
    assert proto
    for c in proto:
        prov = c["positive_control_provenance"]
        assert prov["is_prototype"] is True
        assert prov["is_full_script"] is False


# --- full validate entrypoint -------------------------------------------------


def test_validate_package_passes(validator) -> None:
    report = validator.validate_package()
    assert report["deterministic_run_hash"]
    assert report["package_manifest"]["package_status"] == "mock_only"
