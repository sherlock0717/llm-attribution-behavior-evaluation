"""Static tests for the PA-Wu R1 P1 DUAL-model preflight schema migration.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the HARDENED offline validator: dual-model set, selection/freeze
separation with strict field typing + ISO dates, provider adapters with REAL
recomputed SHA-256 + exact key sets, shared prompt with real content/bundle
hashes, per-model sampling finite ranges, budget cost formulas + aggregate,
dual-model gates + all-or-nothing authorization, per-model/shared/aggregate/
package hashes, structured branch-CI evidence, AST write/exec detection, and
non-interference with the original single-model preflight package and the
merged dual-model decision package.
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
# B. selection vs freeze separation + strict field typing
# ==========================================================================


def _frozen_decision(mid: str, provider: str) -> dict:
    """Correctly typed frozen decision: real bools, valid ISO dates, positive int
    context window, non-placeholder strings, unique source refs."""
    return {
        "freeze_status": "frozen",
        "provider": provider,
        "model_id": mid,
        "role": "co_primary",
        "exact_model_version_or_snapshot": "2026-07-01-snap",
        "endpoint_type": "chat_completions",
        "access_method": "https_api",
        "context_window_requirement": 8192,
        "structured_output_support": True,
        "deterministic_seed_support": False,
        "temperature_support": True,
        "response_id_available": True,
        "provider_retention_policy_reviewed": True,
        "pricing_snapshot_date": "2026-07-01",
        "pricing_source_recorded": "https://example/pricing",
        "regional_availability_reviewed": True,
        "terms_of_use_reviewed": True,
        "decided_by": "researcher",
        "decided_at": "2026-07-02",
        "source_references": ["https://example/docs", "https://example/pricing"],
    }


def test_human_selected_unresolved_ok(validator) -> None:
    d = _load("model_selection_decision.yaml")
    pm = validator.check_model_selection(d)
    assert pm == {m: False for m in MODELS}


def test_human_selected_not_auto_frozen(report) -> None:
    assert report["all_models_frozen"] is False


def test_one_frozen_one_unresolved_false(validator) -> None:
    d = _load("model_selection_decision.yaml")
    d["decisions"]["deepseek-v4-pro"] = _frozen_decision("deepseek-v4-pro", "deepseek")
    d["all_models_frozen"] = False
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


def test_string_bool_field_not_frozen(validator) -> None:
    # "true"/"false"/"documented" strings are NOT accepted for bool fields.
    for val in ("true", "false", "documented"):
        d = _load("model_selection_decision.yaml")
        dec = _frozen_decision("deepseek-v4-pro", "deepseek")
        dec["structured_output_support"] = val
        d["decisions"]["deepseek-v4-pro"] = dec
        pm = validator.check_model_selection(d)
        assert pm["deepseek-v4-pro"] is False, val


def test_invalid_iso_date_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["pricing_snapshot_date"] = "2026-13-40"  # not a real date
    d["decisions"]["deepseek-v4-pro"] = dec
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is False


def test_context_window_bool_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["context_window_requirement"] = True  # bool is not a positive int
    d["decisions"]["deepseek-v4-pro"] = dec
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is False


def test_context_window_string_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["context_window_requirement"] = "8192"  # string not accepted
    d["decisions"]["deepseek-v4-pro"] = dec
    pm = validator.check_model_selection(d)
    assert pm["deepseek-v4-pro"] is False


def test_fallback_field_in_decision_fails(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["fallback"] = "gpt-5.6-terra"
    d["decisions"]["deepseek-v4-pro"] = dec
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d)


def test_duplicate_source_references_not_frozen(validator) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["source_references"] = ["https://x", "https://x"]  # duplicate
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
# C. adapter real SHA-256
# ==========================================================================


def _frozen_adapter(validator, provider: str) -> dict:
    a = {
        "provider": provider,
        "request_endpoint_mapping": {"path": "/v1/chat"},
        "request_schema_mapping": {"messages": "messages"},
        "structured_output_mapping": {"schema": "json"},
        "response_parser_mapping": {"choices": "choices"},
        "token_usage_mapping": {"usage": "usage"},
        "response_id_mapping": {"id": "id"},
        "adapter_sha256": None,
        "frozen": True,
    }
    a["adapter_sha256"] = validator.compute_adapter_sha256(a)
    return a


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


def test_adapter_provider_mismatch_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["deepseek-v4-pro"]["provider"] = "openai"
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_non64_hash_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["adapter_sha256"] = "abc123"  # not 64 hex
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_hash_mismatch_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["adapter_sha256"] = "0" * 64  # 64 hex but wrong content
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_mapping_changed_without_hash_update_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["request_endpoint_mapping"] = {"path": "/v2/chat"}  # changed, stale hash
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_scenario_rewrite_field_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["scenario_rewrite"] = True  # extra semantic-rewrite field
    ad["adapter_sha256"] = validator.compute_adapter_sha256(ad)
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_adapter_compatibility_path_change_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["compatibility_reference"]["path"] = "some/other/path.yaml"
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_two_synthetic_adapters_freeze(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["deepseek-v4-pro"] = _frozen_adapter(validator, "deepseek")
    a["adapters"]["gpt-5.6-terra"] = _frozen_adapter(validator, "openai")
    a["all_adapters_frozen"] = True
    pm = validator.check_provider_adapters(a)
    assert all(pm.values())


# ==========================================================================
# D. prompt real hashes
# ==========================================================================

_ITEM_BUNDLE = (
    "pa_wu_p0/items_pa_2024.yaml",
    "pa_wu_p0/items_wu_shen_2026.yaml",
    "pa_wu_p0/forms.yaml",
)


def _inline_segment(text: str) -> dict:
    return {
        "content": text,
        "template_reference": None,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "frozen": True,
        "owner": "researcher",
        "change_requires_new_run_version": True,
    }


def _frozen_prompt(validator) -> dict:
    p = _load("prompt_freeze_contract.yaml")
    for name in ("system_prompt", "task_instruction", "scenario_block",
                 "identity_block", "response_schema"):
        p["segments"][name] = _inline_segment(f"content-{name}")
    bundle = list(_ITEM_BUNDLE)
    p["segments"]["item_block"] = {
        "content": None,
        "template_reference": None,
        "source_bundle": bundle,
        "sha256": validator.source_bundle_hash(bundle),
        "frozen": True,
        "owner": "researcher",
        "change_requires_new_run_version": True,
    }
    return p


def test_prompt_baseline_not_frozen(validator) -> None:
    assert validator.check_prompt(_load("prompt_freeze_contract.yaml")) is False


def test_prompt_all_frozen(validator) -> None:
    assert validator.check_prompt(_frozen_prompt(validator)) is True


def test_prompt_fake_sha_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["sha256"] = "z" * 64  # not hex
    assert validator.check_prompt(p) is False


def test_prompt_content_changed_stale_sha_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["content"] = "mutated content"  # sha now stale
    assert validator.check_prompt(p) is False


def test_prompt_template_escape_fails(validator) -> None:
    p = _frozen_prompt(validator)
    seg = {
        "content": None,
        "template_reference": "../../../etc/passwd",
        "sha256": "a" * 64,
        "frozen": True,
        "owner": "researcher",
        "change_requires_new_run_version": True,
    }
    p["segments"]["system_prompt"] = seg
    assert validator.check_prompt(p) is False


def test_prompt_item_bundle_missing_one_fails(validator) -> None:
    p = _frozen_prompt(validator)
    short = list(_ITEM_BUNDLE)[:2]
    p["segments"]["item_block"]["source_bundle"] = short
    p["segments"]["item_block"]["sha256"] = validator.source_bundle_hash(short)
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_item_bundle_extra_fails(validator) -> None:
    p = _frozen_prompt(validator)
    extra = list(_ITEM_BUNDLE) + ["pa_wu_p0/forms.yaml"]
    p["segments"]["item_block"]["source_bundle"] = extra
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_item_bundle_reordered_fails(validator) -> None:
    p = _frozen_prompt(validator)
    reordered = [_ITEM_BUNDLE[1], _ITEM_BUNDLE[0], _ITEM_BUNDLE[2]]
    p["segments"]["item_block"]["source_bundle"] = reordered
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_item_bundle_real_hash_ok(validator) -> None:
    p = _frozen_prompt(validator)
    # exact fixed-order bundle with real recomputed hash -> frozen.
    assert validator.check_prompt(p) is True


def test_prompt_per_model_semantic_field_forbidden(validator) -> None:
    p = _frozen_prompt(validator)
    p["constraints"]["per_model_semantic_prompt_forbidden"] = False
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


# ==========================================================================
# E. sampling finite ranges
# ==========================================================================


def _shared(pc=8, rp=3) -> dict:
    return {"planned_case_count": pc, "repeats_per_case": rp,
            "scenario_order_policy": "fixed", "item_order_policy": "p0",
            "repeat_index_policy": "zero"}


def _frozen_sampling(seed_supported: bool, seed, rc: int = 24, concurrency: int = 2) -> dict:
    return {
        "temperature": 0.0, "top_p": 1.0, "max_output_tokens": 512,
        "seed": seed, "seed_supported": seed_supported,
        "seed_is_determinism_guarantee": False,
        "planned_request_count": rc, "concurrency": concurrency,
        "request_timeout_seconds": 60, "frozen": True,
    }


def test_sampling_request_count_calc(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["aggregate"] = {"total_planned_requests": 48}
    s["all_model_sampling_frozen"] = True
    assert all(validator.check_sampling(s).values())


def test_sampling_aggregate_sum_wrong_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["aggregate"] = {"total_planned_requests": 999}
    s["all_model_sampling_frozen"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_sampling(s)


def test_sampling_seed_false_requires_null(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, 123, 24)  # seed set but unsupported
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    pm = validator.check_sampling(s)
    assert pm["deepseek-v4-pro"] is False


def test_sampling_negative_temperature_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["temperature"] = -0.1
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_string_temperature_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["temperature"] = "0.0"
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_bool_max_tokens_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["max_output_tokens"] = True
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_nan_timeout_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["request_timeout_seconds"] = float("nan")
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_top_p_out_of_range_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["top_p"] = 1.5  # > 1
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_concurrency_over_requests_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24, concurrency=100)  # > planned_request_count
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


def test_sampling_empty_order_policy_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    sd = _shared()
    sd["scenario_order_policy"] = None
    s["shared_design"] = sd
    s["models"]["deepseek-v4-pro"] = _frozen_sampling(False, None, 24)
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


# ==========================================================================
# F. budget cost formulas + aggregate
# ==========================================================================


def _pricing_inputs() -> dict:
    return {
        "uncached_input_price_per_million": 1.0,
        "cached_input_price_per_million": 0.5,
        "output_price_per_million": 2.0,
        "estimated_cached_input_tokens": 400_000,
        "estimated_uncached_input_tokens": 600_000,
    }


def _budget_model(mid: str, rc: int = 24) -> dict:
    pi = _pricing_inputs()
    out_tokens = 300_000
    cost = (
        (pi["estimated_uncached_input_tokens"] / 1e6) * pi["uncached_input_price_per_million"]
        + (pi["estimated_cached_input_tokens"] / 1e6) * pi["cached_input_price_per_million"]
        + (out_tokens / 1e6) * pi["output_price_per_million"]
    )
    src = "ds_models_and_pricing" if mid == "deepseek-v4-pro" else "oai_model_page"
    return {
        "currency": "USD",
        "pricing_unit": "per_million_tokens",
        "pricing_evidence_reference": {
            "package_path": (
                "tasks/attribution_behavior/measurement_candidates/"
                "pa_wu_r1_p1_decision_fill/dual_model_selection"
            ),
            "source_ids": [src],
        },
        "pricing_snapshot_date": "2026-07-01",
        "pricing_inputs": pi,
        "estimated_input_tokens": 1_000_000,
        "estimated_output_tokens": out_tokens,
        "planned_request_count": rc,
        "estimated_cost": cost,
        "maximum_model_budget": 100.0,
        "warning_threshold": 80.0,
        "concurrency_limit": 10,
        "requests_per_minute_limit": 60,
        "tokens_per_minute_limit": 1_000_000,
        "budget_owner": "pi",
        "budget_approved": True,
        "approval_timestamp": "2026-07-02",
    }


def _approved_budget(rc: int = 24) -> dict:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"] = _budget_model("deepseek-v4-pro", rc)
    b["models"]["gpt-5.6-terra"] = _budget_model("gpt-5.6-terra", rc)
    cost = b["models"]["deepseek-v4-pro"]["estimated_cost"] * 2
    b["aggregate"] = {
        "currency": "USD",
        "maximum_total_budget": 200.0,
        "warning_total_threshold": 150.0,
        "estimated_total_cost": cost,
        "total_planned_requests": rc * 2,
        "aggregate_budget_owner": "pi",
        "aggregate_budget_approved": True,
        "aggregate_approval_timestamp": "2026-07-02",
    }
    b["all_model_budgets_approved"] = True
    return b


def _sampling_models(rc: int = 24) -> dict:
    return {m: {"planned_request_count": rc, "concurrency": 2} for m in MODELS}


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


def test_budget_full_approval_ok(validator) -> None:
    b = _approved_budget()
    pm = validator.check_budget(b, _sampling_models())
    assert all(pm.values())


def test_budget_empty_source_ids_fails(validator) -> None:
    b = _approved_budget()
    b["models"]["deepseek-v4-pro"]["pricing_evidence_reference"]["source_ids"] = []
    b["all_model_budgets_approved"] = False  # keep declared == derived
    pm = validator.check_budget(b, _sampling_models())
    assert pm["deepseek-v4-pro"] is False


def test_budget_string_cost_fails(validator) -> None:
    b = _approved_budget()
    b["models"]["deepseek-v4-pro"]["estimated_cost"] = "10"
    b["all_model_budgets_approved"] = False
    pm = validator.check_budget(b, _sampling_models())
    assert pm["deepseek-v4-pro"] is False


def test_budget_negative_cost_fails(validator) -> None:
    b = _approved_budget()
    b["models"]["deepseek-v4-pro"]["estimated_cost"] = -1.0
    b["all_model_budgets_approved"] = False
    pm = validator.check_budget(b, _sampling_models())
    assert pm["deepseek-v4-pro"] is False


def test_budget_formula_inconsistent_fails(validator) -> None:
    b = _approved_budget()
    b["models"]["deepseek-v4-pro"]["estimated_cost"] = 999.0  # not matching pricing_inputs
    b["all_model_budgets_approved"] = False
    pm = validator.check_budget(b, _sampling_models())
    assert pm["deepseek-v4-pro"] is False


def test_budget_warning_over_hard_limit_fails(validator) -> None:
    b = _approved_budget()
    b["models"]["deepseek-v4-pro"]["warning_threshold"] = 500.0  # > max
    b["all_model_budgets_approved"] = False
    pm = validator.check_budget(b, _sampling_models())
    assert pm["deepseek-v4-pro"] is False


def test_budget_aggregate_missing_model_fails(validator) -> None:
    b = _approved_budget()
    # aggregate cost only counts one model -> mismatch
    b["aggregate"]["estimated_total_cost"] = b["models"]["deepseek-v4-pro"]["estimated_cost"]
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, _sampling_models())


# ==========================================================================
# G. retry / logging / stop hardening
# ==========================================================================


def _frozen_retry() -> dict:
    r = _load("retry_and_recovery_contract.yaml")
    r["shared_policy"]["max_attempts"] = 3
    r["shared_policy"]["exponential_backoff"] = {"base": 2, "cap": 30}
    for mid, prov in (("deepseek-v4-pro", "deepseek"), ("gpt-5.6-terra", "openai")):
        r["models"][mid] = {
            "provider": prov,
            "provider_error_taxonomy": {"429": "rate_limit"},
            "retryable_codes": ["429", "503"],
            "non_auto_retryable_codes": ["400", "401"],
            "frozen": True,
        }
    r["all_model_retry_policies_frozen"] = True
    return r


def test_retry_baseline_not_frozen(validator) -> None:
    assert validator.check_retry(_load("retry_and_recovery_contract.yaml")) == {m: False for m in MODELS}


def test_retry_full_frozen(validator) -> None:
    assert all(validator.check_retry(_frozen_retry()).values())


def test_retry_overlapping_lists_not_frozen(validator) -> None:
    r = _frozen_retry()
    r["models"]["deepseek-v4-pro"]["non_auto_retryable_codes"] = ["429"]  # overlaps retryable
    r["all_model_retry_policies_frozen"] = False  # keep declared == derived
    assert validator.check_retry(r)["deepseek-v4-pro"] is False


def test_retry_duplicate_codes_not_frozen(validator) -> None:
    r = _frozen_retry()
    r["models"]["deepseek-v4-pro"]["retryable_codes"] = ["429", "429"]
    r["all_model_retry_policies_frozen"] = False
    assert validator.check_retry(r)["deepseek-v4-pro"] is False


def _frozen_logging() -> dict:
    lg = _load("provenance_and_logging_contract.yaml")
    lg["frozen"] = True
    lg["frozen_by"] = "pi"
    lg["logging_contract_hash"] = "abc123"
    lg["logging_contract_version"] = "v1"
    lg["privacy_review"] = {"status": "completed", "reviewed_by": "dpo", "reviewed_at": "2026-07-02"}
    return lg


def test_logging_baseline_not_frozen(validator) -> None:
    assert validator.check_logging_frozen(_load("provenance_and_logging_contract.yaml")) is False


def test_logging_full_frozen(validator) -> None:
    assert validator.check_logging_frozen(_frozen_logging()) is True


def test_logging_missing_dual_field_fails(validator) -> None:
    lg = _frozen_logging()
    lg["dual_model_required_log_fields"] = lg["dual_model_required_log_fields"][:-1]
    with pytest.raises(validator.DualPreflightError):
        validator.check_logging_frozen(lg)


def test_logging_duplicate_field_fails(validator) -> None:
    lg = _frozen_logging()
    lg["dual_model_required_log_fields"].append("dual_run_group_id")
    with pytest.raises(validator.DualPreflightError):
        validator.check_logging_frozen(lg)


def test_privacy_needs_iso_date(validator) -> None:
    lg = _frozen_logging()
    lg["privacy_review"]["reviewed_at"] = "not-a-date"
    assert validator.check_privacy_completed(lg) is False


def _frozen_stop() -> dict:
    st = _load("stop_conditions.yaml")
    st["frozen"] = True
    for e in st["threshold_stop"]:
        e["threshold_status"] = "resolved"
        e["threshold"] = 0.1
    return st


def test_stop_baseline_not_frozen(validator) -> None:
    assert validator.check_stop_frozen(_load("stop_conditions.yaml")) is False


def test_stop_full_frozen(validator) -> None:
    assert validator.check_stop_frozen(_frozen_stop()) is True


def test_stop_duplicate_condition_fails(validator) -> None:
    st = _frozen_stop()
    st["immediate_stop"].append(dict(st["immediate_stop"][0]))
    with pytest.raises(validator.DualPreflightError):
        validator.check_stop_frozen(st)


def test_stop_illegal_action_fails(validator) -> None:
    st = _frozen_stop()
    st["immediate_stop"][0]["action"] = "ignore"
    with pytest.raises(validator.DualPreflightError):
        validator.check_stop_frozen(st)


def test_stop_unresolved_threshold_not_frozen(validator) -> None:
    st = _frozen_stop()
    st["threshold_stop"][0]["threshold_status"] = "unresolved"
    assert validator.check_stop_frozen(st) is False


# ==========================================================================
# H. environment CI evidence
# ==========================================================================


def _valid_ci() -> dict:
    return {
        "workflow": "CI",
        "run_number": 5,
        "run_id": 123456,
        "status": "completed",
        "conclusion": "success",
        "verified_head_sha": "a" * 40,
        "jobs": {
            "windows-latest / Python 3.12": "success",
            "ubuntu-latest / Python 3.12": "success",
        },
    }


def test_env_baseline_not_reviewed(validator) -> None:
    assert validator.check_environment_reviewed(_load("environment_acceptance.yaml")) is False


def test_env_full_evidence_ok(validator) -> None:
    env = _load("environment_acceptance.yaml")
    env["branch_ci"] = _valid_ci()
    env["environment_review_completed"] = True
    assert validator.check_environment_reviewed(env) is True


def test_env_nonempty_ci_but_invalid_fails(validator) -> None:
    env = _load("environment_acceptance.yaml")
    env["branch_ci"] = {"note": "some ci ran"}  # non-empty but not structured
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env)


@pytest.mark.parametrize("bad_conclusion", ["queued", "in_progress", "failure", "cancelled"])
def test_env_bad_conclusion_fails(validator, bad_conclusion) -> None:
    env = _load("environment_acceptance.yaml")
    ci = _valid_ci()
    ci["conclusion"] = bad_conclusion
    env["branch_ci"] = ci
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env)


def test_env_wrong_head_sha_fails(validator) -> None:
    env = _load("environment_acceptance.yaml")
    ci = _valid_ci()
    ci["verified_head_sha"] = "xyz"  # not 40 hex
    env["branch_ci"] = ci
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env)


def test_env_missing_ubuntu_job_fails(validator) -> None:
    env = _load("environment_acceptance.yaml")
    ci = _valid_ci()
    del ci["jobs"]["ubuntu-latest / Python 3.12"]
    env["branch_ci"] = ci
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env)


def test_env_inherited_baseline_does_not_pass(validator) -> None:
    env = _load("environment_acceptance.yaml")
    # only inherited baseline present, branch_ci still null.
    assert env.get("inherited_baseline_ci") is not None
    assert validator.check_environment_reviewed(env) is False


# ==========================================================================
# I. gates & authorization
# ==========================================================================


def test_required_gates_exact(validator) -> None:
    auth = _load("authorization_gate.yaml")
    validator.check_required_gates_exact(auth)  # ok
    auth["required_gates"] = auth["required_gates"][:-1]
    with pytest.raises(validator.DualPreflightError):
        validator.check_required_gates_exact(auth)


def test_required_gates_duplicate_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["required_gates"] = list(auth["required_gates"]) + ["route_frozen"]
    with pytest.raises(validator.DualPreflightError):
        validator.check_required_gates_exact(auth)


def test_per_model_authorization_field_forbidden(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["per_model_authorization"] = {"deepseek-v4-pro": True}
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


def test_authorized_needs_iso_date(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = "pi"
    auth["authorized_at"] = "yesterday"  # not ISO
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, True)
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
    assert report["ready_for_authorization"] is False
    assert "all_models_frozen" in report["blocking_gates"]
    assert "route_frozen" in report["resolved_gates"]


# ==========================================================================
# J. hashes & isolation
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
    assert per2 == per1  # shared prompt is not a per-model sub-contract


def test_sampling_aggregate_change_affects_aggregate_hash(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    per1 = validator.compute_per_model_contract_hashes(c)
    c["sampling_and_repeat_contract.yaml"]["aggregate"] = {"total_planned_requests": 48}
    agg2 = validator.compute_aggregate_contract_hash(c)
    per2 = validator.compute_per_model_contract_hashes(c)
    assert agg2 != agg1
    assert per2 == per1


def test_budget_aggregate_change_affects_aggregate_hash(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    per1 = validator.compute_per_model_contract_hashes(c)
    c["budget_and_rate_limit_contract.yaml"]["aggregate"]["maximum_total_budget"] = 500
    agg2 = validator.compute_aggregate_contract_hash(c)
    per2 = validator.compute_per_model_contract_hashes(c)
    assert agg2 != agg1
    assert per2 == per1


def test_authorization_status_change_affects_aggregate_hash(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    c["authorization_gate.yaml"]["authorization_status"] = "authorized"
    agg2 = validator.compute_aggregate_contract_hash(c)
    assert agg2 != agg1


def test_branch_ci_change_affects_aggregate_hash(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    per1 = validator.compute_per_model_contract_hashes(c)
    c["environment_acceptance.yaml"]["branch_ci"] = _valid_ci()
    agg2 = validator.compute_aggregate_contract_hash(c)
    per2 = validator.compute_per_model_contract_hashes(c)
    assert agg2 != agg1
    assert per2 == per1  # per-model hashes untouched


def test_provider_adapter_hash_not_self_referential(validator) -> None:
    # stored adapter_sha256 must NOT feed the reported provider_adapter_hash.
    c = _contracts(validator)
    h1 = validator.compute_provider_adapter_hashes(c)
    c["provider_adapter_contract.yaml"]["adapters"]["deepseek-v4-pro"]["adapter_sha256"] = "f" * 64
    h2 = validator.compute_provider_adapter_hashes(c)
    assert h2 == h1  # only canonical mapping payload matters


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


# ==========================================================================
# K. AST write / exec / env detection (temporary validator injection)
# ==========================================================================

_SCAN_HEADER = "from pathlib import Path\n"


def _scan_snippet(validator, tmp_path, body: str) -> None:
    p = tmp_path / "snippet.py"
    p.write_text(_SCAN_HEADER + body, encoding="utf-8")
    validator.scan_python_source(p)


def test_scan_write_text_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "def f(p):\n    Path(p).write_text('x')\n")


def test_scan_open_write_mode_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "def f():\n    open('a', 'w')\n")


def test_scan_unlink_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "def f(p):\n    Path(p).unlink()\n")


def test_scan_subprocess_run_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "import subprocess\ndef f():\n    subprocess.run(['ls'])\n")


def test_scan_getenv_fails(validator, tmp_path) -> None:
    body = "def f():\n    return __import__('os').getenv('X')\n"
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, body)


def test_scan_pure_read_text_ok(validator, tmp_path) -> None:
    # read-only Path.read_text must pass.
    _scan_snippet(validator, tmp_path, "def f(p):\n    return Path(p).read_text()\n")


def test_scan_open_read_mode_ok(validator, tmp_path) -> None:
    _scan_snippet(validator, tmp_path, "def f():\n    return open('a', 'r')\n")


def test_package_scan_passes(validator) -> None:
    validator.check_package_python_scan()  # scans all package python files


# ==========================================================================
# L. isolation & no-network guarantees
# ==========================================================================


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
                   "import socket", "\nimport os\n", "import subprocess", "import shutil"):
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
