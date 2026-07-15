"""Unit tests for parsing/validation + scoring (FAST-001)."""

from __future__ import annotations

import json

from freewill_attribution.benchmark.models import (
    AttemptParseStatus,
    AttemptValidationStatus,
)
from freewill_attribution.tasks.freewill_attribution import parsing, scoring, spec


def _valid_payload():
    items = []
    for s in spec.ITEM_SPECS:
        low = s["response_min"]
        items.append({"item_id": s["item_id"], "rating": low})
    return {"items": items}


def test_parse_ok_and_fence_stripped():
    text = "```json\n" + json.dumps(_valid_payload()) + "\n```"
    payload, status, _ = parsing.parse_response(text)
    assert status == AttemptParseStatus.OK
    assert isinstance(payload, dict)


def test_parse_empty_and_malformed():
    _, status_empty, _ = parsing.parse_response("")
    assert status_empty == AttemptParseStatus.EMPTY
    _, status_bad, _ = parsing.parse_response("{items: [")
    assert status_bad == AttemptParseStatus.MALFORMED_JSON


def test_validate_ok():
    ratings, status, detail, _ = parsing.validate_core(_valid_payload())
    assert status == AttemptValidationStatus.OK
    assert len(ratings) == 34
    assert detail["missing"] == []


def test_validate_missing_item():
    payload = _valid_payload()
    payload["items"] = payload["items"][:-1]
    _, status, detail, _ = parsing.validate_core(payload)
    assert status == AttemptValidationStatus.MISSING_ITEM
    assert len(detail["missing"]) == 1


def test_validate_out_of_range():
    payload = _valid_payload()
    payload["items"][0]["rating"] = 999
    _, status, detail, _ = parsing.validate_core(payload)
    assert status == AttemptValidationStatus.OUT_OF_RANGE
    assert detail["out_of_range"]


def test_validate_unknown_and_duplicate():
    payload = _valid_payload()
    payload["items"].append({"item_id": "not_a_real_item", "rating": 1})
    _, status, _detail, _ = parsing.validate_core(payload)
    assert status == AttemptValidationStatus.UNKNOWN_ITEM

    dup = _valid_payload()
    dup["items"].append(dict(dup["items"][0]))
    _, dup_status, _dd, _ = parsing.validate_core(dup)
    assert dup_status == AttemptValidationStatus.DUPLICATE_ITEM


def test_scoring_scale_means():
    ratings = {s["item_id"]: s["response_min"] for s in spec.ITEM_SPECS}
    scores = scoring.score_ratings(ratings)
    assert "agency" in scores
    assert scores["agency"] is not None


def test_aggregate_contrasts_present():
    records = []
    for cond in spec.PROCESS_CONDITIONS:
        for ident in spec.IDENTITY_LABELS:
            records.append({"condition": cond, "identity": ident, "scores": {"agency": 4.0, "free_will_attribution": 4.0}})
    agg = scoring.aggregate_scores(records)
    assert "condition_sensitivity_agency" in agg
    assert "identity_effect_human_minus_ai" in agg
