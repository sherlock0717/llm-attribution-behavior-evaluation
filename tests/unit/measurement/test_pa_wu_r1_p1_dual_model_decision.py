"""Static tests for the PA-Wu R1 P1 dual-model selection decision package.

NO real model, NO network, NO API key, NO model output, NO ranking, NO effect
evaluation. These tests exercise the offline validator: exact dual-model
selection, co-primary roles, per-field + per-endpoint-subclaim + per-risk
official evidence mapping (documented computed ONLY from confirmed evidence;
source must list the field/subclaim/risk in supports_fields), provider/source
integrity, dual-provider compatibility binding, deterministic package hash, and
non-interference with the existing preflight package.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import shutil
import subprocess

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

MC_DIR = PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates"
PKG_DIR = MC_DIR / "pa_wu_r1_p1_decision_fill" / "dual_model_selection"
PREFLIGHT_DIR = MC_DIR / "pa_wu_p1_preflight"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PKG_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_module("pa_wu_dual_model_validate", "validate_dual_model_decision.py")


@pytest.fixture(scope="module")
def report(validator):
    return validator.build_report()


def _load(name: str) -> dict:
    with (PKG_DIR / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _src_meta(validator, evidence: dict) -> dict:
    return validator._check_sources(evidence["sources"])


def _model(evidence: dict, model_id: str) -> dict:
    for m in evidence["models"]:
        if m["model_id"] == model_id:
            return m
    raise AssertionError(f"model {model_id} not found")


def _source(evidence: dict, sid: str) -> dict:
    for s in evidence["sources"]:
        if s["source_id"] == sid:
            return s
    raise AssertionError(f"source {sid} not found")


def _isolated_pkg(validator, tmp_path, monkeypatch):
    dst = tmp_path / "dual_model_selection"
    shutil.copytree(PKG_DIR, dst)
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    return dst


def _dir_snapshot(directory) -> dict:
    snap: dict = {}
    if not directory.exists():
        return snap
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            rel = p.relative_to(directory).as_posix()
            snap[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap


# ==========================================================================
# Happy path + report outputs
# ==========================================================================


def test_report_ok(report) -> None:
    assert report["selection_status"] == "human_selected"
    assert report["selected_models"] == ["deepseek-v4-pro", "gpt-5.6-terra"]
    assert report["role_policy"] == "co_primary"
    assert report["empirical_evaluation_status"] == "not_evaluated"
    assert report["migration_status"] == "proposed_not_implemented"
    assert report["operational_readiness"] == "incomplete"
    for mid in ("deepseek-v4-pro", "gpt-5.6-terra"):
        assert "endpoint_type" in report["documented_fields_by_model"][mid]


def test_provider_specific_documented(report) -> None:
    assert report["documented_provider_specific_fields_by_model"]["deepseek-v4-pro"] == ["concurrency_limit"]
    assert report["documented_provider_specific_fields_by_model"]["gpt-5.6-terra"] == ["long_context_pricing_rules"]


def test_direct_and_inference_risks(report) -> None:
    assert set(report["direct_documented_risks_by_model"]["deepseek-v4-pro"]) == {
        "json_empty_content", "thinking_parameters_ignored"
    }
    assert report["grounded_inference_risks_by_model"]["deepseek-v4-pro"] == ["snapshot_update_risk"]
    assert report["direct_documented_risks_by_model"]["gpt-5.6-terra"] == ["reasoning_cost_latency"]
    assert report["grounded_inference_risks_by_model"]["gpt-5.6-terra"] == ["snapshot_update_risk"]


def test_binding_counts_present(report) -> None:
    assert report["source_field_binding_count"] > 0
    assert report["compatibility_dual_provider_binding_count"] >= 1


# ==========================================================================
# Decision-level failures
# ==========================================================================


def test_missing_one_model_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"] = d["selected_models"][:1]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_wrong_model_id_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"][0]["model_id"] = "deepseek-v3"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_role_not_co_primary_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"][0]["role"] = "primary"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_selection_status_unresolved_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selection_status"] = "unresolved"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_empirical_evaluated_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["empirical_evaluation"]["status"] = "evaluated"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_operational_readiness_ready_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["operational_readiness"]["status"] = "ready"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


# ==========================================================================
# Hygiene
# ==========================================================================


def test_winner_field_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    (dst / "comparability_boundaries.yaml").write_text(
        (dst / "comparability_boundaries.yaml").read_text(encoding="utf-8")
        + "\nwinner: gpt-5.6-terra\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_no_placeholders_no_ranking()


def test_placeholder_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    (dst / "parameter_compatibility.yaml").write_text(
        (dst / "parameter_compatibility.yaml").read_text(encoding="utf-8") + "\nfoo: TBD\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_no_placeholders_no_ranking()


# ==========================================================================
# endpoint_type per-subclaim evidence
# ==========================================================================


def test_endpoint_ok(validator) -> None:
    ev = _load("official_evidence.yaml")
    # baseline passes end-to-end
    validator.check_evidence(ev)


def test_deepseek_drop_anthropic_subclaim_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    m["endpoint_type"] = ["openai_chat_completions"]
    del m["field_evidence"]["endpoint_type"]["subclaims"]["anthropic_compatible_api"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_deepseek_anthropic_missing_source_fails(validator) -> None:
    # keep the anthropic subclaim but remove ds_models_and_pricing (its only source)
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    m["field_evidence"]["endpoint_type"]["subclaims"]["anthropic_compatible_api"]["source_ids"] = ["ds_create_chat_completion"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_openai_drop_responses_subclaim_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "gpt-5.6-terra")
    m["endpoint_type"] = ["chat_completions"]
    del m["field_evidence"]["endpoint_type"]["subclaims"]["responses_api"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_openai_subclaim_unsupported_source_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "gpt-5.6-terra")
    # oai_responses_api does NOT support endpoint_type.responses_api
    m["field_evidence"]["endpoint_type"]["subclaims"]["responses_api"]["source_ids"] = ["oai_responses_api"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_endpoint_values_vs_subclaims_mismatch_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    m["endpoint_type"] = ["openai_chat_completions", "anthropic_compatible_api", "extra_endpoint"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


# ==========================================================================
# concurrency_limit sources + exact value
# ==========================================================================


def test_concurrency_two_sources_ok(validator) -> None:
    ev = _load("official_evidence.yaml")
    fe = _model(ev, "deepseek-v4-pro")["field_evidence"]["concurrency_limit"]
    assert set(fe["source_ids"]) == {"ds_models_and_pricing", "ds_rate_limit"}
    validator.check_evidence(ev)  # passes


def test_concurrency_rate_limit_source_ok(validator) -> None:
    # ds_rate_limit now supports concurrency_limit; citing it must NOT fail per se
    ev = _load("official_evidence.yaml")
    _model(ev, "deepseek-v4-pro")["field_evidence"]["concurrency_limit"]["source_ids"] = ["ds_rate_limit"]
    validator.check_evidence(ev)


def test_concurrency_unsupported_source_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    _model(ev, "deepseek-v4-pro")["field_evidence"]["concurrency_limit"]["source_ids"] = ["ds_privacy"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_concurrency_value_not_500_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    _model(ev, "deepseek-v4-pro")["concurrency_limit"] = 400
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_concurrency_both_sources_removed_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    # remove both direct sources from the field evidence -> empty -> fail
    _model(ev, "deepseek-v4-pro")["field_evidence"]["concurrency_limit"]["source_ids"] = []
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


# ==========================================================================
# Fabricated per-field split sources removed
# ==========================================================================


def test_ds_pricing_snapshot_removed() -> None:
    ev = _load("official_evidence.yaml")
    assert all(s["source_id"] != "ds_pricing_snapshot" for s in ev["sources"])


def test_oai_pricing_snapshot_removed() -> None:
    ev = _load("official_evidence.yaml")
    assert all(s["source_id"] != "oai_pricing_snapshot" for s in ev["sources"])


def test_fabricated_source_name_rejected(validator) -> None:
    ev = _load("official_evidence.yaml")
    fake = copy.deepcopy(_source(ev, "ds_models_and_pricing"))
    fake["source_id"] = "ds_pricing_snapshot"
    fake["page_title"] = "Models & Pricing (snapshot)"
    ev["sources"].append(fake)
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_unresolved_fields_cite_real_sources_with_reason(validator) -> None:
    ev = _load("official_evidence.yaml")
    ds = _model(ev, "deepseek-v4-pro")
    assert ds["field_evidence"]["seed_support"]["source_ids"] == ["ds_create_chat_completion"]
    assert ds["field_evidence"]["response_id_support"]["source_ids"] == ["ds_create_chat_completion"]
    assert ds["field_evidence"]["pricing_snapshot_date"]["source_ids"] == ["ds_models_and_pricing"]
    for f in ("seed_support", "response_id_support", "pricing_snapshot_date"):
        assert ds["field_evidence"][f]["reason"].strip()
    validator.check_evidence(ev)


# ==========================================================================
# regional availability sources
# ==========================================================================


def test_regional_correct_sources(validator) -> None:
    ev = _load("official_evidence.yaml")
    assert _model(ev, "deepseek-v4-pro")["field_evidence"]["regional_availability_status"]["source_ids"] == ["ds_open_platform_terms"]
    assert _model(ev, "gpt-5.6-terra")["field_evidence"]["regional_availability_status"]["source_ids"] == ["oai_supported_countries"]
    validator.check_evidence(ev)


def test_deepseek_regional_citing_rate_limit_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    _model(ev, "deepseek-v4-pro")["field_evidence"]["regional_availability_status"]["source_ids"] = ["ds_rate_limit"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_openai_regional_citing_models_index_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    _model(ev, "gpt-5.6-terra")["field_evidence"]["regional_availability_status"]["source_ids"] = ["oai_models_index"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_cdn_domain_whitelisted(validator) -> None:
    assert "cdn.deepseek.com" in validator.ALLOWED_SOURCE_DOMAINS


def test_cdn_domain_missing_fails(validator, monkeypatch) -> None:
    ev = _load("official_evidence.yaml")
    monkeypatch.setattr(
        validator, "ALLOWED_SOURCE_DOMAINS",
        tuple(d for d in validator.ALLOWED_SOURCE_DOMAINS if d != "cdn.deepseek.com"),
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


# ==========================================================================
# risk claim_type
# ==========================================================================


def test_illegal_claim_type_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    next(r for r in m["known_risks"] if r["risk_id"] == "json_empty_content")["claim_type"] = "guess"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_snapshot_risk_is_inference(validator) -> None:
    ev = _load("official_evidence.yaml")
    for mid in ("deepseek-v4-pro", "gpt-5.6-terra"):
        risk = next(r for r in _model(ev, mid)["known_risks"] if r["risk_id"] == "snapshot_update_risk")
        assert risk["claim_type"] == "methodological_inference_from_official_documentation"


# ==========================================================================
# General evidence integrity
# ==========================================================================


def test_duplicate_source_id_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    ev["sources"].append(copy.deepcopy(ev["sources"][1]))
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_source_illegal_supports_field_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    _source(ev, "ds_models_and_pricing")["supports_fields"].append("not_a_real_field")
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_documented_only_from_field_evidence(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    m["field_evidence"]["context_window"] = {
        "status": "requires_interface_check",
        "source_ids": ["ds_models_and_pricing"],
        "reason": "downgraded",
    }
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_official_source_ids_superset(validator) -> None:
    ev = _load("official_evidence.yaml")
    m = _model(ev, "deepseek-v4-pro")
    m["official_source_ids"] = [s for s in m["official_source_ids"] if s != "ds_open_platform_terms"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


# ==========================================================================
# Compatibility
# ==========================================================================


def test_compat_ok(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    summary, dual = validator.check_parameter_compatibility(_load("parameter_compatibility.yaml"), meta)
    assert dual >= 1
    assert sum(summary.values()) == len(validator.REQUIRED_MAPPING_PARAMS)


def test_compat_exact_param_set(validator) -> None:
    got = {mp["canonical_research_parameter"] for mp in _load("parameter_compatibility.yaml")["mappings"]}
    assert got == set(validator.REQUIRED_MAPPING_PARAMS)
    assert "context_window" in got


def test_compat_endpoint_only_deepseek_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    compat = _load("parameter_compatibility.yaml")
    ep = next(mp for mp in compat["mappings"] if mp["canonical_research_parameter"] == "endpoint")
    ep["evidence_source_ids"] = ["ds_create_chat_completion", "ds_models_and_pricing"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat, meta)


def test_compat_context_window_only_openai_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    compat = _load("parameter_compatibility.yaml")
    cw = next(mp for mp in compat["mappings"] if mp["canonical_research_parameter"] == "context_window")
    cw["evidence_source_ids"] = ["oai_model_page"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat, meta)


def test_compat_source_not_supporting_field_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    compat = _load("parameter_compatibility.yaml")
    cw = next(mp for mp in compat["mappings"] if mp["canonical_research_parameter"] == "context_window")
    cw["evidence_source_ids"] = ["ds_privacy", "oai_model_page"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat, meta)


def test_compat_unknown_source_id_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    compat = _load("parameter_compatibility.yaml")
    compat["mappings"][0]["evidence_source_ids"] = ["nope_source"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat, meta)


def test_compat_missing_context_window_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    meta = _src_meta(validator, ev)
    compat = _load("parameter_compatibility.yaml")
    compat["mappings"] = [
        mp for mp in compat["mappings"]
        if mp["canonical_research_parameter"] != "context_window"
    ]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat, meta)


def test_migration_marked_implemented_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    plan = dst / "preflight_schema_migration_plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "migration_status: proposed_not_implemented",
            "migration_status: implemented",
        ),
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_migration_plan()


# ==========================================================================
# Package hash + isolation
# ==========================================================================


def test_package_hash_deterministic(validator) -> None:
    assert validator.compute_package_hash() == validator.compute_package_hash()


def test_package_hash_changes_on_evidence(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    h1 = validator.compute_package_hash()
    ev = dst / "official_evidence.yaml"
    ev.write_text(ev.read_text(encoding="utf-8") + "\n# tweak\n", encoding="utf-8")
    assert validator.compute_package_hash() != h1


def test_package_hash_changes_on_compat(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    h1 = validator.compute_package_hash()
    cp = dst / "parameter_compatibility.yaml"
    cp.write_text(cp.read_text(encoding="utf-8") + "\n# tweak\n", encoding="utf-8")
    assert validator.compute_package_hash() != h1


def _repo_status(paths) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    ).stdout


def test_preflight_dir_untouched(validator) -> None:
    rel = "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight"
    snap_before = _dir_snapshot(PREFLIGHT_DIR)
    status_before = _repo_status([rel])
    validator.build_report()
    assert _dir_snapshot(PREFLIGHT_DIR) == snap_before
    assert _repo_status([rel]) == status_before


def test_validator_does_not_read_authorization(validator) -> None:
    validator.check_no_authorization_access()
    src = (PKG_DIR / "validate_dual_model_decision.py").read_text(encoding="utf-8")
    auth_yaml = "authorization" + "_gate.yaml"
    assert auth_yaml not in src
    assert "pa_wu_p1_preflight" not in src


def test_no_legacy_selected_model_singular() -> None:
    text = (PKG_DIR / "dual_model_decision.yaml").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        assert not stripped.startswith("selected_model:")
