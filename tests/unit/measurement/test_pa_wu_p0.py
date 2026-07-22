"""Tests for the PA-Wu P0 candidate measurement engine (mock-only).

Covers: contract loading/validation, PA13/8/5 membership, Wu construct mapping,
forms/order, dynamic source_instrument_ids, strict response validation (incl.
out-of-range -> error), the four mock smoke runs, full record fields, derived
scoring, forbidden totals, is_mock invariant + validate_record, administration
hash sensitivity, request accounting, and corrupted-contract rejection fixtures.
"""

from __future__ import annotations

import pytest
import yaml

from freewill_attribution.measurement import pa_wu_p0 as p0


@pytest.fixture(scope="module")
def contract() -> p0.P0Contract:
    return p0.load_contract()


# ---------------------------------------------------------------------------
# corrupted-contract fixtures (build a temp candidate dir and mutate it)
# ---------------------------------------------------------------------------


def _materialize(tmp_path):
    """Copy the real candidate contract into a temp dir; return that dir."""
    import shutil

    dst = tmp_path / "pa_wu_p0"
    shutil.copytree(p0.CANDIDATE_DIR, dst)
    return dst


def _load_yaml(path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _dump_yaml(path, data):
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True)


# ---------------------------------------------------------------------------
# contract structure (happy path)
# ---------------------------------------------------------------------------


def test_pa_has_13_scored_items(contract: p0.P0Contract) -> None:
    assert len(contract.pa_item_ids) == 13
    assert len(set(contract.pa_item_ids)) == 13


def test_pa_versions_are_subsets_of_pa13(contract: p0.P0Contract) -> None:
    pa13 = set(contract.pa_version_members("pa13"))
    assert pa13 == set(contract.pa_item_ids)
    assert len(contract.pa_version_members("pa8")) == 8
    assert len(contract.pa_version_members("pa5")) == 5


def test_wu_construct_mapping(contract: p0.P0Contract) -> None:
    assert len(contract.wu_item_ids) == 19
    assert len(contract.wu_construct_members("perceived_machine_independence")) == 4
    assert len(contract.wu_construct_members("perceived_machine_goal_orientation")) == 4
    assert len(contract.wu_construct_members("mental_state_inference")) == 6
    assert len(contract.wu_construct_members("influential_capacity_judgment")) == 5


# --- forms & dynamic source instruments -------------------------------------


def test_form_f1_32_items_both_orders(contract: p0.P0Contract) -> None:
    pa_first = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    wu_first = p0.build_form_item_ids(contract, "pa13_wu19_combined", "wu_first")
    assert len(pa_first) == 32 and len(wu_first) == 32
    assert set(pa_first) == set(wu_first) and pa_first != wu_first


def test_source_instruments_per_form(contract: p0.P0Contract) -> None:
    assert p0.form_source_instruments(contract, "pa13_only") == ["pa_2024"]
    assert p0.form_source_instruments(contract, "wu19_only") == ["wu_shen_2026"]
    assert p0.form_source_instruments(contract, "pa13_wu19_combined") == [
        "pa_2024",
        "wu_shen_2026",
    ]


# --- strict response validation ---------------------------------------------


def _valid_ratings(contract, form, order):
    ranges = p0._rating_ranges(contract)
    return [{"item_id": i, "rating": ranges[i][0]} for i in p0.build_form_item_ids(contract, form, order)]


def test_full_response_ok(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    assert p0.validate_response(contract, "pa13_wu19_combined", "pa_first", r) == []


def test_missing_item_warns(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")[:-1]
    warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", r)
    assert any("missing_items" in w for w in warnings)


def test_duplicate_item_rejected(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", [r[0], *r])


def test_unknown_item_rejected(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    r[0] = {"item_id": "bogus", "rating": 1}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", r)


def test_out_of_range_rejected(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    r[0] = {"item_id": r[0]["item_id"], "rating": 999}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", r)


def test_non_numeric_rejected(contract: p0.P0Contract) -> None:
    r = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    r[0] = {"item_id": r[0]["item_id"], "rating": "x"}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", r)


# --- scoring ----------------------------------------------------------------


def test_derive_scores_full(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    result = p0.derive_scores(contract, ratings)
    for s in ("PA13", "PA8", "PA5", "IN4", "GO4", "MSI6", "IC5"):
        assert s in result.derived_scores
    assert result.scoring_warnings == []


def test_missing_member_not_silently_scored(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    ratings.pop(contract.pa_version_members("pa13")[0])
    result = p0.derive_scores(contract, ratings)
    assert "PA13" not in result.derived_scores
    assert any("PA13" in w for w in result.scoring_warnings)


def test_out_of_range_blocked_from_derivation(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    ratings[contract.pa_version_members("pa13")[0]] = 999
    with pytest.raises(p0.P0ContractError):
        p0.derive_scores(contract, ratings)


def test_no_forbidden_totals(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    result = p0.derive_scores(contract, {i: ranges[i][0] + 1 for i in ids})
    for forbidden in p0.FORBIDDEN_SCORE_IDS:
        assert forbidden not in result.derived_scores


# --- mock smoke A/B/C/D + record fields -------------------------------------

_MATERIALS = [
    {"scenario_id": "risk_project_choice", "condition_id": "D0_U0", "identity": "AI 决策者",
     "choice_direction": "choose_option_1"},
    {"scenario_id": "relationship_honesty", "condition_id": "D2_U3", "identity": "人类决策者",
     "choice_direction": "choose_option_1"},
]


def test_smoke_a_record_has_all_fields(contract: p0.P0Contract) -> None:
    records = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "pa_first", repeats=1)
    assert len(records) == 2
    for rec in records:
        assert rec["is_mock"] is True
        assert len(rec["raw_item_ratings"]) == 32
        for key in ("raw_item_ratings", "derived_scores", "validation_warnings", "scoring_warnings"):
            assert key in rec
        assert rec["derived_scores"]  # normal path computes scores
        p0.validate_record(rec)


def test_smoke_b_wu_first_deterministic(contract: p0.P0Contract) -> None:
    r1 = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "wu_first", repeats=1)
    r2 = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "wu_first", repeats=1)
    assert r1 == r2
    assert r1[0]["item_order_id"] == "wu_first"


def test_smoke_c_pa_only_wu_only(contract: p0.P0Contract) -> None:
    pa = p0.mock_run(contract, _MATERIALS, "pa13_only", "pa_only", repeats=1)
    wu = p0.mock_run(contract, _MATERIALS, "wu19_only", "wu_only", repeats=1)
    assert all(len(r["raw_item_ratings"]) == 13 for r in pa)
    assert all(len(r["raw_item_ratings"]) == 19 for r in wu)
    assert pa[0]["source_instrument_ids"] == ["pa_2024"]
    assert wu[0]["source_instrument_ids"] == ["wu_shen_2026"]


@pytest.mark.parametrize("fault", ["missing_item", "duplicate_item", "out_of_range", "unknown_item"])
def test_smoke_d_error_fixtures(contract: p0.P0Contract, fault: str) -> None:
    rec = p0.mock_run(
        contract, _MATERIALS[:1], "pa13_wu19_combined", "pa_first", repeats=1, inject_fault=fault
    )[0]
    entries = [{"item_id": e["item_id"], "rating": e["rating"]} for e in rec["raw_item_ratings"]]
    if fault == "missing_item":
        warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", entries)
        assert any("missing_items" in w for w in warnings)
    else:  # duplicate / out_of_range / unknown -> raise
        with pytest.raises(p0.P0ContractError):
            p0.validate_response(contract, "pa13_wu19_combined", "pa_first", entries)


def test_is_mock_always_true(contract: p0.P0Contract) -> None:
    records = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "pa_first", repeats=2)
    assert all(rec["is_mock"] is True for rec in records)


def test_validate_record_rejects_real(contract: p0.P0Contract) -> None:
    rec = p0.mock_run(contract, _MATERIALS[:1], "pa13_wu19_combined", "pa_first")[0]
    rec["is_mock"] = False
    with pytest.raises(p0.P0ContractError):
        p0.validate_record(rec)


# --- administration hash sensitivity ----------------------------------------


def test_administration_hash_changes_with_order(contract: p0.P0Contract) -> None:
    m = _MATERIALS[0]
    h_pa = p0.administration_hash(contract, "pa13_wu19_combined", "pa_first", m, 0)
    h_wu = p0.administration_hash(contract, "pa13_wu19_combined", "wu_first", m, 0)
    assert h_pa != h_wu


def test_administration_hash_changes_with_item_text(tmp_path, contract: p0.P0Contract) -> None:
    m = _MATERIALS[0]
    base = p0.administration_hash(contract, "pa13_only", "pa_only", m, 0)
    dst = _materialize(tmp_path)
    pa = _load_yaml(dst / "items_pa_2024.yaml")
    pa["items"][0]["text"] = pa["items"][0]["text"] + " (edited)"
    _dump_yaml(dst / "items_pa_2024.yaml", pa)
    mutated = p0.load_contract(dst)
    changed = p0.administration_hash(mutated, "pa13_only", "pa_only", m, 0)
    assert base != changed


# --- request / item-rating accounting ---------------------------------------


def test_accounting_p1_min() -> None:
    acc = p0.account_requests(24, 32, 3, 1)
    assert acc["api_requests"] == 72 and acc["item_ratings"] == 2304


def test_accounting_p1_context() -> None:
    f1 = p0.account_requests(24, 32, 3, 1)
    pa = p0.account_requests(8, 13, 3, 1)
    wu = p0.account_requests(8, 19, 3, 1)
    assert f1["api_requests"] + pa["api_requests"] + wu["api_requests"] == 120
    assert f1["item_ratings"] + pa["item_ratings"] + wu["item_ratings"] == 3072


def test_accounting_p1_order() -> None:
    base = p0.account_requests(24, 32, 3, 1)
    extra = p0.account_requests(8, 32, 3, 1)
    assert base["api_requests"] + extra["api_requests"] == 96


# --- assert_administrable (placeholder text blocks administration) ----------


def test_placeholder_blocks_administration(contract: p0.P0Contract) -> None:
    # Wu items are pending_source_verbatim in this environment -> not administrable.
    with pytest.raises(p0.P0ContractError):
        p0.assert_administrable(contract)


# ---------------------------------------------------------------------------
# corrupted-contract rejection fixtures (1-8, plus source/version mismatches)
# ---------------------------------------------------------------------------


def test_corrupt_pa8_not_subset(tmp_path) -> None:
    dst = _materialize(tmp_path)
    pa = _load_yaml(dst / "items_pa_2024.yaml")
    pa["versions"]["pa8"][0] = "not_a_pa13_member"
    _dump_yaml(dst / "items_pa_2024.yaml", pa)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_pa5_wrong_count(tmp_path) -> None:
    dst = _materialize(tmp_path)
    pa = _load_yaml(dst / "items_pa_2024.yaml")
    pa["versions"]["pa5"] = pa["versions"]["pa5"][:-1]
    _dump_yaml(dst / "items_pa_2024.yaml", pa)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_wu_subscale_missing_member(tmp_path) -> None:
    dst = _materialize(tmp_path)
    wu = _load_yaml(dst / "items_wu_shen_2026.yaml")
    wu["constructs"]["influential_capacity_judgment"]["items"] = ["wu_ic1", "wu_ic3"]
    _dump_yaml(dst / "items_wu_shen_2026.yaml", wu)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_wu_construct_duplicate_coverage(tmp_path) -> None:
    dst = _materialize(tmp_path)
    wu = _load_yaml(dst / "items_wu_shen_2026.yaml")
    # Make goal-orientation duplicate an independence item -> coverage mismatch.
    wu["constructs"]["perceived_machine_goal_orientation"]["items"] = [
        "wu_in1a", "wu_go2a", "wu_go3b", "wu_go4a",
    ]
    _dump_yaml(dst / "items_wu_shen_2026.yaml", wu)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_form_item_count(tmp_path) -> None:
    dst = _materialize(tmp_path)
    forms = _load_yaml(dst / "forms.yaml")
    forms["forms"][0]["item_count"] = 99
    _dump_yaml(dst / "forms.yaml", forms)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_form_instruments_vs_order(tmp_path) -> None:
    dst = _materialize(tmp_path)
    forms = _load_yaml(dst / "forms.yaml")
    # F2 declares only pa_2024 but order sequence lists wu_shen_2026.
    for form in forms["forms"]:
        if form["form_id"] == "pa13_only":
            form["orders"][0]["sequence"] = ["wu_shen_2026"]
    _dump_yaml(dst / "forms.yaml", forms)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_scoring_version_mismatch(tmp_path) -> None:
    dst = _materialize(tmp_path)
    scoring = _load_yaml(dst / "scoring.yaml")
    scoring["scoring_version"] = "different.vX"
    _dump_yaml(dst / "scoring.yaml", scoring)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_corrupt_empty_item_text(tmp_path) -> None:
    dst = _materialize(tmp_path)
    pa = _load_yaml(dst / "items_pa_2024.yaml")
    pa["items"][0]["text"] = "   "
    _dump_yaml(dst / "items_pa_2024.yaml", pa)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_forbidden_total_in_scoring_rejected(tmp_path) -> None:
    dst = _materialize(tmp_path)
    scoring = _load_yaml(dst / "scoring.yaml")
    scoring["derived_scores"].append(
        {"score_id": "WU19_TOTAL", "method": "mean", "source_instrument": "wu_shen_2026",
         "construct": "mental_state_inference"}
    )
    _dump_yaml(dst / "scoring.yaml", scoring)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)


def test_manifest_forms_mismatch_rejected(tmp_path) -> None:
    dst = _materialize(tmp_path)
    manifest = _load_yaml(dst / "manifest.yaml")
    manifest["forms"] = [f for f in manifest["forms"] if f["form_id"] != "wu19_only"]
    _dump_yaml(dst / "manifest.yaml", manifest)
    with pytest.raises(p0.P0ContractError):
        p0.load_contract(dst)
