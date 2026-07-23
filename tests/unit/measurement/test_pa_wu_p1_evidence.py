"""Structural validation for the PA-Wu P1 evidence & route decision (no models).

Read-only YAML/structure checks. NO network I/O, NO real model, NO API key.

Covered checks (task section 11):
 1. all three routes (R1/R2/R3) exist
 2. each route has the required decision-matrix fields
 3. R3 is flagged as adaptation, not a source-faithful version
 4. the provisional Chinese route is not marked validated
 5. Wu supplementary retrieval is a THREE-stage state machine
    (A: signed URL not captured; B: captured+attempted but download failed;
     C: ZIP obtained) with implications zip->attempted->captured
 6. no in-repo rehosted media file when PA media license is unclear
 7. no Wu19 / machine-agency / PA+Wu total generated
 8. no real-model call code
 9. no API key
10. final decision is consistent with blocking evidence gaps
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

EVID_DIR = (
    PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates" / "pa_wu_p1_evidence"
)
FORBIDDEN_TOTAL_MARKERS = ("WU19_TOTAL", "MACHINE_AGENCY_TOTAL", "PA_WU_TOTAL")
VALID_STATUSES = {
    "ready_for_execution_package_design",
    "ready_for_mock_package_only",
    "needs_more_evidence",
    "reject_for_current_project",
}


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def route_decision() -> dict:
    return _load(EVID_DIR / "p1_route_decision.yaml")


@pytest.fixture(scope="module")
def wu_retrieval() -> dict:
    return _load(EVID_DIR / "wu_supplementary_retrieval.yaml")


@pytest.fixture(scope="module")
def pa_media() -> dict:
    return _load(EVID_DIR / "pa_calibration_media_audit.yaml")


# --- 1: all three routes exist ----------------------------------------------


def test_three_routes_exist(route_decision: dict) -> None:
    ids = {str(r["route_id"]) for r in route_decision["routes"]}
    assert ids == {"R1", "R2", "R3"}


# --- 2: each matrix row has required fields ----------------------------------

REQUIRED_MATRIX_FIELDS = (
    "source_fidelity",
    "translation_risk",
    "identity_equivalence_risk",
    "du_anchor_fit",
    "positive_control_availability",
    "scoring_contract_compatibility",
    "interpretability",
    "request_burden",
    "research_claim_scope",
    "blocking_evidence_gaps",
    "recommended_status",
)


def test_matrix_rows_complete(route_decision: dict) -> None:
    rows = {str(m["route_id"]): m for m in route_decision["matrix"]}
    assert set(rows) == {"R1", "R2", "R3"}
    for rid, row in rows.items():
        for field in REQUIRED_MATRIX_FIELDS:
            assert field in row, f"{rid} missing {field}"
        # every dimension (except the two list/enum ones) has an explicit reason
        for field in REQUIRED_MATRIX_FIELDS:
            if field in ("blocking_evidence_gaps", "recommended_status"):
                continue
            assert str(row[field].get("reason", "")).strip(), f"{rid}.{field} has no reason"
        assert str(row["recommended_status"]) in VALID_STATUSES
        assert str(row["recommended_status_reason"]).strip()
        assert isinstance(row["blocking_evidence_gaps"]["items"], list)


# --- 3: R3 is adaptation, not source-faithful --------------------------------


def test_r3_is_adaptation(route_decision: dict) -> None:
    r3 = next(r for r in route_decision["routes"] if str(r["route_id"]) == "R3")
    assert r3["is_adaptation"] is True
    assert str(r3["fidelity_class"]) == "construct_adaptation"
    assert r3["is_default_route"] is False
    r1 = next(r for r in route_decision["routes"] if str(r["route_id"]) == "R1")
    assert r1["is_adaptation"] is False


# --- 4: provisional Chinese route not marked validated -----------------------


def test_r2_not_validated(route_decision: dict) -> None:
    r2 = next(r for r in route_decision["routes"] if str(r["route_id"]) == "R2")
    assert r2["translation_validated"] is False
    # no file in this dir claims a validated Chinese scale (only negations allowed)
    for path in EVID_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        for bad in ("validated Chinese scale", "已验证中文版", "有效中文版"):
            # allowed only in an explicit negation ("不" / "NOT" / "not")
            idx = 0
            while (idx := text.find(bad, idx)) != -1:
                window = text[max(0, idx - 12):idx]
                assert ("不" in window) or ("NOT" in window) or ("not" in window), (
                    f"unqualified '{bad}' in {path.name}"
                )
                idx += len(bad)


# --- 5: Wu supplementary link / retrieval / full-script separated ------------


EXPECTED_CONDITION_IDS = {
    "low_independence", "high_independence",
    "low_goal_orientation", "high_goal_orientation",
}


def test_wu_supplementary_status_separated(wu_retrieval: dict) -> None:
    # The resolved supplementary download TARGET must be recorded as discovered
    # and externally verified, independent of any agent-run download attempt.
    assert wu_retrieval["resolved_download_target_discovered"] is True
    assert str(wu_retrieval["resolved_file_name"]) == "zmag009_supplementary_data.zip"
    assert wu_retrieval["supplementary_link_discovered"] is True
    assert wu_retrieval["resolved_target_verified_by_external_review"] is True

    captured = wu_retrieval["signed_url_captured_in_agent_run"]
    attempted = wu_retrieval["actual_signed_url_attempted_in_agent_run"]
    zip_obtained = wu_retrieval["zip_obtained"]

    # --- general implications (hold in every stage) ------------------------
    # A successful ZIP implies a signed-url attempt was made; an attempt implies
    # the signed url was captured. Capturing/attempting does NOT imply success.
    if zip_obtained is True:
        assert attempted is True, "zip_obtained -> actual_signed_url_attempted_in_agent_run"
    if attempted is True:
        assert captured is True, (
            "actual_signed_url_attempted_in_agent_run -> signed_url_captured_in_agent_run"
        )

    audit = _load(EVID_DIR / "wu_table9_stimulus_audit.yaml")
    retrieval_status = str(wu_retrieval.get("retrieval_status", ""))

    # --- three explicit stages (no captured==zip conflation) ---------------
    if captured is False:
        # STAGE A: signed URL not captured in the agent run.
        assert attempted is False
        assert zip_obtained is False
        assert wu_retrieval.get("sha256") is None
        assert audit["table9_obtained_this_run"] is False
        assert len(audit["conditions"]) == 4
        for cond in audit["conditions"]:
            assert cond["verbatim_text_available"] is False
    elif zip_obtained is False:
        # STAGE B: signed URL captured AND attempted, but the download FAILED.
        assert attempted is True
        assert wu_retrieval.get("sha256") is None
        assert wu_retrieval["repository_action"]["full_supplementary_file_committed"] is False
        assert audit["table9_obtained_this_run"] is False
        assert len(audit["conditions"]) == 4
        for cond in audit["conditions"]:
            assert cond["verbatim_text_available"] is False
        # retrieval_status must NOT claim success in the failed-download stage.
        assert "not_obtained" in retrieval_status or "fail" in retrieval_status.lower(), (
            f"failed-download stage must not report success: {retrieval_status!r}"
        )
    else:
        # STAGE C: ZIP download SUCCEEDED (implies captured & attempted True).
        assert captured is True
        assert attempted is True
        assert str(wu_retrieval.get("sha256") or "").strip()
        assert audit["table9_obtained_this_run"] is True
        conds = {str(c["condition_id"]) for c in audit["conditions"]}
        assert conds == EXPECTED_CONDITION_IDS
        assert len(audit["conditions"]) == 4
        for c in audit["conditions"]:
            assert c["verbatim_text_available"] is True

    # In NO case may the log claim the material does not exist unless negated.
    text = (EVID_DIR / "wu_supplementary_retrieval.yaml").read_text(encoding="utf-8")
    low = text.lower()
    idx = 0
    while (idx := low.find("does not exist", idx)) != -1:
        window = low[max(0, idx - 60):idx]
        assert "not" in window, "unqualified 'material does not exist' claim in retrieval log"
        idx += len("does not exist")


# --- 6: no rehosted media file when PA media license unclear -----------------


def test_no_rehosted_pa_media(pa_media: dict) -> None:
    for m in pa_media["calibration_media"]:
        assert str(m["license_or_reuse_status"]) == "not_stated"
        assert m["may_rehost"] is False
        assert m["media_url"] is None
    assert pa_media["repository_action"]["media_downloaded_into_repo"] is False
    assert pa_media["repository_action"]["media_rehosted"] is False
    # there is no media binary committed in this evidence dir
    media_exts = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".zip", ".pdf", ".docx"}
    offenders = [p.name for p in EVID_DIR.rglob("*") if p.suffix.lower() in media_exts]
    assert offenders == [], f"unexpected media/binary files committed: {offenders}"


def test_pa_modality_status_not_overgeneralized(pa_media: dict) -> None:
    # The reason PA video cannot enter P1 must be contract/model status, NOT an
    # over-generalized "all LLMs cannot watch video".
    m = pa_media["target_rater_modality"]
    assert m["selected_model_not_fixed"] is True
    assert m["current_p1_contract_supports_video"] is False
    assert m["multimodal_model_applicability_evaluated"] is False
    text = (EVID_DIR / "pa_calibration_media_audit.yaml").read_text(encoding="utf-8").lower()
    assert "llm raters cannot watch video" not in text
    assert "无法观看视频" not in text


# --- 7: no forbidden totals --------------------------------------------------


def test_no_forbidden_totals() -> None:
    for path in EVID_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TOTAL_MARKERS:
            assert marker not in text, f"{marker} in {path.name}"


# --- 8 & 9: no real-model call code and no API key ---------------------------


def test_no_model_calls_or_api_keys() -> None:
    import re

    # substrings that would indicate real model-call code or credentials
    banned_substrings = (
        "openai", "anthropic", "api_key", "apikey", "requests.post",
        "httpx", "chat.completions", "deepseek",
    )
    # an actual OpenAI-style key literal: 'sk-' followed by >=16 key chars
    key_literal = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)
    for path in EVID_DIR.rglob("*"):
        if path.suffix.lower() not in (".yaml", ".md"):
            continue
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        for bad in banned_substrings:
            assert bad not in low, f"'{bad}' found in evidence asset {path.name}"
        assert not key_literal.search(text), f"API key literal found in {path.name}"


# --- 10: final decision consistent with blocking gaps ------------------------


def test_final_decision_consistent_with_gaps(route_decision: dict) -> None:
    # If any route still lists blocking evidence gaps, no route may be
    # 'ready_for_execution_package_design'; the strongest allowed is
    # 'ready_for_mock_package_only'. Aggregate check.
    statuses = {str(m["route_id"]): str(m["recommended_status"]) for m in route_decision["matrix"]}
    for m in route_decision["matrix"]:
        gaps = m["blocking_evidence_gaps"]["items"]
        if gaps:
            assert statuses[str(m["route_id"])] != "ready_for_execution_package_design", (
                f"{m['route_id']} has blocking gaps but is marked execution-ready"
            )
    # README final decision is 'C — needs more evidence' (not 'can run P1').
    readme = (EVID_DIR / "README.md").read_text(encoding="utf-8")
    assert "C — 仍需补证" in readme
    # every occurrence of the phrase '可运行 P1' must be inside a negation ('不得')
    idx = 0
    while (idx := readme.find("可运行 P1", idx)) != -1:
        window = readme[max(0, idx - 8):idx]
        assert "不得" in window, "unqualified '可运行 P1' claim in README"
        idx += len("可运行 P1")
