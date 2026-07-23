"""Structural validation for the PA-Wu P1 prep assets (no real model calls).

Checks the internal provisional translation + source-audited positive-control
assets against the merged P0 English contract. This test performs NO network I/O
and invokes NO real model; it only reads YAML files and compares structures.

Translation provenance: internal_agent_two_pass_translation (two internal
renderings, NOT a blinded independent re-translation).

Covered checks (task sections 2, 4, 8, 9, 13):
 - PA13/8/5 and Wu19 membership unchanged vs P0
 - English source_text_en (and MSI anchors) exactly match P0
 - every item has both passes / reconciled / back-translation, all non-empty
 - MSI left/right anchors + polarity: not swapped, low->negative, high->positive
 - no adaptation candidate text leaked into the literal translation
 - two DISTINCT status contracts (literal=none, adaptation=candidate_unvalidated)
 - review_status internal_agent_review_only everywhere
 - no forbidden totals
 - verbatim vs adapted-prototype not conflated
 - supplementary link availability vs retrieval separated; nothing unobtained
   recorded as obtained; PA author-page action descriptions recorded; PA synthetic
   prototype not filed as verbatim/calibration original
 - all 32 items present in item_review_matrix
 - protocol status enums consistent with the two asset layers
 - source / license fields complete
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

P0_DIR = PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates" / "pa_wu_p0"
P1_DIR = PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates" / "pa_wu_p1_prep"
PC_DIR = P1_DIR / "positive_controls"

FORBIDDEN_TOTAL_MARKERS = ("WU19_TOTAL", "MACHINE_AGENCY_TOTAL", "PA_WU_TOTAL")
MSI_IDS = {"MS1", "MS2", "MS3", "MS4", "MS5", "MS6"}

# Chinese negative/low markers and positive/high markers for anchor polarity.
LOW_MARKERS = ("没有", "不能", "无法", "不")
HIGH_HINT_MARKERS = ("有", "会", "拥有")


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def p0_pa() -> dict:
    return _load(P0_DIR / "items_pa_2024.yaml")


@pytest.fixture(scope="module")
def p0_wu() -> dict:
    return _load(P0_DIR / "items_wu_shen_2026.yaml")


@pytest.fixture(scope="module")
def p1_pa() -> dict:
    return _load(P1_DIR / "items_pa_2024.zh-CN.provisional.yaml")


@pytest.fixture(scope="module")
def p1_wu() -> dict:
    return _load(P1_DIR / "items_wu_shen_2026.zh-CN.provisional.yaml")


@pytest.fixture(scope="module")
def adaptations() -> dict:
    return _load(P1_DIR / "adaptation_candidates.yaml")


@pytest.fixture(scope="module")
def protocol() -> dict:
    return _load(P1_DIR / "translation_protocol.yaml")


@pytest.fixture(scope="module")
def matrix() -> dict:
    return _load(P1_DIR / "item_review_matrix.yaml")


# --- membership unchanged ----------------------------------------------------


def test_pa_membership_unchanged(p0_pa: dict, p1_pa: dict) -> None:
    p0_ids = [str(it["item_id"]) for it in p0_pa["items"]]
    p1_ids = [str(it["source_item_id"]) for it in p1_pa["items"]]
    assert set(p1_ids) == set(p0_ids)
    assert len(p1_ids) == 13
    assert len(p0_pa["versions"]["pa8"]) == 8
    assert len(p0_pa["versions"]["pa5"]) == 5
    assert set(p0_pa["versions"]["pa8"]).issubset(set(p0_ids))
    assert set(p0_pa["versions"]["pa5"]).issubset(set(p0_ids))


def test_wu_membership_unchanged(p0_wu: dict, p1_wu: dict) -> None:
    p0_src_ids = [str(it["source_item_id"]) for it in p0_wu["items"]]
    p1_src_ids = [str(it["source_item_id"]) for it in p1_wu["items"]]
    assert set(p1_src_ids) == set(p0_src_ids)
    assert len(p1_src_ids) == 19
    for it in p1_wu["items"]:
        p0_match = next(x for x in p0_wu["items"] if str(x["source_item_id"]) == str(it["source_item_id"]))
        assert str(it["construct"]) == str(p0_match["construct"])


# --- English source text matches P0 exactly ----------------------------------


def test_pa_source_text_matches_p0(p0_pa: dict, p1_pa: dict) -> None:
    p0_text = {str(it["item_id"]): str(it["text"]) for it in p0_pa["items"]}
    for it in p1_pa["items"]:
        assert str(it["source_text_en"]) == p0_text[str(it["source_item_id"])]


def test_wu_source_text_matches_p0(p0_wu: dict, p1_wu: dict) -> None:
    p0_text = {str(it["source_item_id"]): str(it["text"]) for it in p0_wu["items"]}
    p0_left = {str(it["source_item_id"]): str(it.get("left_anchor_text", "")) for it in p0_wu["items"]}
    p0_right = {str(it["source_item_id"]): str(it.get("right_anchor_text", "")) for it in p0_wu["items"]}
    for it in p1_wu["items"]:
        sid = str(it["source_item_id"])
        assert str(it["source_text_en"]) == p0_text[sid]
        if sid in MSI_IDS:
            assert str(it["source_left_anchor_en"]) == p0_left[sid]
            assert str(it["source_right_anchor_en"]) == p0_right[sid]


# --- every item has both passes / reconciled / back-translation, non-empty ---


def _has_all_translation_layers(it: dict) -> bool:
    required = ("translation_pass_a", "translation_pass_b", "reconciled_zh_cn", "back_translation_en")
    return all(str(it.get(k, "")).strip() for k in required)


def test_pa_all_translation_layers(p1_pa: dict) -> None:
    for it in p1_pa["items"]:
        assert _has_all_translation_layers(it), it.get("source_item_id")


def test_wu_all_translation_layers(p1_wu: dict) -> None:
    for it in p1_wu["items"]:
        assert _has_all_translation_layers(it), it.get("source_item_id")


# --- section 8: MSI anchors + polarity (not swapped, low<->negative) ---------


def test_msi_anchors_polarity_and_direction(p0_wu: dict, p1_wu: dict) -> None:
    p0_by_id = {str(it["source_item_id"]): it for it in p0_wu["items"]}
    seen = 0
    for it in p1_wu["items"]:
        sid = str(it["source_item_id"])
        if sid not in MSI_IDS:
            continue
        seen += 1
        left_zh = str(it.get("reconciled_left_anchor_zh_cn", ""))
        right_zh = str(it.get("reconciled_right_anchor_zh_cn", ""))
        # non-empty and distinct
        assert left_zh.strip() and right_zh.strip()
        assert left_zh.strip() != right_zh.strip()
        # polarity fields present and consistent across all six items
        assert str(it["left_polarity"]) == "low"
        assert str(it["right_polarity"]) == "high"
        # English anchors equal P0 (direction not reversed at source level)
        assert str(it["source_left_anchor_en"]) == str(p0_by_id[sid]["left_anchor_text"])
        assert str(it["source_right_anchor_en"]) == str(p0_by_id[sid]["right_anchor_text"])
        # Chinese low end expresses absence/negation; high end expresses presence.
        assert any(m in left_zh for m in LOW_MARKERS), f"{sid} left not negative: {left_zh}"
        assert any(m in right_zh for m in HIGH_HINT_MARKERS), f"{sid} right not positive: {right_zh}"
        # not swapped: the negated low end must not itself read as the positive end
        assert not (left_zh.strip() == right_zh.strip())
    assert seen == 6


def test_msi_direction_all_consistent(p1_wu: dict) -> None:
    polarities = [
        (str(it["left_polarity"]), str(it["right_polarity"]))
        for it in p1_wu["items"]
        if str(it["source_item_id"]) in MSI_IDS
    ]
    assert len(polarities) == 6
    assert all(p == ("low", "high") for p in polarities)


# --- no adaptation candidate leaked into the literal translation -------------


def test_no_adaptation_leak_into_literal(p1_pa: dict, p1_wu: dict, adaptations: dict) -> None:
    leaked_texts: set[str] = set()
    for entry in adaptations["candidates"]:
        for var in entry["variants"]:
            if var["variant"] != "literal_machine_version":
                leaked_texts.add(str(var["candidate_text"]).strip())
    for it in [*p1_pa["items"], *p1_wu["items"]]:
        assert str(it["reconciled_zh_cn"]).strip() not in leaked_texts
        assert str(it.get("adaptation_status", "none")) == "none"


# --- section 2: two DISTINCT status contracts -------------------------------


def test_protocol_two_distinct_status_contracts(protocol: dict) -> None:
    lit = protocol["literal_translation"]["adaptation_status_allowed"]
    adp = protocol["adaptation_candidates"]["status_allowed"]
    assert lit == ["none"]
    assert adp == ["candidate_unvalidated"]
    # the two enums must NOT be the same rule
    assert set(lit) != set(adp)


def test_literal_layer_status_contract(p1_pa: dict, p1_wu: dict, protocol: dict) -> None:
    allowed = set(protocol["literal_translation"]["adaptation_status_allowed"])
    for it in [*p1_pa["items"], *p1_wu["items"]]:
        assert str(it["adaptation_status"]) in allowed


def test_adaptation_layer_status_contract(adaptations: dict, protocol: dict) -> None:
    allowed = set(protocol["adaptation_candidates"]["status_allowed"])
    for entry in adaptations["candidates"]:
        for var in entry["variants"]:
            if var["variant"] == "literal_machine_version":
                continue
            assert str(var["status"]) in allowed


# --- section 1: provenance does not claim independence -----------------------


def test_protocol_does_not_claim_independence(protocol: dict) -> None:
    assert protocol["protocol_id"] == "pa_wu_p1_prep.internal_agent_two_pass_translation.v1"
    prov = protocol["provenance"]
    assert prov["independence_claim"] is False
    assert prov["isolation_evidence_available"] is False
    assert protocol["disclaimers"]["not_independent_re_translation"] is True
    # provisional files reference the two_pass protocol id
    for name in ("items_pa_2024.zh-CN.provisional.yaml", "items_wu_shen_2026.zh-CN.provisional.yaml"):
        data = _load(P1_DIR / name)
        assert "two_pass_translation" in str(data["protocol"])
        assert "dual_pass" not in str(data["protocol"])


# --- review_status everywhere ------------------------------------------------


def test_review_status_everywhere() -> None:
    files = [
        P1_DIR / "translation_protocol.yaml",
        P1_DIR / "terminology_glossary.yaml",
        P1_DIR / "items_pa_2024.zh-CN.provisional.yaml",
        P1_DIR / "items_wu_shen_2026.zh-CN.provisional.yaml",
        P1_DIR / "translation_decisions.yaml",
        P1_DIR / "adaptation_candidates.yaml",
        P1_DIR / "item_review_matrix.yaml",
        PC_DIR / "source_inventory.yaml",
        PC_DIR / "wu_independence_controls.yaml",
        PC_DIR / "wu_goal_orientation_controls.yaml",
        PC_DIR / "pa_calibration_inventory.yaml",
        PC_DIR / "synthetic_construct_prototypes.yaml",
    ]
    for path in files:
        data = _load(path)
        assert str(data.get("review_status")) == "internal_agent_review_only", path.name
    for path in (P1_DIR / "items_pa_2024.zh-CN.provisional.yaml",
                 P1_DIR / "items_wu_shen_2026.zh-CN.provisional.yaml",
                 P1_DIR / "item_review_matrix.yaml"):
        data = _load(path)
        for it in data["items"]:
            assert str(it["review_status"]) == "internal_agent_review_only"


# --- no forbidden totals -----------------------------------------------------


def test_no_forbidden_totals() -> None:
    for path in P1_DIR.rglob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TOTAL_MARKERS:
            assert marker not in text, f"{marker} found in {path.name}"


# --- section 4: all 32 items in the review matrix ----------------------------


def test_item_review_matrix_covers_all_32(p0_pa: dict, p0_wu: dict, matrix: dict) -> None:
    expected = {("pa_2024", str(it["item_id"])) for it in p0_pa["items"]}
    expected |= {("wu_shen_2026", str(it["source_item_id"])) for it in p0_wu["items"]}
    assert len(expected) == 32
    got = {(str(it["instrument_id"]), str(it["source_item_id"])) for it in matrix["items"]}
    assert got == expected
    # controlled enums respected
    enums = matrix["enums"]
    for it in matrix["items"]:
        assert str(it["semantic_fidelity_status"]) in enums["semantic_fidelity_status"]
        assert str(it["chinese_comprehensibility_risk"]) in enums["chinese_comprehensibility_risk"]
        assert str(it["construct_contamination_risk"]) in enums["construct_contamination_risk"]
        assert str(it["ai_human_parallel_risk"]) in enums["ai_human_parallel_risk"]
        assert str(it["du_material_anchor_risk"]) in enums["du_material_anchor_risk"]


# --- verbatim vs adapted-prototype not conflated -----------------------------


def test_verbatim_and_adapted_not_conflated() -> None:
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml",
                 "pa_calibration_inventory.yaml"):
        data = _load(PC_DIR / name)
        verbatim = data.get("source_verbatim_positive_control", []) or []
        adapted = data.get("source_adapted_positive_control_prototype", []) or []
        for v in verbatim:
            assert str(v.get("modifications")) == "none"
            assert "adapted_text" not in v
            assert "status" not in v
        for a in adapted:
            assert str(a["status"]) == "prototype_unvalidated"
            assert "verbatim_text" not in a


# --- section 9: rewritten source-consistency cross-checks --------------------


def test_inventory_and_controls_is_full_script_consistent() -> None:
    # (9.1) inventory says full script NOT obtained -> every verbatim fragment in
    # the wu control files must be is_full_script: false (no full-script claim).
    inv = _load(PC_DIR / "source_inventory.yaml")
    wu_src = next(s for s in inv["sources"] if "Wu" in str(s["source"]))
    for c in wu_src["constructs_audited"]:
        assert c["full_script_obtained"] is False
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml"):
        data = _load(PC_DIR / name)
        for v in data.get("source_verbatim_positive_control", []) or []:
            assert v.get("is_full_script") is False   # (9.3) no is_full_script: true


def test_supplementary_link_and_retrieval_separated() -> None:
    # (9.2) public link availability and retrieval-in-this-run are distinct fields.
    inv = _load(PC_DIR / "source_inventory.yaml")
    wu_src = next(s for s in inv["sources"] if "Wu" in str(s["source"]))
    for c in wu_src["constructs_audited"]:
        assert "public_supplementary_link_available" in c
        assert "supplementary_retrieved_in_this_run" in c
        assert "full_script_obtained" in c
        assert c["public_supplementary_link_available"] is True
        assert c["supplementary_retrieved_in_this_run"] is False
        assert str(c["full_script_expected_location"]).strip()


def test_pa_author_page_action_descriptions_recorded() -> None:
    # (9.4) PA author-page video morphology/action descriptions are recorded.
    inv = _load(PC_DIR / "source_inventory.yaml")
    pa_src = next(s for s in inv["sources"] if "Trafton" in str(s["source"]))
    cal = pa_src["constructs_audited"][0]
    assert cal["public_video_action_descriptions_available"] is True
    assert cal["public_full_text_stimulus_available"] is False
    assert str(cal["video_to_text_conversion_risk"]) == "high"
    names = {str(v["name"]) for v in cal["author_page_calibration_videos"]}
    assert {"Service", "Cheating RPS", "Feeder"} <= names
    for v in cal["author_page_calibration_videos"]:
        assert str(v["morphology"]).strip()
        assert str(v["action_description"]).strip()


def test_pa_synthetic_not_filed_as_verbatim_or_calibration_original() -> None:
    # (9.5) PA synthetic prototype must not be a verbatim/adapted positive control
    # nor a calibration original.
    pa = _load(PC_DIR / "pa_calibration_inventory.yaml")
    assert (pa.get("source_verbatim_positive_control") or []) == []
    assert (pa.get("source_adapted_positive_control_prototype") or []) == []
    syn = _load(PC_DIR / "synthetic_construct_prototypes.yaml")
    assert str(syn["kind"]) == "construct_derived_synthetic_prototype"
    assert syn["is_positive_control"] is False
    assert syn["is_original_stimulus"] is False
    assert syn["is_text_version_of_original_video"] is False
    assert syn["used_for_pa_calibration_reproduction"] is False
    for p in syn["prototypes"]:
        assert str(p["kind"]) == "construct_derived_synthetic_prototype"
        assert str(p["status"]) == "prototype_unvalidated"


def test_protocol_enums_consistent_with_asset_layers(protocol: dict, p1_pa: dict,
                                                     p1_wu: dict, adaptations: dict) -> None:
    # (9.7) protocol status enums match what the two asset layers actually use.
    lit_allowed = set(protocol["literal_translation"]["adaptation_status_allowed"])
    adp_allowed = set(protocol["adaptation_candidates"]["status_allowed"])
    lit_used = {str(it["adaptation_status"]) for it in [*p1_pa["items"], *p1_wu["items"]]}
    adp_used = set()
    for entry in adaptations["candidates"]:
        for var in entry["variants"]:
            if var["variant"] != "literal_machine_version":
                adp_used.add(str(var["status"]))
    assert lit_used <= lit_allowed
    assert adp_used <= adp_allowed


# --- section 7: independence prototype purified (no goal words) --------------


def test_independence_prototype_no_goal_contamination() -> None:
    data = _load(PC_DIR / "wu_independence_controls.yaml")
    high = next(
        a for a in data["source_adapted_positive_control_prototype"]
        if str(a["condition"]) == "high_independence"
    )
    text = str(high["adapted_text"])
    for banned in ("自行规划", "目标", "计划"):
        assert banned not in text, f"goal-orientation contamination '{banned}' in independence prototype"


# --- section 3: PA treats_others keeps 'as if' -------------------------------


def test_pa_treats_others_keeps_as_if(p1_pa: dict) -> None:
    it = next(x for x in p1_pa["items"] if str(x["source_item_id"]) == "pa_treats_others_as_minded")
    # reconciled Chinese must keep a hypothetical stance ("就好像"/"好像"/"仿佛"/"像...那样")
    assert any(m in str(it["reconciled_zh_cn"]) for m in ("就好像", "好像", "仿佛", "像"))
    # back-translation returns to an 'as if' structure
    assert "as if" in str(it["back_translation_en"]).lower()


# --- source / license fields complete ----------------------------------------


def test_source_and_license_fields_complete() -> None:
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml"):
        data = _load(PC_DIR / name)
        for v in data.get("source_verbatim_positive_control", []) or []:
            for field in ("source", "study", "construct", "condition", "verbatim_text",
                          "license", "retrieval_location", "verified_on"):
                assert str(v.get(field, "")).strip(), f"{name}:{field}"
    inv = _load(PC_DIR / "source_inventory.yaml")
    for src in inv["sources"]:
        assert str(src.get("doi", "")).strip()
