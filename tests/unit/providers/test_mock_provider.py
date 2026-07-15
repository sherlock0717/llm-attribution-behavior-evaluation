"""Unit tests for the deterministic mock provider (FAST-001)."""

from __future__ import annotations

import json

from freewill_attribution.providers.base import ProviderRequest
from freewill_attribution.providers.mock import MockProvider
from freewill_attribution.tasks.freewill_attribution import spec


def _request(**overrides):
    base = dict(
        prompt="p",
        task_id="freewill-attribution-v2",
        condition="reasons",
        identity="人类决策者",
        scenario_id="moral_friend_report",
        seed=20260425,
        request_index=0,
        attempt=1,
        item_specs=tuple(spec.ITEM_SPECS),
        structure_level=2,
        choice_valence="mixed_choice",
    )
    base.update(overrides)
    return ProviderRequest(**base)


def test_mock_is_deterministic():
    p = MockProvider()
    r1 = p.generate(_request())
    r2 = p.generate(_request())
    assert r1.text == r2.text
    assert r1.provider == "mock"
    assert r1.model_id == "rule-based-v2"
    assert r1.usage is None
    assert r1.finish_reason == "mock_complete"


def test_mock_output_is_valid_core_json_with_all_items():
    p = MockProvider()
    payload = json.loads(p.generate(_request()).text)
    assert set(payload.keys()) == {"items"}
    ids = [i["item_id"] for i in payload["items"]]
    assert sorted(ids) == sorted(spec.ITEM_IDS)
    for entry in payload["items"]:
        low, high = spec.ITEM_RANGE[entry["item_id"]]
        assert low <= entry["rating"] <= high


def test_mock_no_runner_owned_metadata():
    p = MockProvider()
    payload = json.loads(p.generate(_request()).text)
    for banned in ("participant_id", "condition", "identity", "run_id", "task_id", "short_reason"):
        assert banned not in payload


def test_conditions_produce_some_difference():
    p = MockProvider()
    low = json.loads(p.generate(_request(condition="direct_choice", structure_level=0)).text)
    high = json.loads(p.generate(_request(condition="reflection_feedback", structure_level=3)).text)
    assert low["items"] != high["items"]


def test_fault_injection_only_affects_first_attempt():
    p = MockProvider()
    bad = p.generate(_request(fault="malformed_json", attempt=1)).text
    good = p.generate(_request(fault="malformed_json", attempt=2)).text
    # first attempt malformed; repair attempt valid JSON
    try:
        json.loads(bad)
        malformed = False
    except json.JSONDecodeError:
        malformed = True
    assert malformed
    assert json.loads(good)["items"]
