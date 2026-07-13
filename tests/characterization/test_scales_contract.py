"""Characterization tests for src/scales.py.

Records the current item pool structure and response ranges. These tests only
fix the existing definitions; they do not claim the current scales have passed
formal psychometric validation.
"""

from __future__ import annotations

from scales import ITEM_RESPONSE_RANGES, ITEM_TEXT, ITEMS, SCALE_ITEMS


def test_item_count_and_uniqueness():
    assert len(ITEMS) == 34
    ids = [item.item_id for item in ITEMS]
    assert len(set(ids)) == 34


def test_current_scale_item_counts():
    expected_counts = {
        "agency": 6,
        "experience": 5,
        "free_will_attribution": 5,
        "autonomy": 3,
        "outcome_accountability": 2,
        "moral_praise_blame": 2,
        "process_accountability": 2,
        "perceived_intelligence": 3,
        "factual_manipulation_check": 3,
        "subjective_process_completeness": 3,
    }
    actual_counts = {scale: len(items) for scale, items in SCALE_ITEMS.items()}
    assert actual_counts == expected_counts
    assert sum(expected_counts.values()) == 34


def test_response_ranges_current_behavior():
    for item in ITEMS:
        if item.scale == "factual_manipulation_check":
            assert (item.response_min, item.response_max) == (0, 2)
        else:
            assert (item.response_min, item.response_max) == (1, 7)

        assert ITEM_RESPONSE_RANGES[item.item_id] == (item.response_min, item.response_max)
        assert ITEM_TEXT[item.item_id] == item.text
        assert item.text


def test_factual_and_other_item_split():
    factual = [i for i in ITEMS if i.scale == "factual_manipulation_check"]
    others = [i for i in ITEMS if i.scale != "factual_manipulation_check"]
    assert len(factual) == 3
    assert len(others) == 31
