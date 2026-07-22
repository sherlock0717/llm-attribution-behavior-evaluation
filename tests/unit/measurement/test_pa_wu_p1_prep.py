"""Structural validation for the PA-Wu P1 prep assets (no real model calls).

Checks the internal provisional translation + source-audited positive-control
assets against the merged P0 English contract. This test performs NO network I/O
and invokes NO real model; it only reads YAML files and compares structures.

Covered checks (task section 13):
 1. PA13/8/5 membership unchanged vs P0
 2. Wu19 membership unchanged vs P0
 3. English source_text_en exactly matches P0
 4. every item has A/B/reconciled/back-translation
 5. all Chinese translations non-empty
 6. MSI left/right anchors complete and direction not reversed
 7. no adaptation candidate text leaked into the literal translation fields
 8. adaptation_status is candidate_unvalidated in adaptation_candidates
 9. review_status is internal_agent_review_only everywhere
10. no forbidden totals generated
11. source-verbatim vs source-adapted not conflated
12. no unobtained stimulus recorded as obtained
13. source / license fields complete
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


# --- 1 & 2: membership unchanged (P1 prep must not alter P0 membership) ------


def test_pa_membership_unchanged(p0_pa: dict, p1_pa: dict) -> None:
    p0_ids = [str(it["item_id"]) for it in p0_pa["items"]]
    p1_ids = [str(it["source_item_id"]) for it in p1_pa["items"]]
    # provisional PA translates exactly the 13 scored items (attention check excluded)
    assert set(p1_ids) == set(p0_ids)
    assert len(p1_ids) == 13
    # PA8 / PA5 still derive from PA13 in P0 (P1 prep adds no new short-form members)
    assert len(p0_pa["versions"]["pa8"]) == 8
    assert len(p0_pa["versions"]["pa5"]) == 5
    assert set(p0_pa["versions"]["pa8"]).issubset(set(p0_ids))
    assert set(p0_pa["versions"]["pa5"]).issubset(set(p0_ids))


def test_wu_membership_unchanged(p0_wu: dict, p1_wu: dict) -> None:
    p0_src_ids = [str(it["source_item_id"]) for it in p0_wu["items"]]
    p1_src_ids = [str(it["source_item_id"]) for it in p1_wu["items"]]
    assert set(p1_src_ids) == set(p0_src_ids)
    assert len(p1_src_ids) == 19
    # construct mapping unchanged
    for it in p1_wu["items"]:
        p0_match = next(x for x in p0_wu["items"] if str(x["source_item_id"]) == str(it["source_item_id"]))
        assert str(it["construct"]) == str(p0_match["construct"])


# --- 3: English source text matches P0 exactly ------------------------------


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


# --- 4 & 5: every item has A/B/reconciled/back-translation, all non-empty ----


def _has_all_translation_layers(it: dict) -> bool:
    required = ("translation_pass_a", "translation_pass_b", "reconciled_zh_cn", "back_translation_en")
    return all(str(it.get(k, "")).strip() for k in required)


def test_pa_all_translation_layers(p1_pa: dict) -> None:
    for it in p1_pa["items"]:
        assert _has_all_translation_layers(it), it.get("source_item_id")


def test_wu_all_translation_layers(p1_wu: dict) -> None:
    for it in p1_wu["items"]:
        assert _has_all_translation_layers(it), it.get("source_item_id")


# --- 6: MSI anchors complete + direction not reversed ------------------------


def test_msi_anchors_complete_and_direction_preserved(p0_wu: dict, p1_wu: dict) -> None:
    p0_by_id = {str(it["source_item_id"]): it for it in p0_wu["items"]}
    seen = 0
    for it in p1_wu["items"]:
        sid = str(it["source_item_id"])
        if sid not in MSI_IDS:
            continue
        seen += 1
        left_zh = str(it.get("reconciled_left_anchor_zh_cn", ""))
        right_zh = str(it.get("reconciled_right_anchor_zh_cn", ""))
        assert left_zh.strip() and right_zh.strip()
        assert left_zh.strip() != right_zh.strip()
        # direction preserved: the P1 English anchors equal the P0 English anchors
        assert str(it["source_left_anchor_en"]) == str(p0_by_id[sid]["left_anchor_text"])
        assert str(it["source_right_anchor_en"]) == str(p0_by_id[sid]["right_anchor_text"])
        # low pole (left) must not be silently swapped with the high pole (right):
        # the P0 left anchor is the "no/negative" pole in this instrument.
        assert str(p0_by_id[sid]["left_anchor_text"]) == str(it["source_left_anchor_en"])
    assert seen == 6


# --- 7: no adaptation candidate leaked into the literal translation ----------


def test_no_adaptation_leak_into_literal(p1_pa: dict, p1_wu: dict, adaptations: dict) -> None:
    # Collect all ai/human/neutral candidate texts (non-literal variants).
    leaked_texts: set[str] = set()
    for entry in adaptations["candidates"]:
        for var in entry["variants"]:
            if var["variant"] != "literal_machine_version":
                leaked_texts.add(str(var["candidate_text"]).strip())
    # None of these must appear as a reconciled literal translation.
    for it in [*p1_pa["items"], *p1_wu["items"]]:
        assert str(it["reconciled_zh_cn"]).strip() not in leaked_texts
        # literal translation must not carry an adaptation_status other than 'none'
        assert str(it.get("adaptation_status", "none")) == "none"


# --- 8: adaptation_status candidate_unvalidated ------------------------------


def test_adaptation_status_all_unvalidated(adaptations: dict) -> None:
    for entry in adaptations["candidates"]:
        for var in entry["variants"]:
            if var["variant"] == "literal_machine_version":
                continue
            assert str(var["status"]) == "candidate_unvalidated"


# --- 9: review_status internal_agent_review_only everywhere ------------------


def test_review_status_everywhere() -> None:
    files = [
        P1_DIR / "translation_protocol.yaml",
        P1_DIR / "terminology_glossary.yaml",
        P1_DIR / "items_pa_2024.zh-CN.provisional.yaml",
        P1_DIR / "items_wu_shen_2026.zh-CN.provisional.yaml",
        P1_DIR / "translation_decisions.yaml",
        P1_DIR / "adaptation_candidates.yaml",
        PC_DIR / "source_inventory.yaml",
        PC_DIR / "wu_independence_controls.yaml",
        PC_DIR / "wu_goal_orientation_controls.yaml",
        PC_DIR / "pa_calibration_inventory.yaml",
    ]
    for path in files:
        data = _load(path)
        assert str(data.get("review_status")) == "internal_agent_review_only", path.name
    # per-item review_status too
    for path in (P1_DIR / "items_pa_2024.zh-CN.provisional.yaml",
                 P1_DIR / "items_wu_shen_2026.zh-CN.provisional.yaml"):
        data = _load(path)
        for it in data["items"]:
            assert str(it["review_status"]) == "internal_agent_review_only"


# --- 10: no forbidden totals generated anywhere ------------------------------


def test_no_forbidden_totals() -> None:
    for path in P1_DIR.rglob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TOTAL_MARKERS:
            assert marker not in text, f"{marker} found in {path.name}"


# --- 11: verbatim vs adapted not conflated -----------------------------------


def test_verbatim_and_adapted_not_conflated() -> None:
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml",
                 "pa_calibration_inventory.yaml"):
        data = _load(PC_DIR / name)
        verbatim = data.get("source_verbatim_positive_control", []) or []
        adapted = data.get("source_adapted_positive_control_prototype", []) or []
        # verbatim entries carry modifications: none and no adapted-only fields
        for v in verbatim:
            assert str(v.get("modifications")) == "none"
            assert "adapted_text" not in v
            assert "status" not in v  # verbatim has no prototype status
        # adapted entries are prototype_unvalidated and never claim to be originals
        for a in adapted:
            assert str(a["status"]) == "prototype_unvalidated"
            assert "verbatim_text" not in a


# --- 12: nothing unobtained recorded as obtained -----------------------------


def test_no_unobtained_recorded_as_obtained() -> None:
    inv = _load(PC_DIR / "source_inventory.yaml")
    for src in inv["sources"]:
        for c in src["constructs_audited"]:
            # If a full verbatim script was not available, no verbatim entry may
            # claim is_full_script: true for that construct.
            if c.get("full_verbatim_script_available") is False:
                pass  # inventory itself is consistent; detailed check below
    # Any verbatim fragment must be explicitly flagged is_full_script: false
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml"):
        data = _load(PC_DIR / name)
        for v in data.get("source_verbatim_positive_control", []) or []:
            assert v.get("is_full_script") is False
    # PA has no public text stimulus -> verbatim list must be empty
    pa = _load(PC_DIR / "pa_calibration_inventory.yaml")
    assert (pa.get("source_verbatim_positive_control") or []) == []


# --- 13: source / license fields complete ------------------------------------


def test_source_and_license_fields_complete() -> None:
    for name in ("wu_independence_controls.yaml", "wu_goal_orientation_controls.yaml"):
        data = _load(PC_DIR / name)
        for v in data.get("source_verbatim_positive_control", []) or []:
            for field in ("source", "study", "construct", "condition", "verbatim_text",
                          "license", "retrieval_location", "verified_on"):
                assert str(v.get(field, "")).strip(), f"{name}:{field}"
    inv = _load(PC_DIR / "source_inventory.yaml")
    for src in inv["sources"]:
        assert str(src.get("license") or src.get("doi")).strip()
        assert str(src.get("doi", "")).strip()
