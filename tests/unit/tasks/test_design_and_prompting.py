"""Unit tests for task-pack design + prompting (FAST-001)."""

from __future__ import annotations

import json

from freewill_attribution.tasks.freewill_attribution import prompting, spec, stimuli


def test_design_cell_counts():
    design = stimuli.build_design(n_per_cell=2, seed=20260425)
    assert len(design) == 6 * 2 * 2  # 24
    cells = {}
    for row in design:
        cells.setdefault((row["condition"], row["identity"]), 0)
        cells[(row["condition"], row["identity"])] += 1
    assert len(cells) == 12
    assert set(cells.values()) == {2}


def test_design_is_deterministic():
    a = stimuli.build_design(1, 20260425)
    b = stimuli.build_design(1, 20260425)
    assert [r["record_id"] for r in a] == [r["record_id"] for r in b]
    assert [r["material"] for r in a] == [r["material"] for r in b]


def test_six_conditions_two_identities():
    assert len(spec.PROCESS_CONDITIONS) == 6
    assert len(spec.IDENTITY_LABELS) == 2
    assert len(spec.ITEM_IDS) == 34


def test_prompt_hides_construct_labels():
    design = stimuli.build_design(1, 20260425)
    text = prompting.render_prompt(design[0])
    payload = json.loads(text)
    # No item exposes a 'scale'/construct label.
    for item in payload["items"]:
        assert "scale" not in item
        assert set(item.keys()) <= {"item_id", "text", "valid_range", "coding"}
    # Construct label words must not appear as JSON scale keys.
    assert '"scale"' not in text


def test_prompt_template_stable_hash_inputs():
    t1 = prompting.prompt_template_text()
    t2 = prompting.prompt_template_text()
    assert t1 == t2


def test_factual_items_use_0_2_range():
    factual = [i for i in spec.ITEM_SPECS if i["scale"] == "factual_manipulation_check"]
    assert factual
    for item in factual:
        assert (item["response_min"], item["response_max"]) == (0, 2)
