"""Characterization tests for pure functions in src/analyze_results.py.

Only pure helpers are exercised (cronbach_alpha, scale_scores, char_len_summary).
The full analysis pipeline, ANOVA, bootstrap mediation, plots and report
generation are out of scope for this task. Alpha values here are NOT treated as
validated psychometric conclusions.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from scales import SCALE_ITEMS
from stimuli import PROCESS_CONDITIONS
from analyze_results import char_len_summary, cronbach_alpha, scale_scores


def test_cronbach_alpha_fewer_than_two_items_is_nan():
    df = pd.DataFrame({"a": [1, 2, 3]})
    assert math.isnan(cronbach_alpha(df))


def test_cronbach_alpha_fewer_than_three_rows_is_nan():
    df = pd.DataFrame({"a": [1, 2], "b": [2, 3]})
    assert math.isnan(cronbach_alpha(df))


def test_cronbach_alpha_zero_total_variance_is_nan():
    # Row sums are all 4 -> total variance is zero.
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1]})
    assert math.isnan(cronbach_alpha(df))


def test_cronbach_alpha_nondegenerate_is_finite_float():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1, 2, 3, 4, 6]})
    value = cronbach_alpha(df)
    assert isinstance(value, float)
    assert math.isfinite(value)


def test_scale_scores_row_means_and_responsibility_total():
    scales_used = [
        "agency",
        "outcome_accountability",
        "moral_praise_blame",
        "process_accountability",
    ]

    data = {
        "participant_id": ["p1", "p2"],
        "identity_label": ["AI 决策者", "人类决策者"],
        "identity_ordinal": [0, 1],
        "process_condition": ["direct_choice", "reasons"],
        "process_ordinal": [0, 2],
        "structure_level": [0, 2],
        "scenario_id": ["s1", "s2"],
        "domain": ["d", "d"],
        "choice_valence": ["positive_choice", "negative_choice"],
        "char_len": [10, 20],
        "synthetic": [True, True],
    }
    for scale in scales_used:
        for offset, item_id in enumerate(SCALE_ITEMS[scale]):
            data[item_id] = [offset + 1, offset + 2]

    df = pd.DataFrame(data)
    scores = scale_scores(df)

    agency_items = SCALE_ITEMS["agency"]
    expected_agency = sum(df[c].iloc[0] for c in agency_items) / len(agency_items)
    assert scores["agency"].iloc[0] == pytest.approx(expected_agency)

    expected_rt = (
        scores["outcome_accountability"].iloc[0]
        + scores["moral_praise_blame"].iloc[0]
        + scores["process_accountability"].iloc[0]
    ) / 3
    assert scores["responsibility_total"].iloc[0] == pytest.approx(expected_rt)

    assert list(scores["participant_id"]) == ["p1", "p2"]
    assert list(scores["process_condition"]) == ["direct_choice", "reasons"]


def test_char_len_summary_orders_by_process_conditions():
    unordered = [
        "reasons",
        "direct_choice",
        "reflection_feedback",
        "alternatives",
        "reasons_concise",
        "direct_choice_long",
    ]
    df = pd.DataFrame(
        {
            "process_condition": unordered,
            "char_len": [10, 20, 30, 40, 50, 60],
        }
    )
    summary = char_len_summary(df)
    assert list(summary["process_condition"]) == PROCESS_CONDITIONS
