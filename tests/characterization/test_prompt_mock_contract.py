"""Characterization tests for prompt construction, extract_json() and mock_response().

Records the current prompt exposure structure, JSON extraction behavior and the
deterministic rule-based mock generator. These tests do not endorse the current
prompt design; they merely capture present behavior.
"""

from __future__ import annotations

import json
import random

import pytest

from scales import ITEM_RESPONSE_RANGES, ITEMS
from run_simulated_study import build_prompt, extract_json, make_design, mock_response

SEED = 20260425


def _sample_row():
    return make_design(n_per_cell=1, seed=SEED)[0]


def test_build_prompt_current_structure():
    row = _sample_row()
    messages = build_prompt(row["persona"], row["material"])

    assert len(messages) == 2
    assert [m["role"] for m in messages] == ["system", "user"]

    payload = json.loads(messages[1]["content"])
    for key in (
        "task",
        "factual_check_rule",
        "persona",
        "material",
        "items",
        "output_schema",
        "strict_rules",
    ):
        assert key in payload

    assert len(payload["items"]) == 34
    prompt_item_ids = {item["item_id"] for item in payload["items"]}
    assert prompt_item_ids == {item.item_id for item in ITEMS}
    assert payload["output_schema"]["participant_id"] == row["persona"]["participant_id"]


def test_extract_json_plain_object():
    assert extract_json('{"a": 1, "b": 2}') == {"a": 1, "b": 2}


def test_extract_json_fenced_block():
    fenced = "```json\n{\"a\": 1}\n```"
    assert extract_json(fenced) == {"a": 1}


def test_extract_json_embedded_in_text():
    text = "preamble text {\"a\": 1, \"c\": 3} trailing text"
    assert extract_json(text) == {"a": 1, "c": 3}


def test_extract_json_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        extract_json("this is not json at all")


def test_mock_response_is_deterministic_and_in_range():
    row = _sample_row()
    first = mock_response(row, random.Random(12345))
    second = mock_response(row, random.Random(12345))

    assert first == second

    ratings = first["ratings"]
    assert set(ratings.keys()) == {item.item_id for item in ITEMS}
    assert len(ratings) == 34

    for item_id, value in ratings.items():
        low, high = ITEM_RESPONSE_RANGES[item_id]
        assert low <= value <= high

    assert first["participant_id"] == row["participant_id"]
    assert first["attention_check"] == "已按材料评分"
    assert first["short_reason"] == "mock synthetic response"
