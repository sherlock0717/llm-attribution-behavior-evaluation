"""Tests for the neutral attribution-behavior task contract and its loader.

These verify that the external contract under ``tasks/attribution_behavior/``
loads, validates and stays behaviourally identical to the current benchmark
task pack. No network access; only local file reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freewill_attribution.contracts import (
    ContractError,
    default_task_path,
    load_task_contract,
)
from freewill_attribution.tasks.freewill_attribution import spec

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = REPO_ROOT / "tasks" / "attribution_behavior"


# --- file loading ----------------------------------------------------------

def test_default_task_path_points_at_contract():
    assert default_task_path() == TASK_DIR / "task.yaml"
    assert default_task_path().is_file()


def test_all_referenced_files_exist_and_parse():
    for name in ("task.yaml", "scenarios.jsonl", "conditions.yaml",
                 "items.yaml", "prompt.yaml"):
        assert (TASK_DIR / name).is_file(), name
    # loading exercises YAML + JSONL parsing and UTF-8 decoding of every file
    contract = load_task_contract()
    assert contract.task_id == "attribution-behavior"


def test_scenarios_jsonl_each_line_is_valid_json():
    text = (TASK_DIR / "scenarios.jsonl").read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert len(lines) == 8
    for ln in lines:
        json.loads(ln)
    # file ends with a trailing newline
    assert text.endswith("\n")


# --- uniqueness ------------------------------------------------------------

def test_ids_are_unique():
    c = load_task_contract()
    for ids in (c.scenario_ids, c.condition_ids, c.item_ids):
        assert len(ids) == len(set(ids)), ids


def test_task_id_is_neutral():
    c = load_task_contract()
    assert c.task_id == "attribution-behavior"
    assert "freewill" not in c.task_id
    assert "v1" not in c.task_id and "v2" not in c.task_id


# --- completeness ----------------------------------------------------------

def test_counts_match_current_design():
    c = load_task_contract()
    assert len(c.scenarios) == 8
    assert len(c.conditions) == 6
    assert len(c.identity_labels) == 2
    assert len(c.items) == 34


def test_each_scenario_has_required_fields():
    c = load_task_contract()
    for s in c.scenarios:
        assert s.context and s.option_a and s.option_b and s.fixed_choice


def test_each_condition_has_template():
    c = load_task_contract()
    for cond in c.conditions:
        assert "{actor}" in cond.process_template or "{fixed_choice}" in cond.process_template


def test_each_item_has_valid_range():
    c = load_task_contract()
    for it in c.items:
        assert it.min_score <= it.max_score
        if it.construct == "factual_manipulation_check":
            assert (it.min_score, it.max_score) == (0, 2)
        else:
            assert (it.min_score, it.max_score) == (1, 7)


# --- behavioural parity with the current task pack -------------------------

def test_contract_matches_task_pack_ids_and_order():
    c = load_task_contract()
    assert c.condition_ids == list(spec.PROCESS_CONDITIONS)
    assert c.identity_labels == list(spec.IDENTITY_LABELS)
    assert c.item_ids == list(spec.ITEM_IDS)
    assert [s.scenario_id for s in c.scenarios] == [s.scenario_id for s in spec.SCENARIOS]


def test_material_rendering_is_stable_anchor():
    c = load_task_contract()
    # A small explicit anchor (not the full corpus): the direct_choice material
    # for one scenario/identity must match the frame + process contract exactly.
    text = c.build_decision_text("self_control_deadline", "direct_choice", "AI 决策者")
    assert text.startswith("【情境】")
    assert "【决策者身份】AI 决策者" in text
    assert text.rstrip().endswith("AI 决策者选择：拒绝娱乐活动，先完成申请材料。")


def test_task_pack_and_contract_render_identically():
    c = load_task_contract()
    # spec.build_decision_text delegates to the contract; both must agree for a
    # representative structured condition.
    a = c.build_decision_text("risk_project_choice", "reasons", "人类决策者")
    b = spec.build_decision_text("risk_project_choice", "reasons", "人类决策者")
    assert a == b


# --- path safety -----------------------------------------------------------

def test_loads_with_explicit_path():
    c = load_task_contract(TASK_DIR / "task.yaml")
    assert c.task_id == "attribution-behavior"


def test_missing_task_file_is_reported_clearly(tmp_path):
    with pytest.raises(ContractError) as exc:
        load_task_contract(tmp_path / "nope" / "task.yaml")
    assert "task.yaml" in str(exc.value)


def test_traversal_reference_is_rejected(tmp_path):
    # A task.yaml that points its scenario_source outside the task dir must fail.
    bad_dir = tmp_path / "bad_task"
    bad_dir.mkdir()
    (bad_dir / "task.yaml").write_text(
        "task_id: attribution-behavior\n"
        "scenario_source: ../../etc/passwd\n"
        "condition_source: conditions.yaml\n"
        "item_source: items.yaml\n"
        "prompt_source: prompt.yaml\n",
        encoding="utf-8",
    )
    with pytest.raises(ContractError) as exc:
        load_task_contract(bad_dir / "task.yaml")
    assert "escape" in str(exc.value) or "not found" in str(exc.value)
