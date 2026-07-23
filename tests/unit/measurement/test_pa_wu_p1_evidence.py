"""Structural validation for the PA-Wu P1 evidence & route decision (no models).

Read-only YAML/structure checks. NO network I/O, NO real model, NO API key.

Covered checks (task section 11):
 1. all three routes (R1/R2/R3) exist
 2. each route has the required decision-matrix fields
 3. R3 is flagged as adaptation, not a source-faithful version
 4. the provisional Chinese route is not marked validated
 5. Wu supplementary link / retrieval / full-script status are separated
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


def test_wu_supplementary_status_separated(wu_retrieval: dict) -> None:
    assert str(wu_retrieval["retrieval_status"]) == "failed_this_run"
    assert wu_retrieval["failure"]["whether_public_link_exists"] is True
    assert wu_retrieval["failure"]["http_status"] == 403
    assert wu_retrieval["download_url"] is None
    assert wu_retrieval["sha256"] is None
    assert wu_retrieval["repository_action"]["full_supplementary_file_committed"] is False
    # "failed this run" must NOT be stated as "material does not exist".
    # The phrase may appear ONLY inside an explicit negation ("NOT the same as").
    text = (EVID_DIR / "wu_supplementary_retrieval.yaml").read_text(encoding="utf-8")
    low = text.lower()
    idx = 0
    while (idx := low.find("does not exist", idx)) != -1:
        # look at the preceding sentence: the phrase must be inside a negation
        # such as "... is not the same as 'the material does not exist'".
        window = low[max(0, idx - 60):idx]
        assert "not" in window, (
            "unqualified 'material does not exist' claim in retrieval log"
        )
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
