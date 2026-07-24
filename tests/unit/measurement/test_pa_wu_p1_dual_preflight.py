"""Static tests for the PA-Wu R1 P1 DUAL-model preflight schema migration.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the offline validator: dual-model set, selection/freeze
separation, provider adapters + semantic invariants, shared prompt boundary,
per-model sampling/budget, aggregate relations, dual-model gates + all-or-nothing
authorization, per-model/aggregate/package hashes, and non-interference with the
original single-model preflight package and the merged dual-model decision pkg.
"""

from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

MC_DIR = PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates"
PKG_DIR = MC_DIR / "pa_wu_p1_dual_preflight"
SINGLE_DIR = MC_DIR / "pa_wu_p1_preflight"
DECISION_DIR = MC_DIR / "pa_wu_r1_p1_decision_fill" / "dual_model_selection"
MODELS = ("deepseek-v4-pro", "gpt-5.6-terra")


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PKG_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_module("pa_wu_dual_preflight_validate", "validate_dual_preflight.py")


@pytest.fixture(scope="module")
def report(validator):
    return validator.build_report()


def _load(name: str) -> dict:
    with (PKG_DIR / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


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
# Baseline
# ==========================================================================


def test_report_baseline(report) -> None:
    assert report["migration_status"] == "schema_implemented_not_frozen"
    assert report["selected_models"] == list(MODELS)
    assert report["role_policy"] == "co_primary"
    assert report["dual_model_decision_verified"] is True
    assert report["all_models_frozen"] is False
    assert report["provider_adapters_frozen"] is False
    assert report["prompt_frozen"] is False
    assert report["all_model_sampling_frozen"] is False
    assert report["all_model_budgets_approved"] is False
    assert report["authorization_status"] == "blocked"
    assert report["real_model_execution_authorized"] is False
    assert report["preflight_status"] == "blocked"
    assert report["p1_execution_status"] == "blocked"


# ==========================================================================
# A. dual-model set
# ==========================================================================


def test_missing_model_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["selected_models"] = d["selected_models"][:1]
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_extra_model_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["selected_models"].append({"provider": "anthropic", "model_id": "c", "role": "co_primary"})
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_wrong_model_id_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["selected_models"][0]["model_id"] = "deepseek-v3"
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_wrong_provider_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["selected_models"][0]["provider"] = "openai"
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_role_not_co_primary_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["selected_models"][0]["role"] = "primary"
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_adapter_fallback_key_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["deepseek-v4-pro"]["fallback"] = "gpt-5.6-terra"
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_primary_secondary_key_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["gpt-5.6-terra"]["primary_model"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


# ==========================================================================
# B. selection vs freeze separation
# ==========================================================================


def _frozen_decision(mid: str, provider: str) -> dict:
    return {
        "freeze_status": "frozen",
        "provider": provider,
        "model_id": mid,
        "role": "co_primary",
        "exact_model_version_or_snapshot": "2026-07-01",
        "endpoint_type": "chat",
        "access_method": "https_api",
        "context_window_requirement": 8192,
        "structured_output_support": "documented",
        "deterministic_seed_support": "false",
        "temperature_support": "documented",
        "response_id_available": "documented",
        "provider_retention_policy_reviewed": True,
        "pricing_snapshot_date": "2026-07-01",
        "pricing_source_recorded": "https://x",
        "regional_availability_reviewed": True,
        "terms_of_use_reviewed": True,
        "decided_by": "researcher",
        "decided_at": "2026-07-02",
        "source_references": ["https://x/docs"],
    }


def test_human_selected_unresolved_ok(validator) -> None:
    d = _load("model_selection_decision.yaml")
    pm = validator.check_model_selection(d)
    assert pm == {m: False for m in MODELS}


def test_human_selected_not_auto_frozen(report) -> None:
    # selection is human_selected but all_models_frozen stays false
    assert report["all_models_frozen"] is False


def test_one_frozen_one_unresolved_false(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["decisions"]["deepseek-v4-pro"] = _frozen_decision("deepseek-v4-pro", "deepseek")
    d["all_models_frozen"] = False  # still not all
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is True
    assert pm["gpt-5.6-terra"] is False


def test_missing_snapshot_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["exact_model_version_or_snapshot"] = None
    d["decisions"]["deepseek-v4-pro"] = dec
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is False


def test_incomplete_review_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["terms_of_use_reviewed"] = False
    d["decisions"]["deepseek-v4-pro"] = dec
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is False


def test_both_frozen_all_models_frozen_true(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["decisions"]["deepseek-v4-pro"] = _frozen_decision("deepseek-v4-pro", "deepseek")
    d["decisions"]["gpt-5.6-terra"] = _frozen_decision("gpt-5.6-terra", "openai")
    d["all_models_frozen"] = True
    pm = validator.check_model_selection(d)
    assert all(pm.values())


# ==========================================================================
# C. adapter
# ==========================================================================


def test_adapter_missing_model_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    del a["adapters"]["gpt-5.6-terra"]
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_semantic_invariant_false_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["semantic_invariants"]["item_wording_unchanged"] = False
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_frozen_adapter_missing_hash_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = a["adapters"]["deepseek-v4-pro"]
    for f in ("request_endpoint_mapping", "request_schema_mapping", "structured_output_mapping",
              "response_parser_mapping", "token_usage_mapping", "response_id_mapping"):
        ad[f] = "map"
    ad["frozen"] = True
    ad["adapter_sha256"] = None  # missing hash
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_provider_mismatch_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["deepseek-v4-pro"]["provider"] = "openai"
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


# ==========================================================================
# D. sampling
# ==========================================================================


def _frozen_sampling(seed_supported: bool, seed, rc: int = 24) -> dict:
    return {
        "temperature": 0.0, "top_p": 1.0, "max_output_tokens": 512,
        "seed": seed, "seed_supported": seed_supported,
        "seed_is_determinism_guarantee": False,
        "planned_request_count": rc, "concurrency": 2, "request_timeout_seconds": 60,
        "frozen": True,
    }


def test_sampling_request_count_calc(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = {"planned_case_count": 8, "repeats_per_case": 3,
                          "scenario_order_policy": "fixed", "item_order_policy": "p0",
                          "repeat_index_policy": "zero"}
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["aggregate"] = {"total_planned_requests": 48}
    s["all_model_sampling_frozen"] = True
    pm = validator.check_sampling(s)
    assert all(pm.values())


def test_sampling_aggregate_sum(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = {"planned_case_count": 8, "repeats_per_case": 3,
                          "scenario_order_policy": "fixed", "item_order_policy": "p0",
                          "repeat_index_policy": "zero"}
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["aggregate"] = {"total_planned_requests": 999}  # wrong sum
    s["all_model_sampling_frozen"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_sampling(s)


def test_sampling_one_missing_not_frozen(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = {"planned_case_count": 8, "repeats_per_case": 3,
                          "scenario_order_policy": "fixed", "item_order_policy": "p0",
                          "repeat_index_policy": "zero"}
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    # gpt left unfrozen (from baseline) -> not all
    s["all_model_sampling_frozen"] = False
    pm = validator.check_sampling(s)
    assert pm["deepseek-v4-pro"] is True
    assert pm["gpt-5.6-terra"] is False


def test_sampling_seed_false_requires_null(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = {"planned_case_count": 8, "repeats_per_case": 3,
                          "scenario_order_policy": "fixed", "item_order_policy": "p0",
                          "repeat_index_policy": "zero"}
    bad = _frozen_sampling(False, 123, 24)  # seed_supported false but seed set
    s["models"]["deepseek-v4-pro"] = bad
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    pm = validator.check_sampling(s)
    assert pm["deepseek-v4-pro"] is False


# ==========================================================================
# E. budget
# ==========================================================================


def test_budget_deepseek_concurrency_over_500_fails(validator) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"]["concurrency_limit"] = 501
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"])


def test_budget_cross_provider_price_source_fails(validator) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"]["pricing_evidence_reference"]["source_ids"] = ["oai_model_page"]
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"])


def test_budget_one_unapproved_overall_false(validator) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    pm = validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"])
    assert pm == {m: False for m in MODELS}


# ==========================================================================
# F. gates & authorization
# ==========================================================================


def test_required_gates_exact(validator) -> None:
    auth = _load("authorization_gate.yaml")
    validator.check_required_gates_exact(auth)  # ok
    auth["required_gates"] = auth["required_gates"][:-1]
    with pytest.raises(validator.DualPreflightError):
        validator.check_required_gates_exact(auth)


def test_blocked_with_authorized_by_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorized_by"] = "someone"
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, False)
    with pytest.raises(validator.DualPreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_authorized_requires_all_gates(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = "pi"
    auth["authorized_at"] = "2026-07-02"
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, True)
    gate_status["prompt_frozen"] = False
    with pytest.raises(validator.DualPreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_authorized_all_gates_ok(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = "pi"
    auth["authorized_at"] = "2026-07-02"
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, True)
    assert validator.check_authorization_state_machine(auth, gate_status) == "authorized"


def test_baseline_blocking_gates(report) -> None:
    # baseline: many gates blocking, not ready for authorization
    assert report["ready_for_authorization"] is False
    assert "all_models_frozen" in report["blocking_gates"]
    assert "route_frozen" in report["resolved_gates"]


# ==========================================================================
# G. hash & isolation
# ==========================================================================


def _contracts(validator) -> dict:
    return {n: _load(n) for n in validator.CONTRACT_FILES}


def test_per_model_hash_deterministic(validator) -> None:
    c = _contracts(validator)
    assert validator.compute_per_model_contract_hashes(c) == validator.compute_per_model_contract_hashes(c)


def test_changing_deepseek_changes_only_its_hash(validator) -> None:
    c = _contracts(validator)
    h1 = validator.compute_per_model_contract_hashes(c)
    agg1 = validator.compute_aggregate_contract_hash(c)
    c["sampling_and_repeat_contract.yaml"]["models"]["deepseek-v4-pro"]["temperature"] = 0.7
    h2 = validator.compute_per_model_contract_hashes(c)
    agg2 = validator.compute_aggregate_contract_hash(c)
    assert h2["deepseek-v4-pro"] != h1["deepseek-v4-pro"]
    assert h2["gpt-5.6-terra"] == h1["gpt-5.6-terra"]
    assert agg2 != agg1


def test_changing_openai_changes_only_its_hash(validator) -> None:
    c = _contracts(validator)
    h1 = validator.compute_per_model_contract_hashes(c)
    c["budget_and_rate_limit_contract.yaml"]["models"]["gpt-5.6-terra"]["estimated_cost"] = 10
    h2 = validator.compute_per_model_contract_hashes(c)
    assert h2["gpt-5.6-terra"] != h1["gpt-5.6-terra"]
    assert h2["deepseek-v4-pro"] == h1["deepseek-v4-pro"]


def test_shared_prompt_change_affects_aggregate(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    per1 = validator.compute_per_model_contract_hashes(c)
    c["prompt_freeze_contract.yaml"]["segments"]["system_prompt"]["owner"] = "x"
    agg2 = validator.compute_aggregate_contract_hash(c)
    per2 = validator.compute_per_model_contract_hashes(c)
    assert agg2 != agg1
    # per-model hashes unaffected (shared prompt is not a per-model sub-contract)
    assert per2 == per1


def test_package_hash_deterministic(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    assert validator.compute_package_hash(c, m) == validator.compute_package_hash(c, m)


def test_package_hash_sensitive(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    c = {n: yaml.safe_load((dst / n).read_text(encoding="utf-8")) for n in validator.CONTRACT_FILES}
    m = yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8"))
    h1 = validator.compute_package_hash(c, m)
    vp = dst / "validate_dual_preflight.py"
    vp.write_text(vp.read_text(encoding="utf-8") + "\n# x\n", encoding="utf-8")
    assert validator.compute_package_hash(c, m) != h1


def _repo_status(paths) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    ).stdout


def test_original_single_preflight_untouched(validator) -> None:
    rel = "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight"
    snap = _dir_snapshot(SINGLE_DIR)
    status = _repo_status([rel])
    validator.build_report()
    assert _dir_snapshot(SINGLE_DIR) == snap
    assert _repo_status([rel]) == status


def test_dual_decision_package_untouched(validator) -> None:
    rel = "tasks/attribution_behavior/measurement_candidates/pa_wu_r1_p1_decision_fill/dual_model_selection"
    snap = _dir_snapshot(DECISION_DIR)
    status = _repo_status([rel])
    validator.build_report()
    assert _dir_snapshot(DECISION_DIR) == snap
    assert _repo_status([rel]) == status


def test_validator_no_network_no_sdk_no_secret(validator) -> None:
    validator.check_validator_self_scan()
    src = (PKG_DIR / "validate_dual_preflight.py").read_text(encoding="utf-8")
    for banned in ("import requests", "import httpx", "import openai", "import anthropic",
                   "import socket", "\nimport os\n"):
        assert banned not in src


def test_no_singular_selected_model() -> None:
    text = (PKG_DIR / "model_selection_decision.yaml").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        assert not stripped.startswith("selected_model:")


def test_manifest_source_hashes_recorded(validator) -> None:
    m = validator.check_manifest()
    sp = m["source_packages"]
    assert sp["single_model_preflight"]["contract_hash"] == validator.SINGLE_PREFLIGHT_CONTRACT_HASH
    assert sp["single_model_preflight"]["package_hash"] == validator.SINGLE_PREFLIGHT_PACKAGE_HASH
    assert sp["dual_model_decision"]["package_hash"] == validator.DUAL_DECISION_PACKAGE_HASH
