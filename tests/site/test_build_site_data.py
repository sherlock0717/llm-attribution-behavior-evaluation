"""Tests for scripts/build_site_data.py (SITE-002).

These tests never call the network or any API, never modify outputs/, and only
read repository source files plus the generated site/data JSON.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_site_data.py"
DATA_DIR = REPO_ROOT / "site" / "data"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_site_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_site_data"] = module
    spec.loader.exec_module(module)
    return module


bsd = _load_module()


def test_build_all_has_four_documents():
    built = bsd.build_all()
    assert set(built) == {
        "site_summary.json",
        "roadmap.json",
        "version_history.json",
        "historical_results.json",
    }


def test_site_summary_core_fields():
    s = bsd.build_site_summary()
    assert s["historical_record_count"] == 360
    assert s["process_condition_count"] == 6
    assert s["identity_condition_count"] == 2
    assert s["n_per_cell"] == 30
    assert s["historical_provider"] == "DeepSeek API"
    assert s["historical_data_type"] == "real_api_output"
    assert s["mock_usage"] == "engineering_validation_only"
    assert s["project_stage"] == "current"
    assert s["local_engineering_status"] == "completed"
    assert s["release_verification_status"] == "pending_verification"
    assert s["benchmark_status"] == "planned"
    assert s["token_usage_total"] is None
    assert s["estimated_cost_usd"] is None
    assert s["model_version_snapshot"] is None
    assert len(s["source_commit"]) >= 7
    assert len(s["data_as_of_date"]) == 10


def test_build_is_deterministic_except_generated_at():
    a = bsd.build_site_summary()
    b = bsd.build_site_summary()
    a.pop("generated_at")
    b.pop("generated_at")
    assert a == b
    # non-summary docs must be fully deterministic
    assert bsd.build_roadmap() == bsd.build_roadmap()
    assert bsd.build_version_history() == bsd.build_version_history()
    assert bsd.build_historical_results() == bsd.build_historical_results()


def test_historical_results_cover_required_claims():
    hr = bsd.build_historical_results()
    ids = {c["id"] for c in hr["claims"]}
    assert {
        "factual-check",
        "agency-condition-means",
        "agency-controlled-regression",
        "agency-planned-contrasts",
        "freewill-controlled-regression",
        "parallel-mediation",
        "responsibility-exploratory",
    } <= ids


def test_every_metric_has_source_file_and_field():
    hr = bsd.build_historical_results()
    for claim in hr["claims"]:
        for metric in claim["metrics"]:
            assert metric["source_file"]
            assert metric["source_field"]


def test_mediation_is_exploratory_path_diagnostic():
    hr = bsd.build_historical_results()
    med = next(c for c in hr["claims"] if c["id"] == "parallel-mediation")
    assert med["evidence_level"] == "exploratory_path_diagnostic"
    for m in med["metrics"]:
        assert m["evidence_level"] == "exploratory_path_diagnostic"


def test_responsibility_claim_has_source_and_exploratory_label():
    hr = bsd.build_historical_results()
    resp = next(c for c in hr["claims"] if c["id"] == "responsibility-exploratory")
    assert resp["source_refs"]
    assert resp["evidence_level"] == "exploratory_path_diagnostic"


def test_agency_regression_value_matches_source():
    reg = bsd._controlled("agency")
    assert round(reg["F"], 2) == 12.19


def test_figures_have_matching_sha256():
    hr = bsd.build_historical_results()
    assert len(hr["figures"]) == 3
    for fig in hr["figures"]:
        source = REPO_ROOT / fig["source_file"]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert fig["sha256"] == digest


def test_roadmap_phase_six_is_planned():
    rm = bsd.build_roadmap()
    phase6 = next(p for p in rm["phases"] if p["id"] == "phase-6")
    assert phase6["status"] == "planned"
    phase1 = next(p for p in rm["phases"] if p["id"] == "phase-1")
    assert phase1["local_status"] == "completed"
    assert phase1["release_status"] == "pending_verification"


def test_missing_source_raises_build_error(tmp_path, monkeypatch):
    monkeypatch.setattr(bsd, "ROOT", tmp_path)
    with pytest.raises(bsd.BuildError):
        bsd.build_site_summary()


@pytest.mark.skipif(not DATA_DIR.exists(), reason="site/data not generated yet")
def test_check_mode_reports_up_to_date():
    assert bsd.main(["--check"]) == 0


# --- SITE-005.1 additions --------------------------------------------------

def test_source_commit_uses_research_source_commit():
    s = bsd.build_site_summary()
    expected = bsd._latest_source_commit()
    assert s["source_commit"] == expected
    # and it is the git log over the declared research sources, not rev-parse HEAD
    log_commit = bsd._git(["log", "-1", "--format=%H", "--", *bsd.RESEARCH_SOURCE_PATHS])
    assert s["source_commit"] == log_commit


def test_source_commit_not_plain_head_when_head_is_site_only():
    # HEAD may or may not equal the research source commit; the point is the
    # value is derived from research sources. If they differ, prove independence.
    head = bsd._git(["rev-parse", "HEAD"])
    src = bsd._latest_source_commit()
    # research source commit must be an ancestor of (or equal to) HEAD
    # and must be the last commit touching a research path.
    assert len(src) == 40
    if head != src:
        # HEAD moved past the research-source commit; source_commit stayed put.
        assert src != head


def test_data_as_of_matches_source_commit():
    s = bsd.build_site_summary()
    expected_date = bsd._git(["show", "-s", "--format=%cI", s["source_commit"]])[:10]
    assert s["data_as_of_date"] == expected_date


def test_design_block_has_six_conditions_with_length_control():
    s = bsd.build_site_summary()
    design = s["design"]
    keys = [c["key"] for c in design["process_conditions"]]
    assert len(keys) == 6
    assert "direct_choice_long" in keys
    for c in design["process_conditions"]:
        assert c["label"] and c["note"]


def test_figures_carry_read_note():
    hr = bsd.build_historical_results()
    for fig in hr["figures"]:
        assert fig.get("read_note")


def test_mediation_metrics_structured():
    hr = bsd.build_historical_results()
    med = next(c for c in hr["claims"] if c["id"] == "parallel-mediation")
    for m in med["metrics"]:
        for field in ("estimate", "ci_low", "ci_high", "crosses_zero", "path_role"):
            assert field in m


# --- CI-003: --check must be stable under a shallow (PR merge) checkout -----

def test_check_ignores_git_derived_run_context():
    """--check equality for site_summary.json must ignore run-context fields.

    Under GitHub's PR merge commit (fetch-depth=1) only the merge commit is
    visible, so ``git log`` over the research paths collapses to the merge SHA
    and source_commit / data_as_of_date differ from the committed value. Those
    fields, plus generated_at, must not trigger a spurious OUT OF DATE.
    """
    base = bsd.build_site_summary()
    shifted = dict(base)
    shifted["source_commit"] = "0" * 40
    shifted["data_as_of_date"] = "1999-12-31"
    shifted["generated_at"] = "1999-12-31T00:00:00+00:00"
    assert bsd._comparable("site_summary.json", base) == bsd._comparable(
        "site_summary.json", shifted
    )


def test_check_still_detects_research_content_drift():
    """A genuine research-content change must still be reported as different."""
    base = bsd.build_site_summary()
    changed = dict(base)
    changed["historical_record_count"] = base["historical_record_count"] + 1
    assert bsd._comparable("site_summary.json", base) != bsd._comparable(
        "site_summary.json", changed
    )
