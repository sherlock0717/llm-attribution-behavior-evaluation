"""Static tests for the PA-Wu R1 P1 DUAL-model preflight package.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the HARDENED offline validator: recursive managed-asset inventory
+ package hash, prompt structural exclusivity, model freeze field-source binding
to official evidence + supplemental evidence, budget official price binding + GPT
long-context, stable ci_subject_hash + CI evidence, recursive AST write/exec
detection, logging real hash, stop exact condition sets, dual-model gates +
all-or-nothing authorization, and non-interference with the original single-model
preflight package and the merged dual-model decision package.
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


@pytest.fixture(scope="module")
def evidence(validator):
    return validator.load_official_evidence()


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
    assert "ci_subject_hash" in report


# ==========================================================================
# 2. recursive managed asset inventory + package hash
# ==========================================================================


def test_managed_assets_baseline_ok(validator) -> None:
    validator.check_managed_assets(_load("preflight_manifest.yaml"))


def test_extra_top_level_file_fails(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "extra.yaml").write_text("x: 1\n", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    with pytest.raises(validator.DualPreflightError):
        validator.check_managed_assets(yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8")))


def test_undeclared_nested_python_fails(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "nested").mkdir()
    (dst / "nested" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    with pytest.raises(validator.DualPreflightError):
        validator.check_managed_assets(yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8")))


def test_nested_python_write_text_fails_ast(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "templates").mkdir()
    (dst / "templates" / "tool.py").write_text(
        "from pathlib import Path\ndef f(p):\n    Path(p).write_text('x')\n", encoding="utf-8"
    )
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    # recursive AST scan must catch the write even in a nested file.
    with pytest.raises(validator.DualPreflightError):
        validator.check_package_python_scan()


def test_manifest_files_duplicate_fails(validator) -> None:
    m = _load("preflight_manifest.yaml")
    m["files"] = list(m["files"]) + [m["files"][0]]
    with pytest.raises(validator.DualPreflightError):
        validator.check_managed_assets(m)


def test_template_files_missing_declaration_fails(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "templates").mkdir()
    (dst / "templates" / "seg.txt").write_text("hi", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    m = yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8"))
    # template_files still [] -> undeclared asset -> fail.
    with pytest.raises(validator.DualPreflightError):
        validator.check_managed_assets(m)


def test_readme_change_changes_package_hash(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    c = {n: yaml.safe_load((dst / n).read_text(encoding="utf-8")) for n in validator.CONTRACT_FILES}
    m = yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8"))
    h1 = validator.compute_package_hash(c, m)
    (dst / "README.md").write_text((dst / "README.md").read_text(encoding="utf-8") + "\nX\n", encoding="utf-8")
    assert validator.compute_package_hash(c, m) != h1


def test_template_change_changes_package_hash(validator, tmp_path, monkeypatch) -> None:
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "templates").mkdir()
    (dst / "templates" / "seg.txt").write_text("hi", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    c = {n: yaml.safe_load((dst / n).read_text(encoding="utf-8")) for n in validator.CONTRACT_FILES}
    m = yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8"))
    m["template_files"] = ["templates/seg.txt"]
    h1 = validator.compute_package_hash(c, m)
    (dst / "templates" / "seg.txt").write_text("hi2", encoding="utf-8")
    assert validator.compute_package_hash(c, m) != h1


# ==========================================================================
# 3. prompt structural exclusivity
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


def test_prompt_content_true_hash_match_still_fails(validator) -> None:
    p = _frozen_prompt(validator)
    seg = p["segments"]["system_prompt"]
    seg["content"] = True
    seg["sha256"] = hashlib.sha256(b"True").hexdigest()  # even if "hash matches"
    assert validator.check_prompt(p) is False


def test_prompt_content_number_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["content"] = 123
    assert validator.check_prompt(p) is False


def test_prompt_content_mapping_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["content"] = {}
    assert validator.check_prompt(p) is False


def test_prompt_top_level_model_prompts_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["model_prompts"] = {"deepseek-v4-pro": "x"}
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_top_level_model_id_key_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["deepseek-v4-pro"] = "x"
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_constraints_provider_override_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["constraints"]["provider_override"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_segment_extra_model_id_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["gpt-5.6-terra"] = "x"
    # extra key breaks segment exact key set -> not frozen.
    assert validator.check_prompt(p) is False


def test_prompt_content_changed_stale_sha_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"]["content"] = "mutated content"
    assert validator.check_prompt(p) is False


def test_prompt_template_escape_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["system_prompt"] = {
        "content": None,
        "template_reference": "../../../etc/passwd",
        "sha256": "a" * 64,
        "frozen": True,
        "owner": "researcher",
        "change_requires_new_run_version": True,
    }
    assert validator.check_prompt(p) is False


def test_prompt_item_bundle_missing_one_fails(validator) -> None:
    p = _frozen_prompt(validator)
    short = list(_ITEM_BUNDLE)[:2]
    p["segments"]["item_block"]["source_bundle"] = short
    p["segments"]["item_block"]["sha256"] = validator.source_bundle_hash(short)
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_item_bundle_reordered_fails(validator) -> None:
    p = _frozen_prompt(validator)
    p["segments"]["item_block"]["source_bundle"] = [_ITEM_BUNDLE[1], _ITEM_BUNDLE[0], _ITEM_BUNDLE[2]]
    with pytest.raises(validator.DualPreflightError):
        validator.check_prompt(p)


def test_prompt_item_bundle_real_hash_ok(validator) -> None:
    assert validator.check_prompt(_frozen_prompt(validator)) is True


# ==========================================================================
# 4. model freeze evidence binding
# ==========================================================================


def _frozen_decision(mid: str, provider: str) -> dict:
    """Frozen decision bound to REAL official source IDs, real context bound,
    supplemental evidence for still-unresolved fields, NO example URLs."""
    if mid == "deepseek-v4-pro":
        endpoint = "openai_chat_completions"
        ctx = 1_000_000
        pricing_src = "ds_models_and_pricing"
        fsi = {
            "context_window_requirement": ["ds_models_and_pricing"],
            "endpoint_type": ["ds_create_chat_completion", "ds_models_and_pricing"],
            "access_method": ["ds_create_chat_completion"],
            "structured_output_support": ["ds_json_output"],
            "temperature_support": ["ds_thinking_mode"],
        }
        refs = ["ds_models_and_pricing", "ds_create_chat_completion"]
    else:
        endpoint = "responses_api"
        ctx = 1_050_000
        pricing_src = "oai_model_page"
        fsi = {
            "context_window_requirement": ["oai_model_page"],
            "endpoint_type": ["oai_model_page", "oai_models_compare"],
            "access_method": ["oai_responses_api"],
            "structured_output_support": ["oai_structured_outputs"],
            "temperature_support": ["oai_model_page"],
        }
        refs = ["oai_model_page", "oai_responses_api"]
    supp = {
        f: {
            "evidence_id": f"supp_{mid}_{f}",
            "field": f,
            "model_id": mid,
            "status": "reviewed",
            "value": "confirmed_by_manual_interface_check",
            "reviewed_by": "researcher",
            "reviewed_at": "2026-07-20",
            "reference": "internal_interface_check_log",
            "claim_scope": "manual_account_interface_verification",
        }
        for f in ("exact_model_version_or_snapshot", "deterministic_seed_support", "response_id_available")
    }
    return {
        "freeze_status": "frozen",
        "provider": provider,
        "model_id": mid,
        "role": "co_primary",
        "exact_model_version_or_snapshot": "2026-07-01-snap",
        "endpoint_type": endpoint,
        "access_method": "https_api",
        "context_window_requirement": ctx,
        "structured_output_support": True,
        "deterministic_seed_support": False,
        "temperature_support": True,
        "response_id_available": True,
        "provider_retention_policy_reviewed": True,
        "pricing_snapshot_date": "2026-07-01",
        "pricing_source_recorded": pricing_src,
        "regional_availability_reviewed": True,
        "terms_of_use_reviewed": True,
        "decided_by": "researcher",
        "decided_at": "2026-07-02",
        "source_references": refs,
        "evidence_binding": {
            "official_evidence_package_hash": "97a9a625bba76636",
            "field_source_ids": fsi,
            "supplemental_evidence": supp,
        },
    }


def test_human_selected_unresolved_ok(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    assert validator.check_model_selection(d, evidence) == {m: False for m in MODELS}


def test_both_frozen_all_models_frozen_true(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    d["decisions"]["deepseek-v4-pro"] = _frozen_decision("deepseek-v4-pro", "deepseek")
    d["decisions"]["gpt-5.6-terra"] = _frozen_decision("gpt-5.6-terra", "openai")
    d["all_models_frozen"] = True
    assert all(validator.check_model_selection(d, evidence).values())


def test_source_id_not_exist_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["evidence_binding"]["field_source_ids"]["context_window_requirement"] = ["not_a_real_source"]
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_source_cross_provider_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["evidence_binding"]["field_source_ids"]["context_window_requirement"] = ["oai_model_page"]
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_source_duplicate_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["evidence_binding"]["field_source_ids"]["endpoint_type"] = ["ds_models_and_pricing", "ds_models_and_pricing"]
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_source_not_supporting_field_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    # ds_privacy does not support context_window_requirement.
    dec["evidence_binding"]["field_source_ids"]["context_window_requirement"] = ["ds_privacy"]
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_context_over_official_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["context_window_requirement"] = 2_000_000  # exceeds official 1,000,000
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_endpoint_not_confirmed_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["endpoint_type"] = "some_made_up_endpoint"
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_pricing_source_recorded_url_rejected(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["pricing_source_recorded"] = "https://example/pricing"  # arbitrary URL, not a source id
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_source_references_example_url_rejected(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["source_references"] = ["https://x/docs"]  # not real source ids
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_missing_supplemental_snapshot_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    del dec["evidence_binding"]["supplemental_evidence"]["exact_model_version_or_snapshot"]
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


def test_decision_extra_key_fails(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["winner"] = True
    d["decisions"]["deepseek-v4-pro"] = dec
    with pytest.raises(validator.DualPreflightError):
        validator.check_model_selection(d, evidence)


def test_incomplete_review_not_frozen(validator, evidence) -> None:
    d = _load("model_selection_decision.yaml")
    dec = _frozen_decision("deepseek-v4-pro", "deepseek")
    dec["terms_of_use_reviewed"] = False
    d["decisions"]["deepseek-v4-pro"] = dec
    assert validator.check_model_selection(d, evidence)["deepseek-v4-pro"] is False


# ==========================================================================
# 5. budget official price binding + GPT long-context
# ==========================================================================


def _official(validator, evidence, mid: str) -> dict:
    mev = validator._index_model_evidence(evidence)[mid]
    return {
        "cached": float(mev["cached_input_price"]),
        "uncached": float(mev["uncached_input_price"]),
        "output": float(mev["output_price"]),
    }


def _budget_model(validator, evidence, mid: str, rc: int = 24) -> dict:
    prices = _official(validator, evidence, mid)
    cached_tokens, uncached_tokens, out_tokens = 400_000, 600_000, 300_000
    if mid == "deepseek-v4-pro":
        src = "ds_models_and_pricing"
        cost = (
            (uncached_tokens / 1e6) * prices["uncached"]
            + (cached_tokens / 1e6) * prices["cached"]
            + (out_tokens / 1e6) * prices["output"]
        )
        policy = {
            "base_price_source_ids": [src],
            "maximum_uncached_input_tokens_per_request": None,
            "long_context_pricing_applicability": "not_applicable",
            "explicit_cache_write_used": None,
        }
        conc_limit = 500
    else:
        src = "oai_model_page"
        # not_applicable, uncached per request <= 272000.
        cost = (
            (uncached_tokens / 1e6) * prices["uncached"]
            + (cached_tokens / 1e6) * prices["cached"]
            + (out_tokens / 1e6) * prices["output"]
        )
        policy = {
            "base_price_source_ids": [src],
            "maximum_uncached_input_tokens_per_request": 200_000,
            "long_context_pricing_applicability": "not_applicable",
            "explicit_cache_write_used": False,
        }
        conc_limit = 100
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
        "pricing_inputs": {
            "uncached_input_price_per_million": prices["uncached"],
            "cached_input_price_per_million": prices["cached"],
            "output_price_per_million": prices["output"],
            "estimated_cached_input_tokens": cached_tokens,
            "estimated_uncached_input_tokens": uncached_tokens,
        },
        "pricing_policy": policy,
        "estimated_input_tokens": cached_tokens + uncached_tokens,
        "estimated_output_tokens": out_tokens,
        "planned_request_count": rc,
        "estimated_cost": cost,
        "maximum_model_budget": 10_000.0,
        "warning_threshold": 8_000.0,
        "concurrency_limit": conc_limit,
        "requests_per_minute_limit": 60,
        "tokens_per_minute_limit": 1_000_000,
        "budget_owner": "pi",
        "budget_approved": True,
        "approval_timestamp": "2026-07-02",
    }


def _approved_budget(validator, evidence, rc: int = 24) -> dict:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"] = _budget_model(validator, evidence, "deepseek-v4-pro", rc)
    b["models"]["gpt-5.6-terra"] = _budget_model(validator, evidence, "gpt-5.6-terra", rc)
    cost = sum(b["models"][m]["estimated_cost"] for m in MODELS)
    b["aggregate"] = {
        "currency": "USD",
        "maximum_total_budget": 20_000.0,
        "warning_total_threshold": 16_000.0,
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


def test_budget_one_unapproved_overall_false(validator, evidence) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    pm = validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"], evidence)
    assert pm == {m: False for m in MODELS}


def test_budget_full_approval_ok(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    assert all(validator.check_budget(b, _sampling_models(), evidence).values())


def test_budget_correct_source_wrong_price_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    b["models"]["deepseek-v4-pro"]["pricing_inputs"]["output_price_per_million"] = 0.99
    b["all_model_budgets_approved"] = False
    assert validator.check_budget(b, _sampling_models(), evidence)["deepseek-v4-pro"] is False


def test_budget_all_zero_prices_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    for k in ("uncached_input_price_per_million", "cached_input_price_per_million", "output_price_per_million"):
        b["models"]["deepseek-v4-pro"]["pricing_inputs"][k] = 0.0
    b["all_model_budgets_approved"] = False
    assert validator.check_budget(b, _sampling_models(), evidence)["deepseek-v4-pro"] is False


def test_budget_deepseek_openai_multiplier_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    b["models"]["deepseek-v4-pro"]["pricing_policy"]["long_context_pricing_applicability"] = "applies"
    b["all_model_budgets_approved"] = False
    assert validator.check_budget(b, _sampling_models(), evidence)["deepseek-v4-pro"] is False


def test_budget_gpt_over_272k_not_applicable_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    b["models"]["gpt-5.6-terra"]["pricing_policy"]["maximum_uncached_input_tokens_per_request"] = 300_000
    b["all_model_budgets_approved"] = False
    assert validator.check_budget(b, _sampling_models(), evidence)["gpt-5.6-terra"] is False


def test_budget_gpt_unresolved_applicability_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    b["models"]["gpt-5.6-terra"]["pricing_policy"]["long_context_pricing_applicability"] = "unresolved"
    b["all_model_budgets_approved"] = False
    assert validator.check_budget(b, _sampling_models(), evidence)["gpt-5.6-terra"] is False


def test_budget_single_model_request_mismatch_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence, rc=24)
    # single model approved, but sampling request count differs -> immediate check.
    sm = {"deepseek-v4-pro": {"planned_request_count": 999, "concurrency": 2},
          "gpt-5.6-terra": {"planned_request_count": 24, "concurrency": 2}}
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, sm, evidence)


def test_budget_single_approved_without_aggregate_still_fails(validator, evidence) -> None:
    b = _approved_budget(validator, evidence)
    # one model unapproved + aggregate unapproved: per-model of the approved model
    # is True, but overall derived is False.
    b["models"]["gpt-5.6-terra"]["budget_approved"] = False
    b["aggregate"]["aggregate_budget_approved"] = False
    b["all_model_budgets_approved"] = False
    pm = validator.check_budget(b, _sampling_models(), evidence)
    assert pm["deepseek-v4-pro"] is True
    assert pm["gpt-5.6-terra"] is False


def test_budget_deepseek_concurrency_over_500_fails(validator, evidence) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"]["concurrency_limit"] = 501
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"], evidence)


def test_budget_cross_provider_price_source_fails(validator, evidence) -> None:
    b = _load("budget_and_rate_limit_contract.yaml")
    b["models"]["deepseek-v4-pro"]["pricing_evidence_reference"]["source_ids"] = ["oai_model_page"]
    with pytest.raises(validator.DualPreflightError):
        validator.check_budget(b, _load("sampling_and_repeat_contract.yaml")["models"], evidence)


# ==========================================================================
# 6. stable CI subject hash
# ==========================================================================


def _contracts(validator) -> dict:
    return {n: _load(n) for n in validator.CONTRACT_FILES}


def _valid_ci(subject_hash: str) -> dict:
    return {
        "workflow": "CI",
        "run_number": 5,
        "run_id": 123456,
        "status": "completed",
        "conclusion": "success",
        "verified_head_sha": "a" * 40,
        "validated_subject_hash": subject_hash,
        "jobs": {
            "windows-latest / Python 3.12": "success",
            "ubuntu-latest / Python 3.12": "success",
        },
    }


def test_ci_head_sha_wrong_subject_fails(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    subject = validator.compute_ci_subject_hash(c, m)
    env = _load("environment_acceptance.yaml")
    ci = _valid_ci(subject)
    ci["validated_subject_hash"] = "0" * 16  # wrong subject hash
    env["branch_ci"] = ci
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env, subject)


def test_ci_correct_subject_passes(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    subject = validator.compute_ci_subject_hash(c, m)
    env = _load("environment_acceptance.yaml")
    env["branch_ci"] = _valid_ci(subject)
    env["environment_review_completed"] = True
    assert validator.check_environment_reviewed(env, subject) is True


def test_ci_stale_after_prompt_change_fails(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    old_subject = validator.compute_ci_subject_hash(c, m)
    # record CI with old subject, then mutate the prompt.
    c["prompt_freeze_contract.yaml"]["segments"]["system_prompt"]["owner"] = "changed"
    new_subject = validator.compute_ci_subject_hash(c, m)
    assert new_subject != old_subject
    env = _load("environment_acceptance.yaml")
    env["branch_ci"] = _valid_ci(old_subject)  # stale
    env["environment_review_completed"] = True
    with pytest.raises(validator.DualPreflightError):
        validator.check_environment_reviewed(env, new_subject)


def test_ci_stale_after_budget_change_fails(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    old_subject = validator.compute_ci_subject_hash(c, m)
    c["budget_and_rate_limit_contract.yaml"]["aggregate"]["maximum_total_budget"] = 42
    new_subject = validator.compute_ci_subject_hash(c, m)
    assert new_subject != old_subject


def test_ci_subject_unchanged_by_writing_branch_ci(validator) -> None:
    c = _contracts(validator)
    m = _load("preflight_manifest.yaml")
    subject1 = validator.compute_ci_subject_hash(c, m)
    # writing branch_ci / authorization does NOT change the subject hash.
    c["environment_acceptance.yaml"]["branch_ci"] = _valid_ci(subject1)
    c["environment_acceptance.yaml"]["environment_review_completed"] = True
    c["authorization_gate.yaml"]["authorization_status"] = "authorized"
    subject2 = validator.compute_ci_subject_hash(c, m)
    assert subject2 == subject1


# ==========================================================================
# 7. recursive AST scan hardening
# ==========================================================================

_SCAN_HEADER = "from pathlib import Path\n"


def _scan_snippet(validator, tmp_path, body: str, header: str = _SCAN_HEADER) -> None:
    p = tmp_path / "snippet.py"
    p.write_text(header + body, encoding="utf-8")
    validator.scan_python_source(p)


def test_scan_variable_mode_fails(validator, tmp_path) -> None:
    body = "def f(m):\n    return open('a', m)\n"
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, body)


def test_scan_io_open_write_fails(validator, tmp_path) -> None:
    body = "def f():\n    return io.open('a', 'w')\n"
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, body, header="import io\n")


def test_scan_getattr_write_text_fails(validator, tmp_path) -> None:
    body = "def f(p):\n    return getattr(p, 'write_text')\n"
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, body)


def test_scan_open_rb_ok(validator, tmp_path) -> None:
    _scan_snippet(validator, tmp_path, "def f():\n    return open('a', 'rb')\n")


def test_scan_open_default_mode_ok(validator, tmp_path) -> None:
    _scan_snippet(validator, tmp_path, "def f():\n    return open('a')\n")


def test_scan_write_text_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "def f(p):\n    Path(p).write_text('x')\n")


def test_scan_subprocess_run_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "import subprocess\ndef f():\n    subprocess.run(['ls'])\n")


def test_scan_getenv_fails(validator, tmp_path) -> None:
    with pytest.raises(validator.DualPreflightError):
        _scan_snippet(validator, tmp_path, "def f():\n    return __import__('os').getenv('X')\n")


def test_scan_pure_read_text_ok(validator, tmp_path) -> None:
    _scan_snippet(validator, tmp_path, "def f(p):\n    return Path(p).read_text()\n")


def test_package_scan_passes(validator) -> None:
    validator.check_package_python_scan()


# ==========================================================================
# 8. logging real hash + stop exact conditions
# ==========================================================================


def _frozen_logging(validator) -> dict:
    lg = _load("provenance_and_logging_contract.yaml")
    lg["frozen"] = True
    lg["frozen_by"] = "pi"
    lg["logging_contract_version"] = "v1"
    lg["privacy_review"] = {"status": "completed", "reviewed_by": "dpo", "reviewed_at": "2026-07-02"}
    lg["logging_contract_hash"] = validator.compute_logging_contract_hash(lg)
    return lg


def test_logging_baseline_not_frozen(validator) -> None:
    assert validator.check_logging_frozen(_load("provenance_and_logging_contract.yaml")) is False


def test_logging_full_frozen(validator) -> None:
    assert validator.check_logging_frozen(_frozen_logging(validator)) is True


def test_logging_fake_hash_not_frozen(validator) -> None:
    lg = _frozen_logging(validator)
    lg["logging_contract_hash"] = "abc123"
    assert validator.check_logging_frozen(lg) is False


def test_logging_content_changed_stale_hash_not_frozen(validator) -> None:
    lg = _frozen_logging(validator)
    lg["dual_model_required_log_fields"].append("extra_field")  # content changed, hash stale
    assert validator.check_logging_frozen(lg) is False


def test_logging_missing_dual_field_fails(validator) -> None:
    lg = _frozen_logging(validator)
    lg["dual_model_required_log_fields"] = lg["dual_model_required_log_fields"][:-1]
    lg["logging_contract_hash"] = validator.compute_logging_contract_hash(lg)
    with pytest.raises(validator.DualPreflightError):
        validator.check_logging_frozen(lg)


def _frozen_stop() -> dict:
    st = _load("stop_conditions.yaml")
    st["frozen"] = True
    for e in st["threshold_stop"]:
        e["threshold_status"] = "resolved"
        e["threshold"] = 5.0 if e["condition"] == "cost_estimation_error" else 0.1
    return st


def test_stop_baseline_not_frozen(validator) -> None:
    assert validator.check_stop_frozen(_load("stop_conditions.yaml")) is False


def test_stop_full_frozen(validator) -> None:
    assert validator.check_stop_frozen(_frozen_stop()) is True


def test_stop_extra_immediate_condition_fails(validator) -> None:
    st = _frozen_stop()
    st["immediate_stop"].append({"condition": "some_new_condition", "threshold": "x",
                                 "action": "hard_stop", "resume_requires": "x", "owner": None})
    with pytest.raises(validator.DualPreflightError):
        validator.check_stop_frozen(st)


def test_stop_rate_threshold_over_one_not_frozen(validator) -> None:
    st = _frozen_stop()
    for e in st["threshold_stop"]:
        if e["condition"] == "schema_failure_rate":
            e["threshold"] = 1.5  # invalid rate
    assert validator.check_stop_frozen(st) is False


def test_stop_negative_cost_threshold_not_frozen(validator) -> None:
    st = _frozen_stop()
    for e in st["threshold_stop"]:
        if e["condition"] == "cost_estimation_error":
            e["threshold"] = -1.0
    assert validator.check_stop_frozen(st) is False


def test_stop_unresolved_threshold_not_frozen(validator) -> None:
    st = _frozen_stop()
    st["threshold_stop"][0]["threshold_status"] = "unresolved"
    assert validator.check_stop_frozen(st) is False


# ==========================================================================
# adapter (retained + hardened)
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


def test_adapter_hash_mismatch_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["adapter_sha256"] = "0" * 64
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


def test_two_synthetic_adapters_freeze(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    a["adapters"]["deepseek-v4-pro"] = _frozen_adapter(validator, "deepseek")
    a["adapters"]["gpt-5.6-terra"] = _frozen_adapter(validator, "openai")
    a["all_adapters_frozen"] = True
    assert all(validator.check_provider_adapters(a).values())


def test_adapter_scenario_rewrite_field_fails(validator) -> None:
    a = _load("provider_adapter_contract.yaml")
    ad = _frozen_adapter(validator, "deepseek")
    ad["scenario_rewrite"] = True
    ad["adapter_sha256"] = validator.compute_adapter_sha256(ad)
    a["adapters"]["deepseek-v4-pro"] = ad
    with pytest.raises(validator.DualPreflightError):
        validator.check_provider_adapters(a)


# ==========================================================================
# sampling (retained)
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


def test_sampling_top_p_out_of_range_fails(validator) -> None:
    s = _load("sampling_and_repeat_contract.yaml")
    s["shared_design"] = _shared()
    sm = _frozen_sampling(False, None, 24)
    sm["top_p"] = 1.5
    s["models"]["deepseek-v4-pro"] = sm
    s["models"]["gpt-5.6-terra"] = _frozen_sampling(False, None, 24)
    s["all_model_sampling_frozen"] = False
    assert validator.check_sampling(s)["deepseek-v4-pro"] is False


# ==========================================================================
# retry (retained)
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


def test_retry_full_frozen(validator) -> None:
    assert all(validator.check_retry(_frozen_retry()).values())


def test_retry_overlapping_lists_not_frozen(validator) -> None:
    r = _frozen_retry()
    r["models"]["deepseek-v4-pro"]["non_auto_retryable_codes"] = ["429"]
    r["all_model_retry_policies_frozen"] = False
    assert validator.check_retry(r)["deepseek-v4-pro"] is False


# ==========================================================================
# authorization (retained)
# ==========================================================================


def test_required_gates_exact(validator) -> None:
    auth = _load("authorization_gate.yaml")
    validator.check_required_gates_exact(auth)
    auth["required_gates"] = auth["required_gates"][:-1]
    with pytest.raises(validator.DualPreflightError):
        validator.check_required_gates_exact(auth)


def test_per_model_authorization_field_forbidden(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["per_model_authorization"] = {"deepseek-v4-pro": True}
    with pytest.raises(validator.DualPreflightError):
        validator.check_required_gates_exact(auth)


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
# hashes & isolation
# ==========================================================================


def test_per_model_hash_deterministic(validator) -> None:
    c = _contracts(validator)
    assert validator.compute_per_model_contract_hashes(c) == validator.compute_per_model_contract_hashes(c)


def test_changing_deepseek_changes_only_its_hash(validator) -> None:
    c = _contracts(validator)
    h1 = validator.compute_per_model_contract_hashes(c)
    c["sampling_and_repeat_contract.yaml"]["models"]["deepseek-v4-pro"]["temperature"] = 0.7
    h2 = validator.compute_per_model_contract_hashes(c)
    assert h2["deepseek-v4-pro"] != h1["deepseek-v4-pro"]
    assert h2["gpt-5.6-terra"] == h1["gpt-5.6-terra"]


def test_provider_adapter_hash_not_self_referential(validator) -> None:
    c = _contracts(validator)
    h1 = validator.compute_provider_adapter_hashes(c)
    c["provider_adapter_contract.yaml"]["adapters"]["deepseek-v4-pro"]["adapter_sha256"] = "f" * 64
    h2 = validator.compute_provider_adapter_hashes(c)
    assert h2 == h1


def test_aggregate_covers_authorization(validator) -> None:
    c = _contracts(validator)
    agg1 = validator.compute_aggregate_contract_hash(c)
    c["authorization_gate.yaml"]["authorization_status"] = "authorized"
    assert validator.compute_aggregate_contract_hash(c) != agg1


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
                   "import socket", "\nimport os\n", "import subprocess", "import shutil"):
        assert banned not in src


def test_manifest_source_hashes_recorded(validator) -> None:
    m = validator.check_manifest()
    sp = m["source_packages"]
    assert sp["single_model_preflight"]["contract_hash"] == validator.SINGLE_PREFLIGHT_CONTRACT_HASH
    assert sp["dual_model_decision"]["package_hash"] == validator.DUAL_DECISION_PACKAGE_HASH
