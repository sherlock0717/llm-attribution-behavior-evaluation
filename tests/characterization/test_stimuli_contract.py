"""Characterization tests for src/stimuli.py.

These tests record the *current* v0.1 behavior of the stimulus module so that
later refactors (FND-004+) have a regression baseline. They deliberately do not
judge whether the current material design is methodologically ideal, nor do they
treat the current behavior as a permanent product specification.
"""

from __future__ import annotations

import pytest

from stimuli import (
    IDENTITY_LABELS,
    IDENTITY_ORDINAL,
    PROCESS_CONDITIONS,
    PROCESS_ORDINAL,
    SCENARIOS,
    all_materials,
    build_decision_text,
)

VALID_VALENCES = {"positive_choice", "mixed_choice", "negative_choice"}


def test_process_conditions_current_order():
    assert PROCESS_CONDITIONS == [
        "direct_choice",
        "direct_choice_long",
        "alternatives",
        "reasons_concise",
        "reasons",
        "reflection_feedback",
    ]


def test_process_ordinal_current_mapping():
    assert PROCESS_ORDINAL == {
        "direct_choice": 0,
        "direct_choice_long": 0,
        "alternatives": 1,
        "reasons_concise": 2,
        "reasons": 2,
        "reflection_feedback": 3,
    }


def test_identity_labels_and_ordinals():
    assert IDENTITY_LABELS == ["AI 决策者", "人类决策者"]
    assert IDENTITY_ORDINAL == {"AI 决策者": 0, "人类决策者": 1}


def test_scenarios_structure():
    assert len(SCENARIOS) == 8

    ids = [s.scenario_id for s in SCENARIOS]
    assert len(set(ids)) == len(ids)

    for scenario in SCENARIOS:
        assert scenario.fixed_choice in (scenario.option_a, scenario.option_b)
        assert scenario.domain
        assert scenario.context
        assert scenario.choice_valence in VALID_VALENCES


def test_full_material_matrix():
    rows = all_materials()

    assert len(rows) == 8 * 2 * 6 == 96

    combos = {
        (r["scenario_id"], r["identity_label"], r["process_condition"]) for r in rows
    }
    assert len(combos) == len(rows)

    for row in rows:
        text = row["text"]
        assert row["char_len"] == len(text)
        assert row["synthetic"] is True
        assert "【情境】" in text
        assert "【决策者身份】" in text
        assert "【决策过程】" in text
        assert row["identity_label"] in text
        assert row["structure_level"] == PROCESS_ORDINAL[row["process_condition"]]


def test_unknown_process_condition_raises_value_error():
    scenario = SCENARIOS[0]
    with pytest.raises(ValueError):
        build_decision_text(scenario, "not_a_real_condition", IDENTITY_LABELS[0])
