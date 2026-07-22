"""Tests for the PA-Wu P0 candidate measurement engine (mock-only).

Covers: contract loading/validation, PA13/8/5 membership, Wu construct mapping,
forms and item order, strict response validation (13 fault categories), the four
mock smoke runs, derived scoring, forbidden totals, is_mock invariant, and the
request/item-rating accounting (P1-Min / P1-Context / P1-Order).
"""

from __future__ import annotations

import pytest

from freewill_attribution.measurement import pa_wu_p0 as p0


@pytest.fixture(scope="module")
def contract() -> p0.P0Contract:
    return p0.load_contract()


# --- contract structure -----------------------------------------------------


def test_pa_has_13_scored_items(contract: p0.P0Contract) -> None:
    assert len(contract.pa_item_ids) == 13
    assert len(set(contract.pa_item_ids)) == 13


def test_pa_versions_are_subsets_of_pa13(contract: p0.P0Contract) -> None:
    pa13 = set(contract.pa_version_members("pa13"))
    assert pa13 == set(contract.pa_item_ids)
    assert len(contract.pa_version_members("pa8")) == 8
    assert len(contract.pa_version_members("pa5")) == 5
    assert set(contract.pa_version_members("pa8")).issubset(pa13)
    assert set(contract.pa_version_members("pa5")).issubset(pa13)


def test_pa_attention_check_not_in_items(contract: p0.P0Contract) -> None:
    # Only 13 scored items; no "has a face" attention-check item present.
    joined = " ".join(contract.pa_item_ids)
    assert "attention" not in joined
    assert "has_a_face" not in joined


def test_wu_has_19_final_items_and_construct_mapping(contract: p0.P0Contract) -> None:
    assert len(contract.wu_item_ids) == 19
    assert len(contract.wu_construct_members("perceived_machine_independence")) == 4
    assert len(contract.wu_construct_members("perceived_machine_goal_orientation")) == 4
    assert len(contract.wu_construct_members("mental_state_inference")) == 6
    assert len(contract.wu_construct_members("influential_capacity_judgment")) == 5


# --- forms & order ----------------------------------------------------------


def test_form_f1_has_32_items_both_orders(contract: p0.P0Contract) -> None:
    pa_first = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    wu_first = p0.build_form_item_ids(contract, "pa13_wu19_combined", "wu_first")
    assert len(pa_first) == 32
    assert len(wu_first) == 32
    # Same items, different order.
    assert set(pa_first) == set(wu_first)
    assert pa_first != wu_first
    assert pa_first[0].startswith("pa_")
    assert wu_first[0].startswith("wu_")


def test_forms_f2_f3_sizes(contract: p0.P0Contract) -> None:
    assert len(p0.build_form_item_ids(contract, "pa13_only", "pa_only")) == 13
    assert len(p0.build_form_item_ids(contract, "wu19_only", "wu_only")) == 19


def test_unknown_order_rejected(contract: p0.P0Contract) -> None:
    with pytest.raises(p0.P0ContractError):
        p0.build_form_item_ids(contract, "pa13_wu19_combined", "nope")


# --- strict response validation (fault categories) --------------------------


def _valid_ratings(contract: p0.P0Contract, form: str, order: str) -> list[dict]:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, form, order)
    return [{"item_id": i, "rating": ranges[i][0]} for i in ids]


def test_full_32_response_ok(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)
    assert warnings == []


def test_missing_item_warns(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")[:-1]
    warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)
    assert any("missing_items" in w for w in warnings)


def test_duplicate_item_rejected(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    ratings = [ratings[0], *ratings]
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)


def test_unknown_item_rejected(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    ratings[0] = {"item_id": "bogus", "rating": 1}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)


def test_out_of_range_warns(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    ratings[0] = {"item_id": ratings[0]["item_id"], "rating": 999}
    warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)
    assert any("out_of_range" in w for w in warnings)


def test_non_numeric_rating_rejected(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    ratings[0] = {"item_id": ratings[0]["item_id"], "rating": "high"}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)


def test_boolean_rating_rejected(contract: p0.P0Contract) -> None:
    ratings = _valid_ratings(contract, "pa13_wu19_combined", "pa_first")
    ratings[0] = {"item_id": ratings[0]["item_id"], "rating": True}
    with pytest.raises(p0.P0ContractError):
        p0.validate_response(contract, "pa13_wu19_combined", "pa_first", ratings)


# --- scoring / derivation ---------------------------------------------------


def test_derive_scores_full(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    result = p0.derive_scores(contract, ratings)
    for score_id in ("PA13", "PA8", "PA5", "IN4", "GO4", "MSI6", "IC5"):
        assert score_id in result.derived_scores
    assert result.scoring_warnings == []


def test_missing_member_not_silently_scored(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    # Drop one PA13 member -> PA13 must NOT be computed.
    dropped = contract.pa_version_members("pa13")[0]
    ratings.pop(dropped)
    result = p0.derive_scores(contract, ratings)
    assert "PA13" not in result.derived_scores
    assert any("PA13" in w for w in result.scoring_warnings)


def test_no_wu19_or_combined_total(contract: p0.P0Contract) -> None:
    ranges = p0._rating_ranges(contract)
    ids = p0.build_form_item_ids(contract, "pa13_wu19_combined", "pa_first")
    ratings = {i: ranges[i][0] + 1 for i in ids}
    result = p0.derive_scores(contract, ratings)
    for forbidden in p0.FORBIDDEN_SCORE_IDS:
        assert forbidden not in result.derived_scores


# --- mock smoke A/B/C/D ------------------------------------------------------

_MATERIALS = [
    {"scenario_id": "risk_project_choice", "condition_id": "D0_U0", "identity": "AI 决策者",
     "choice_direction": "choose_option_1"},
    {"scenario_id": "relationship_honesty", "condition_id": "D2_U3", "identity": "人类决策者",
     "choice_direction": "choose_option_1"},
]


def test_smoke_a_f1_pa_first(contract: p0.P0Contract) -> None:
    records = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "pa_first", repeats=1)
    assert len(records) == 2
    for rec in records:
        assert rec["is_mock"] is True
        assert len(rec["ratings"]) == 32
        assert p0.validate_response(
            contract, "pa13_wu19_combined", "pa_first",
            [{"item_id": e["item_id"], "rating": e["rating"]} for e in rec["ratings"]],
        ) == []


def test_smoke_b_f1_wu_first_deterministic(contract: p0.P0Contract) -> None:
    r1 = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "wu_first", repeats=1)
    r2 = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "wu_first", repeats=1)
    assert r1 == r2  # deterministic
    assert r1[0]["item_order_id"] == "wu_first"


def test_smoke_c_pa_only_wu_only(contract: p0.P0Contract) -> None:
    pa = p0.mock_run(contract, _MATERIALS, "pa13_only", "pa_only", repeats=1)
    wu = p0.mock_run(contract, _MATERIALS, "wu19_only", "wu_only", repeats=1)
    assert all(len(r["ratings"]) == 13 for r in pa)
    assert all(len(r["ratings"]) == 19 for r in wu)


@pytest.mark.parametrize("fault", ["missing_item", "duplicate_item", "out_of_range", "unknown_item"])
def test_smoke_d_error_fixtures(contract: p0.P0Contract, fault: str) -> None:
    records = p0.mock_run(
        contract, _MATERIALS[:1], "pa13_wu19_combined", "pa_first", repeats=1, inject_fault=fault
    )
    entries = [{"item_id": e["item_id"], "rating": e["rating"]} for e in records[0]["ratings"]]
    if fault in ("duplicate_item", "unknown_item"):
        with pytest.raises(p0.P0ContractError):
            p0.validate_response(contract, "pa13_wu19_combined", "pa_first", entries)
    else:
        warnings = p0.validate_response(contract, "pa13_wu19_combined", "pa_first", entries)
        assert warnings  # missing_item / out_of_range -> warning


def test_is_mock_always_true(contract: p0.P0Contract) -> None:
    records = p0.mock_run(contract, _MATERIALS, "pa13_wu19_combined", "pa_first", repeats=2)
    assert all(rec["is_mock"] is True for rec in records)


# --- request / item-rating accounting ---------------------------------------


def test_accounting_p1_min() -> None:
    acc = p0.account_requests(unique_materials=24, item_count=32, repeats=3, orders=1)
    assert acc["api_requests"] == 72
    assert acc["item_ratings"] == 2304


def test_accounting_p1_context() -> None:
    f1 = p0.account_requests(24, 32, 3, 1)
    pa_only = p0.account_requests(8, 13, 3, 1)
    wu_only = p0.account_requests(8, 19, 3, 1)
    total_requests = f1["api_requests"] + pa_only["api_requests"] + wu_only["api_requests"]
    total_item_ratings = f1["item_ratings"] + pa_only["item_ratings"] + wu_only["item_ratings"]
    assert total_requests == 120
    assert total_item_ratings == 3072


def test_accounting_p1_order() -> None:
    base = p0.account_requests(24, 32, 3, 1)  # PA-first
    wu_first_extra = p0.account_requests(8, 32, 3, 1)  # 8 materials, wu-first
    assert base["api_requests"] + wu_first_extra["api_requests"] == 96
    assert (base["api_requests"] + wu_first_extra["api_requests"]) * 32 == 3072
