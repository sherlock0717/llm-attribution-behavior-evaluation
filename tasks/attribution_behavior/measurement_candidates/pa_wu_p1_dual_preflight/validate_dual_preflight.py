"""Static, offline validator for the PA-Wu R1 P1 DUAL-model preflight package.

STRICT boundaries:
- NO network I/O; NEVER reads an API key or environment variable; NEVER imports
  a real-model SDK; NEVER executes a model; NEVER produces model output;
- NEVER writes a file; NEVER rewrites a contract; NEVER auto-enables authorization;
- NEVER reads R2/R3 or translation assets;
- NEVER modifies the original single-model preflight package.

Authorization state has a SINGLE human source of truth: ``authorization_gate.yaml``.
``p1_execution_status`` is NOT persisted anywhere; it is derived only by
``build_report()``. Two co-primary models are authorized all-or-nothing.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent

EXPECTED_MODELS = (
    ("deepseek", "deepseek-v4-pro"),
    ("openai", "gpt-5.6-terra"),
)
EXPECTED_MODEL_IDS = tuple(m for _, m in EXPECTED_MODELS)
PROVIDER_OF = {mid: prov for prov, mid in EXPECTED_MODELS}

R1_MOCK_HASH = "7c83def4c93ad26f"
SINGLE_PREFLIGHT_CONTRACT_HASH = "2b9548cb6bac6fd3"
SINGLE_PREFLIGHT_PACKAGE_HASH = "d73b5bf6ecee5830"
DUAL_DECISION_PACKAGE_HASH = "97a9a625bba76636"

ITEM_BLOCK_P0_BUNDLE = (
    "pa_wu_p0/items_pa_2024.yaml",
    "pa_wu_p0/items_wu_shen_2026.yaml",
    "pa_wu_p0/forms.yaml",
)

REQUIRED_FILES = (
    "README.md",
    "preflight_manifest.yaml",
    "route_freeze.yaml",
    "model_selection_decision.yaml",
    "provider_adapter_contract.yaml",
    "prompt_freeze_contract.yaml",
    "sampling_and_repeat_contract.yaml",
    "budget_and_rate_limit_contract.yaml",
    "retry_and_recovery_contract.yaml",
    "provenance_and_logging_contract.yaml",
    "stop_conditions.yaml",
    "authorization_gate.yaml",
    "environment_acceptance.yaml",
    "validate_dual_preflight.py",
)

CONTRACT_FILES = (
    "route_freeze.yaml",
    "model_selection_decision.yaml",
    "provider_adapter_contract.yaml",
    "prompt_freeze_contract.yaml",
    "sampling_and_repeat_contract.yaml",
    "budget_and_rate_limit_contract.yaml",
    "retry_and_recovery_contract.yaml",
    "provenance_and_logging_contract.yaml",
    "stop_conditions.yaml",
    "authorization_gate.yaml",
    "environment_acceptance.yaml",
)

REQUIRED_GATES = (
    "route_frozen",
    "dual_model_decision_verified",
    "all_models_frozen",
    "provider_adapters_frozen",
    "prompt_frozen",
    "all_model_sampling_frozen",
    "all_model_budgets_approved",
    "all_model_retry_policies_frozen",
    "logging_contract_frozen",
    "stop_conditions_frozen",
    "privacy_review_completed",
    "environment_review_completed",
    "mock_package_validated",
    "source_hashes_verified",
)

PROMPT_SEGMENTS = (
    "system_prompt",
    "task_instruction",
    "scenario_block",
    "identity_block",
    "response_schema",
    "item_block",
)

_ADAPTER_MAPPING_FIELDS = (
    "request_endpoint_mapping",
    "request_schema_mapping",
    "structured_output_mapping",
    "response_parser_mapping",
    "token_usage_mapping",
    "response_id_mapping",
)

_ADAPTER_SEMANTIC_INVARIANTS = (
    "scenario_semantics_unchanged",
    "identity_semantics_unchanged",
    "item_wording_unchanged",
    "response_field_meaning_unchanged",
    "hidden_reasoning_not_requested",
    "model_specific_content_rewrite_forbidden",
)

_MODEL_FROZEN_FIELDS = (
    "exact_model_version_or_snapshot",
    "endpoint_type",
    "access_method",
    "context_window_requirement",
    "structured_output_support",
    "deterministic_seed_support",
    "temperature_support",
    "response_id_available",
    "pricing_snapshot_date",
    "pricing_source_recorded",
)
_MODEL_TRUE_FIELDS = (
    "provider_retention_policy_reviewed",
    "regional_availability_reviewed",
    "terms_of_use_reviewed",
)

BANNED_MODULES = frozenset(
    {"openai", "anthropic", "httpx", "requests", "socket", "urllib", "os"}
)
FORBIDDEN_PATH_FRAGMENTS = (
    "pa_wu_p1_prep",
    "provisional",
    "adaptation_candidates",
    "ai_human",
    "zh_cn",
    "zh-cn",
)
_NETWORK_CLI = ("curl", "wget", "powershell", "pwsh", "Invoke-WebRequest", "iwr")

DEEPSEEK_CONCURRENCY = 500

_PLACEHOLDERS = frozenset({"", "x", "xx", "placeholder", "todo", "tbd", "none", "null"})
_ROLE_FORBIDDEN_KEYS = ("fallback", "primary_model", "secondary_model", "winner")


class DualPreflightError(RuntimeError):
    """Raised when the dual-model preflight package is inconsistent."""


# --------------------------------------------------------------------------
# Loading + helpers
# --------------------------------------------------------------------------


def _mc_dir() -> Path:
    return PACKAGE_DIR.parent


def _r1_mock_dir() -> Path:
    return _mc_dir() / "pa_wu_r1_mock"


def _single_preflight_dir() -> Path:
    return _mc_dir() / "pa_wu_p1_preflight"


def _dual_decision_dir() -> Path:
    return _mc_dir() / "pa_wu_r1_p1_decision_fill" / "dual_model_selection"


def _load_yaml(name: str) -> dict[str, Any]:
    with (PACKAGE_DIR / name).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise DualPreflightError(f"{name}: expected a mapping at top level")
    return data


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in _PLACEHOLDERS
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


# --------------------------------------------------------------------------
# Structural checks
# --------------------------------------------------------------------------


def check_required_files() -> None:
    missing = [n for n in REQUIRED_FILES if not (PACKAGE_DIR / n).is_file()]
    if missing:
        raise DualPreflightError(f"missing required files: {missing}")


def check_manifest() -> dict[str, Any]:
    m = _load_yaml("preflight_manifest.yaml")
    if m.get("manifest_id") != "pa_wu_p1_dual_preflight.manifest.v1":
        raise DualPreflightError("manifest_id mismatch")
    if m.get("route_id") != "R1":
        raise DualPreflightError("manifest route_id must be R1")
    if m.get("package_status") != "dual_model_preflight_schema":
        raise DualPreflightError("manifest package_status invalid")
    if m.get("migration_status") != "schema_implemented_not_frozen":
        raise DualPreflightError("manifest migration_status invalid")
    if list(m.get("selected_model_ids", [])) != list(EXPECTED_MODEL_IDS):
        raise DualPreflightError("manifest selected_model_ids mismatch")
    if m.get("role_policy") != "co_primary":
        raise DualPreflightError("manifest role_policy must be co_primary")
    if m.get("all_or_nothing_execution") is not True:
        raise DualPreflightError("manifest all_or_nothing_execution must be true")
    if "p1_execution_status" in m:
        raise DualPreflightError("manifest must not persist p1_execution_status")
    if set(m.get("files", [])) != set(REQUIRED_FILES):
        raise DualPreflightError("manifest files list does not match required files")
    if set(m.get("contract_files", [])) != set(CONTRACT_FILES):
        raise DualPreflightError("manifest contract_files mismatch")
    # migration source hashes must equal the real recorded values.
    sp = m.get("source_packages", {})
    single = sp.get("single_model_preflight", {})
    dual = sp.get("dual_model_decision", {})
    if str(single.get("contract_hash")) != SINGLE_PREFLIGHT_CONTRACT_HASH:
        raise DualPreflightError("manifest single_model_preflight.contract_hash mismatch")
    if str(single.get("package_hash")) != SINGLE_PREFLIGHT_PACKAGE_HASH:
        raise DualPreflightError("manifest single_model_preflight.package_hash mismatch")
    if str(dual.get("package_hash")) != DUAL_DECISION_PACKAGE_HASH:
        raise DualPreflightError("manifest dual_model_decision.package_hash mismatch")
    decl = m.get("migration_declarations", {})
    if not isinstance(decl, dict) or not all(v is True for v in decl.values()):
        raise DualPreflightError("manifest migration_declarations must all be true")
    return m


def check_route_boundary(route: dict[str, Any]) -> None:
    expected = {
        "route_id": "R1",
        "language": "en",
        "target_identity": "machine",
        "human_parallel_version": False,
        "translation_used": False,
        "is_construct_adaptation": False,
        "measurement_source": "pa_wu_p0",
        "mock_package_hash": R1_MOCK_HASH,
    }
    for key, want in expected.items():
        if route.get(key) != want:
            raise DualPreflightError(
                f"route_freeze.{key} must be {want!r}, got {route.get(key)!r}"
            )
    for forbidden_key in ("real_model_execution_authorized", "p1_execution_status"):
        if forbidden_key in route:
            raise DualPreflightError(
                f"route_freeze must not carry {forbidden_key!r}"
            )
    forbidden = route.get("forbidden", {})
    if isinstance(forbidden, dict):
        for key, val in forbidden.items():
            if val is not True:
                raise DualPreflightError(f"route_freeze.forbidden.{key} must remain true")


# --------------------------------------------------------------------------
# R1 mock + source hash verification
# --------------------------------------------------------------------------


def verify_r1_mock() -> str:
    import importlib.util

    path = _r1_mock_dir() / "validate_mock_package.py"
    if not path.is_file():
        raise DualPreflightError("R1 mock validator missing")
    spec = importlib.util.spec_from_file_location("pa_wu_r1_mock_from_dual", path)
    if spec is None or spec.loader is None:
        raise DualPreflightError("cannot load R1 mock validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validate_package()
    return str(report["deterministic_run_hash"])


def verify_single_preflight_source() -> bool:
    """Verify the ORIGINAL single-model preflight package is present and its
    recorded hashes match (read-only; the package is never modified)."""
    import importlib.util

    path = _single_preflight_dir() / "validate_preflight.py"
    if not path.is_file():
        raise DualPreflightError("original single-model preflight validator missing")
    spec = importlib.util.spec_from_file_location("pa_wu_single_from_dual", path)
    if spec is None or spec.loader is None:
        raise DualPreflightError("cannot load single-model preflight validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_preflight_report()
    return (
        str(report["contract_hash"]) == SINGLE_PREFLIGHT_CONTRACT_HASH
        and str(report["package_hash"]) == SINGLE_PREFLIGHT_PACKAGE_HASH
    )


def verify_dual_decision_source() -> bool:
    """Verify the merged dual-model decision package hash (read-only)."""
    import importlib.util

    path = _dual_decision_dir() / "validate_dual_model_decision.py"
    if not path.is_file():
        raise DualPreflightError("dual-model decision validator missing")
    spec = importlib.util.spec_from_file_location("pa_wu_decision_from_dual", path)
    if spec is None or spec.loader is None:
        raise DualPreflightError("cannot load dual-model decision validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.build_report()
    if list(report["selected_models"]) != list(EXPECTED_MODEL_IDS):
        raise DualPreflightError("decision package selected_models mismatch")
    if str(report["role_policy"]) != "co_primary":
        raise DualPreflightError("decision package role_policy mismatch")
    return str(report["package_hash"]) == DUAL_DECISION_PACKAGE_HASH


# --------------------------------------------------------------------------
# Dual-model decision (selection vs freeze separation)
# --------------------------------------------------------------------------


def _check_selected_models(models: Any) -> None:
    if not isinstance(models, list) or len(models) != 2:
        raise DualPreflightError("selected_models must contain exactly 2 models")
    got = set()
    for m in models:
        if not isinstance(m, dict):
            raise DualPreflightError("each selected model must be a mapping")
        if str(m.get("role")) != "co_primary":
            raise DualPreflightError("every selected model role must be co_primary")
        got.add((str(m.get("provider")), str(m.get("model_id"))))
    if got != set(EXPECTED_MODELS):
        raise DualPreflightError(f"selected_models must equal {set(EXPECTED_MODELS)}")


def _decision_frozen(dec: dict[str, Any], model_id: str) -> bool:
    """A single model's decision is frozen only when freeze_status == frozen AND
    all frozen fields are set AND all review flags are true. human_selected is
    never auto-promoted to frozen."""
    if not isinstance(dec, dict):
        return False
    if str(dec.get("freeze_status")) != "frozen":
        return False
    if str(dec.get("provider")) != PROVIDER_OF.get(model_id):
        return False
    if str(dec.get("model_id")) != model_id:
        return False
    if str(dec.get("role")) != "co_primary":
        return False
    for f in _MODEL_FROZEN_FIELDS:
        if not _nonempty(dec.get(f)):
            return False
    for f in _MODEL_TRUE_FIELDS:
        if dec.get(f) is not True:
            return False
    if not _nonempty(dec.get("decided_by")):
        return False
    if not _nonempty(dec.get("decided_at")):
        return False
    refs = dec.get("source_references")
    if not isinstance(refs, list) or not refs or not all(_nonempty(r) for r in refs):
        return False
    return True


def check_model_selection(model_sel: dict[str, Any]) -> dict[str, bool]:
    if str(model_sel.get("selection_status")) != "human_selected":
        raise DualPreflightError("selection_status must be human_selected")
    if "selected_model" in model_sel:
        raise DualPreflightError("must not use singular selected_model")
    if model_sel.get("decision_reference_verified") is not True:
        raise DualPreflightError("decision_reference_verified must be true")
    _check_selected_models(model_sel.get("selected_models"))
    decisions = model_sel.get("decisions", {})
    if not isinstance(decisions, dict) or set(decisions) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("decisions keys must equal the two selected models")
    per_model_frozen: dict[str, bool] = {}
    for mid in EXPECTED_MODEL_IDS:
        dec = decisions[mid]
        fs = str(dec.get("freeze_status"))
        if fs not in ("unresolved", "frozen"):
            raise DualPreflightError(f"{mid}: illegal freeze_status {fs!r}")
        per_model_frozen[mid] = _decision_frozen(dec, mid)
    declared_all = model_sel.get("all_models_frozen")
    derived_all = all(per_model_frozen.values())
    if bool(declared_all) != bool(derived_all):
        raise DualPreflightError(
            f"all_models_frozen={declared_all!r} != derived {derived_all!r}"
        )
    return per_model_frozen


# --------------------------------------------------------------------------
# Provider adapter contract
# --------------------------------------------------------------------------


def check_provider_adapters(adapter: dict[str, Any]) -> dict[str, bool]:
    inv = adapter.get("semantic_invariants", {})
    if not isinstance(inv, dict):
        raise DualPreflightError("adapter semantic_invariants must be a mapping")
    for key in _ADAPTER_SEMANTIC_INVARIANTS:
        if inv.get(key) is not True:
            raise DualPreflightError(f"adapter semantic invariant {key!r} must be true")
    ref = adapter.get("compatibility_reference", {})
    if not isinstance(ref, dict) or str(ref.get("package_hash")) != DUAL_DECISION_PACKAGE_HASH:
        raise DualPreflightError("adapter compatibility_reference package_hash mismatch")
    adapters = adapter.get("adapters", {})
    if not isinstance(adapters, dict) or set(adapters) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("adapters keys must equal the two models")
    per_model_frozen: dict[str, bool] = {}
    for mid in EXPECTED_MODEL_IDS:
        a = adapters[mid]
        if not isinstance(a, dict):
            raise DualPreflightError(f"{mid}: adapter must be a mapping")
        if str(a.get("provider")) != PROVIDER_OF[mid]:
            raise DualPreflightError(f"{mid}: adapter provider mismatch")
        for bad in _ROLE_FORBIDDEN_KEYS:
            if bad in a:
                raise DualPreflightError(f"{mid}: adapter must not carry {bad!r}")
        frozen = a.get("frozen")
        if not isinstance(frozen, bool):
            raise DualPreflightError(f"{mid}: adapter frozen must be boolean")
        if frozen:
            for f in _ADAPTER_MAPPING_FIELDS:
                if not _nonempty(a.get(f)):
                    raise DualPreflightError(
                        f"{mid}: frozen adapter missing mapping {f!r}"
                    )
            if not _nonempty(a.get("adapter_sha256")):
                raise DualPreflightError(f"{mid}: frozen adapter missing adapter_sha256")
        per_model_frozen[mid] = bool(frozen)
    declared = adapter.get("all_adapters_frozen")
    if bool(declared) != all(per_model_frozen.values()):
        raise DualPreflightError("all_adapters_frozen != derived")
    return per_model_frozen


# --------------------------------------------------------------------------
# Shared prompt
# --------------------------------------------------------------------------


def check_prompt(prompt: dict[str, Any]) -> bool:
    c = prompt.get("constraints", {})
    if not isinstance(c, dict):
        raise DualPreflightError("prompt constraints must be a mapping")
    if c.get("single_shared_prompt") is not True:
        raise DualPreflightError("prompt must be a single shared prompt")
    if c.get("per_model_semantic_prompt_forbidden") is not True:
        raise DualPreflightError("per-model semantic prompt must be forbidden")
    if str(c.get("identity_presented")) != "machine":
        raise DualPreflightError("identity must be machine")
    if str(c.get("item_wording_source")) != "pa_wu_p0":
        raise DualPreflightError("item_wording_source must be pa_wu_p0")
    segments = prompt.get("segments", {})
    if not isinstance(segments, dict) or set(segments) != set(PROMPT_SEGMENTS):
        raise DualPreflightError("prompt segments must be exactly the six segments")
    item = segments["item_block"]
    if list(item.get("source_bundle", [])) != list(ITEM_BLOCK_P0_BUNDLE):
        raise DualPreflightError("item_block must bind the fixed-order P0 bundle")
    # prompt_frozen only when every segment frozen with a sha256.
    all_frozen = True
    for seg in segments.values():
        if not isinstance(seg, dict) or seg.get("frozen") is not True or not _nonempty(seg.get("sha256")):
            all_frozen = False
    return all_frozen


# --------------------------------------------------------------------------
# Sampling (shared design + per-model)
# --------------------------------------------------------------------------


def _sampling_model_frozen(shared: dict[str, Any], sm: dict[str, Any]) -> bool:
    if not isinstance(sm, dict) or sm.get("frozen") is not True:
        return False
    if sm.get("seed_is_determinism_guarantee") is not False:
        return False
    seed_supported = sm.get("seed_supported")
    if not isinstance(seed_supported, bool):
        return False
    seed = sm.get("seed")
    if seed_supported:
        if not isinstance(seed, int) or isinstance(seed, bool):
            return False
    elif seed is not None:
        return False
    for f in ("temperature", "top_p", "max_output_tokens", "concurrency",
              "request_timeout_seconds"):
        if sm.get(f) is None:
            return False
    if not _positive_int(sm.get("planned_request_count")):
        return False
    pc = shared.get("planned_case_count")
    rp = shared.get("repeats_per_case")
    if not (_positive_int(pc) and _positive_int(rp)):
        return False
    if sm["planned_request_count"] != pc * rp:
        return False
    return True


def check_sampling(sampling: dict[str, Any]) -> dict[str, bool]:
    shared = sampling.get("shared_design", {})
    models = sampling.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("sampling models keys must equal the two models")
    if sampling.get("linked_to_budget_contract") is not True:
        raise DualPreflightError("sampling must be linked_to_budget_contract")
    per_model = {mid: _sampling_model_frozen(shared, models[mid]) for mid in EXPECTED_MODEL_IDS}
    all_frozen = all(per_model.values())
    declared = sampling.get("all_model_sampling_frozen")
    if bool(declared) != all_frozen:
        raise DualPreflightError("all_model_sampling_frozen != derived")
    if all_frozen:
        agg = sampling.get("aggregate", {})
        total = agg.get("total_planned_requests")
        expected_total = sum(models[mid]["planned_request_count"] for mid in EXPECTED_MODEL_IDS)
        if total != expected_total:
            raise DualPreflightError("aggregate.total_planned_requests != sum of models")
    return per_model


# --------------------------------------------------------------------------
# Budget (per-model + aggregate)
# --------------------------------------------------------------------------


def _budget_model_ok(mid: str, bm: dict[str, Any]) -> bool:
    if not isinstance(bm, dict):
        return False
    if bm.get("budget_approved") is not True:
        return False
    if str(bm.get("currency")) != "USD" or str(bm.get("pricing_unit")) != "per_million_tokens":
        return False
    for f in ("estimated_input_tokens", "estimated_output_tokens", "planned_request_count"):
        if not _positive_int(bm.get(f)):
            return False
    for f in ("estimated_cost", "maximum_model_budget", "warning_threshold"):
        if bm.get(f) is None:
            return False
    if not _nonempty(bm.get("budget_owner")) or not _nonempty(bm.get("approval_timestamp")):
        return False
    return True


def check_budget(budget: dict[str, Any], sampling_models: dict[str, Any]) -> dict[str, bool]:
    models = budget.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("budget models keys must equal the two models")
    # DeepSeek concurrency must not exceed 500; cross-provider price rules forbidden.
    ds = models["deepseek-v4-pro"]
    cl = ds.get("concurrency_limit")
    if cl is not None and (not _positive_int(cl) or cl > DEEPSEEK_CONCURRENCY):
        raise DualPreflightError("deepseek concurrency_limit must not exceed 500")
    for mid in EXPECTED_MODEL_IDS:
        ref = models[mid].get("pricing_evidence_reference", {})
        sids = set(map(str, ref.get("source_ids", []))) if isinstance(ref, dict) else set()
        if mid == "deepseek-v4-pro" and not sids <= {"ds_models_and_pricing", "ds_rate_limit"}:
            raise DualPreflightError("deepseek pricing source_ids cross-provider")
        if mid == "gpt-5.6-terra" and not sids <= {"oai_model_page", "oai_models_compare"}:
            raise DualPreflightError("openai pricing source_ids cross-provider")
    per_model = {mid: _budget_model_ok(mid, models[mid]) for mid in EXPECTED_MODEL_IDS}
    agg = budget.get("aggregate", {})
    agg_approved = agg.get("aggregate_budget_approved") is True
    all_ok = all(per_model.values()) and agg_approved
    declared = budget.get("all_model_budgets_approved")
    if bool(declared) != all_ok:
        raise DualPreflightError("all_model_budgets_approved != derived")
    if all_ok:
        # per-model request count must match sampling; aggregate = sum.
        for mid in EXPECTED_MODEL_IDS:
            if models[mid]["planned_request_count"] != sampling_models.get(mid, {}).get("planned_request_count"):
                raise DualPreflightError(f"{mid}: budget request count != sampling")
        exp_cost = sum(models[mid]["estimated_cost"] for mid in EXPECTED_MODEL_IDS)
        if agg.get("estimated_total_cost") != exp_cost:
            raise DualPreflightError("aggregate estimated_total_cost != sum")
        exp_req = sum(models[mid]["planned_request_count"] for mid in EXPECTED_MODEL_IDS)
        if agg.get("total_planned_requests") != exp_req:
            raise DualPreflightError("aggregate total_planned_requests != sum")
    return per_model


# --------------------------------------------------------------------------
# Retry / logging / stop / privacy / environment
# --------------------------------------------------------------------------


def check_retry(retry: dict[str, Any]) -> dict[str, bool]:
    models = retry.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("retry models keys must equal the two models")
    per_model: dict[str, bool] = {}
    for mid in EXPECTED_MODEL_IDS:
        rm = models[mid]
        if str(rm.get("provider")) != PROVIDER_OF[mid]:
            raise DualPreflightError(f"{mid}: retry provider mismatch")
        frozen = rm.get("frozen")
        if not isinstance(frozen, bool):
            raise DualPreflightError(f"{mid}: retry frozen must be boolean")
        if frozen and not _nonempty(rm.get("provider_error_taxonomy")):
            raise DualPreflightError(f"{mid}: frozen retry missing taxonomy")
        per_model[mid] = bool(frozen)
    declared = retry.get("all_model_retry_policies_frozen")
    if bool(declared) != all(per_model.values()):
        raise DualPreflightError("all_model_retry_policies_frozen != derived")
    return per_model


def check_logging_frozen(logging_c: dict[str, Any]) -> bool:
    rules = logging_c.get("rules", {})
    if not isinstance(rules, dict):
        raise DualPreflightError("logging rules must be a mapping")
    for rule in ("never_log_api_key", "never_log_secret", "every_request_has_provider_and_model_id",
                 "cross_model_case_pair_required", "per_model_contract_hash_required",
                 "single_global_model_hash_forbidden"):
        if rules.get(rule) is not True:
            raise DualPreflightError(f"logging rule {rule!r} must be true")
    dual_fields = set(logging_c.get("dual_model_required_log_fields", []))
    required_dual = {"dual_run_group_id", "model_contract_hash", "provider_adapter_hash",
                     "cross_model_case_pair_id", "normalized_token_usage",
                     "normalized_estimated_cost"}
    if not required_dual.issubset(dual_fields):
        raise DualPreflightError("logging missing dual-model provenance fields")
    return logging_c.get("frozen") is True


def check_privacy_completed(logging_c: dict[str, Any]) -> bool:
    pr = logging_c.get("privacy_review", {})
    return (
        isinstance(pr, dict)
        and str(pr.get("status")) == "completed"
        and _nonempty(pr.get("reviewed_by"))
        and _nonempty(pr.get("reviewed_at"))
    )


def check_stop_frozen(stop: dict[str, Any]) -> bool:
    conds = {str(e.get("condition")) for e in stop.get("immediate_stop", []) if isinstance(e, dict)}
    required = {"any_model_contract_hash_changed", "any_provider_adapter_hash_changed",
                "cross_model_case_pair_missing", "one_model_request_count_diverged",
                "one_model_budget_limit_reached", "one_model_systematic_schema_failure"}
    if not required.issubset(conds):
        raise DualPreflightError("stop_conditions missing dual-model conditions")
    policy = stop.get("dual_model_stop_policy", {})
    if not isinstance(policy, dict) or policy.get("no_fallback_substitution") is not True:
        raise DualPreflightError("stop policy must forbid fallback substitution")
    if stop.get("frozen") is not True:
        return False
    for e in stop.get("threshold_stop", []):
        if isinstance(e, dict) and str(e.get("threshold_status")) != "resolved":
            return False
    return True


def check_environment_reviewed(env: dict[str, Any]) -> bool:
    # Must not reuse inherited baseline as this package's own review.
    return env.get("environment_review_completed") is True and env.get("branch_ci") is not None


# --------------------------------------------------------------------------
# Per-model + aggregate + package hashes
# --------------------------------------------------------------------------


def _hash16(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def compute_per_model_contract_hashes(contracts: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Each model's hash covers only that model's sub-contracts (decision,
    adapter, sampling, budget, retry). Changing one model's sub-contract changes
    only that model's hash (and the aggregate), not the other model's."""
    out: dict[str, str] = {}
    for mid in EXPECTED_MODEL_IDS:
        payload = {
            "decision": contracts["model_selection_decision.yaml"]["decisions"][mid],
            "adapter": contracts["provider_adapter_contract.yaml"]["adapters"][mid],
            "sampling": contracts["sampling_and_repeat_contract.yaml"]["models"][mid],
            "budget": contracts["budget_and_rate_limit_contract.yaml"]["models"][mid],
            "retry": contracts["retry_and_recovery_contract.yaml"]["models"][mid],
        }
        out[mid] = _hash16(payload)
    return out


def compute_provider_adapter_hashes(contracts: dict[str, dict[str, Any]]) -> dict[str, str]:
    adapters = contracts["provider_adapter_contract.yaml"]["adapters"]
    return {mid: _hash16(adapters[mid]) for mid in EXPECTED_MODEL_IDS}


def compute_shared_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    """Shared (non per-model) design: prompt, shared sampling design, stop,
    logging, route. Changing the shared prompt changes this and the aggregate."""
    payload = {
        "route": contracts["route_freeze.yaml"],
        "prompt": contracts["prompt_freeze_contract.yaml"],
        "shared_sampling": contracts["sampling_and_repeat_contract.yaml"].get("shared_design"),
        "logging": contracts["provenance_and_logging_contract.yaml"],
        "stop": contracts["stop_conditions.yaml"],
    }
    return _hash16(payload)


def compute_aggregate_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    per_model = compute_per_model_contract_hashes(contracts)
    shared = compute_shared_contract_hash(contracts)
    return _hash16({"per_model": per_model, "shared": shared})


def compute_package_hash(contracts: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> str:
    validator_path = PACKAGE_DIR / "validate_dual_preflight.py"
    if not validator_path.is_file():
        raise DualPreflightError("validator source missing for package hash")
    payload = {
        "manifest": manifest,
        "contracts": {n: contracts[n] for n in sorted(contracts)},
        "validator_source": validator_path.read_text(encoding="utf-8"),
    }
    return _hash16(payload)


# --------------------------------------------------------------------------
# Authorization state machine (single human source)
# --------------------------------------------------------------------------

VALID_AUTH_STATUSES = frozenset({"blocked", "authorized"})


def check_required_gates_exact(auth: dict[str, Any]) -> None:
    gates = auth.get("required_gates", [])
    if not isinstance(gates, list) or set(gates) != set(REQUIRED_GATES):
        raise DualPreflightError("authorization required_gates must equal REQUIRED_GATES")
    if list(auth.get("required_model_ids", [])) != list(EXPECTED_MODEL_IDS):
        raise DualPreflightError("authorization required_model_ids mismatch")
    if auth.get("all_or_nothing_execution") is not True:
        raise DualPreflightError("authorization all_or_nothing_execution must be true")


def check_authorization_state_machine(auth: dict[str, Any], gate_status: dict[str, bool]) -> str:
    status = str(auth.get("authorization_status"))
    if status not in VALID_AUTH_STATUSES:
        raise DualPreflightError(f"illegal authorization_status: {status!r}")
    flag = auth.get("real_model_execution_authorized")
    if not isinstance(flag, bool):
        raise DualPreflightError("real_model_execution_authorized must be boolean")
    all_ok = all(gate_status.values())
    if status == "authorized":
        if flag is not True:
            raise DualPreflightError("authorized requires flag=true")
        if not all_ok:
            failing = sorted(g for g, ok in gate_status.items() if not ok)
            raise DualPreflightError(f"authorized but gates failing: {failing}")
        if not _nonempty(auth.get("authorized_by")) or not _nonempty(auth.get("authorized_at")):
            raise DualPreflightError("authorized requires authorized_by/at")
        return "authorized"
    if flag is True:
        raise DualPreflightError("blocked status must not carry flag=true")
    if _nonempty(auth.get("authorized_by")) or _nonempty(auth.get("authorized_at")):
        raise DualPreflightError("blocked status must have empty authorized_by/at")
    return "blocked"


# --------------------------------------------------------------------------
# AST security scan
# --------------------------------------------------------------------------


def scan_python_source(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))

    def _call_name(node: ast.Call) -> str:
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            parts: list[str] = []
            cur: Any = f
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        return ""

    def _flat_str_args(node: ast.Call) -> list[str]:
        out: list[str] = []
        for a in list(node.args) + [k.value for k in node.keywords]:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append(a.value)
            elif isinstance(a, (ast.List, ast.Tuple)):
                for elt in a.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        out.append(elt.value)
        return out

    importlib_aliases: set[str] = set()
    import_module_aliases: set[str] = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in BANNED_MODULES:
                    raise DualPreflightError(f"banned import {alias.name} in {path.name}")
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or "importlib")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in BANNED_MODULES:
                raise DualPreflightError(f"banned import-from {node.module} in {path.name}")
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_aliases.add(alias.asname or "import_module")

    dynamic = set(import_module_aliases)
    for a in importlib_aliases:
        dynamic.add(f"{a}.import_module")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        args = _flat_str_args(node)
        if name in dynamic or name.endswith(".import_module"):
            for a in args:
                if a.split(".")[0] in BANNED_MODULES:
                    raise DualPreflightError(f"banned dynamic import {a!r} in {path.name}")
                if any(frag in a for frag in FORBIDDEN_PATH_FRAGMENTS):
                    raise DualPreflightError(f"forbidden path import {a!r} in {path.name}")
        top = name.split(".")[0]
        if top in BANNED_MODULES:
            raise DualPreflightError(f"banned network/os call {name!r} in {path.name}")
        if name.startswith("subprocess.") or name in ("run", "Popen", "call", "check_output"):
            for a in args:
                low = a.lower().strip()
                first = low.split()[0] if low.split() else low
                if any(low == c or first == c or c in low.split() for c in (_c.lower() for _c in _NETWORK_CLI)):
                    raise DualPreflightError(f"network CLI via subprocess in {path.name}: {a!r}")
        if name in ("open", "Path") or name.endswith(".open"):
            for a in args:
                if any(frag in a for frag in FORBIDDEN_PATH_FRAGMENTS):
                    raise DualPreflightError(f"forbidden R2/R3 path access {a!r} in {path.name}")
        if name in ("getenv",) or name.endswith(".getenv") or name.endswith("environ.get"):
            raise DualPreflightError(f"environment variable read in {path.name}")


def check_validator_self_scan() -> None:
    scan_python_source(PACKAGE_DIR / "validate_dual_preflight.py")


def check_original_preflight_untouched() -> None:
    """Read-only assertion that the original single-model package still exists;
    this validator never writes to it."""
    if not (_single_preflight_dir() / "validate_preflight.py").is_file():
        raise DualPreflightError("original single-model preflight must remain present")


# --------------------------------------------------------------------------
# Gate computation + full report
# --------------------------------------------------------------------------


def compute_gate_status(
    contracts: dict[str, dict[str, Any]],
    decision_verified: bool,
    mock_ok: bool,
    source_ok: bool,
    per_model_frozen: dict[str, bool],
    per_adapter_frozen: dict[str, bool],
    per_sampling_frozen: dict[str, bool],
    per_budget_ok: dict[str, bool],
    per_retry_frozen: dict[str, bool],
    prompt_frozen: bool,
    logging_frozen: bool,
    privacy_completed: bool,
    stop_frozen: bool,
    env_reviewed: bool,
) -> dict[str, bool]:
    route = contracts["route_freeze.yaml"]
    return {
        "route_frozen": bool(route.get("route_id") == "R1"
                             and str(route.get("mock_package_hash")) == R1_MOCK_HASH),
        "dual_model_decision_verified": bool(decision_verified),
        "all_models_frozen": all(per_model_frozen.values()),
        "provider_adapters_frozen": all(per_adapter_frozen.values()),
        "prompt_frozen": bool(prompt_frozen),
        "all_model_sampling_frozen": all(per_sampling_frozen.values()),
        "all_model_budgets_approved": all(per_budget_ok.values())
            and contracts["budget_and_rate_limit_contract.yaml"].get("aggregate", {}).get("aggregate_budget_approved") is True,
        "all_model_retry_policies_frozen": all(per_retry_frozen.values()),
        "logging_contract_frozen": bool(logging_frozen),
        "stop_conditions_frozen": bool(stop_frozen),
        "privacy_review_completed": bool(privacy_completed),
        "environment_review_completed": bool(env_reviewed),
        "mock_package_validated": bool(mock_ok),
        "source_hashes_verified": bool(source_ok),
    }


def build_report() -> dict[str, Any]:
    check_required_files()
    check_validator_self_scan()
    check_original_preflight_untouched()
    manifest = check_manifest()

    contracts = {n: _load_yaml(n) for n in CONTRACT_FILES}
    check_route_boundary(contracts["route_freeze.yaml"])

    # source verifications
    mock_hash = verify_r1_mock()
    mock_ok = mock_hash == R1_MOCK_HASH
    single_ok = verify_single_preflight_source()
    decision_ok = verify_dual_decision_source()
    source_ok = mock_ok and single_ok and decision_ok

    per_model_frozen = check_model_selection(contracts["model_selection_decision.yaml"])
    per_adapter_frozen = check_provider_adapters(contracts["provider_adapter_contract.yaml"])
    prompt_frozen = check_prompt(contracts["prompt_freeze_contract.yaml"])
    per_sampling_frozen = check_sampling(contracts["sampling_and_repeat_contract.yaml"])
    per_budget_ok = check_budget(
        contracts["budget_and_rate_limit_contract.yaml"],
        contracts["sampling_and_repeat_contract.yaml"]["models"],
    )
    per_retry_frozen = check_retry(contracts["retry_and_recovery_contract.yaml"])
    logging_frozen = check_logging_frozen(contracts["provenance_and_logging_contract.yaml"])
    privacy_completed = check_privacy_completed(contracts["provenance_and_logging_contract.yaml"])
    stop_frozen = check_stop_frozen(contracts["stop_conditions.yaml"])
    env_reviewed = check_environment_reviewed(contracts["environment_acceptance.yaml"])

    auth = contracts["authorization_gate.yaml"]
    check_required_gates_exact(auth)

    gate_status = compute_gate_status(
        contracts, decision_ok, mock_ok, source_ok, per_model_frozen, per_adapter_frozen,
        per_sampling_frozen, per_budget_ok, per_retry_frozen, prompt_frozen, logging_frozen,
        privacy_completed, stop_frozen, env_reviewed,
    )
    resolved_status = check_authorization_state_machine(auth, gate_status)

    resolved_gates = sorted(g for g, ok in gate_status.items() if ok)
    blocking_gates = sorted(g for g, ok in gate_status.items() if not ok)
    all_ok = all(gate_status.values())

    preflight_status = "authorized" if resolved_status == "authorized" else "blocked"

    per_model_gate_status = {
        mid: {
            "decision_frozen": per_model_frozen[mid],
            "adapter_frozen": per_adapter_frozen[mid],
            "sampling_frozen": per_sampling_frozen[mid],
            "budget_approved": per_budget_ok[mid],
            "retry_frozen": per_retry_frozen[mid],
        }
        for mid in EXPECTED_MODEL_IDS
    }

    return {
        "migration_status": manifest["migration_status"],
        "selected_models": list(EXPECTED_MODEL_IDS),
        "role_policy": "co_primary",
        "dual_model_decision_verified": decision_ok,
        "all_models_frozen": gate_status["all_models_frozen"],
        "provider_adapters_frozen": gate_status["provider_adapters_frozen"],
        "prompt_frozen": gate_status["prompt_frozen"],
        "all_model_sampling_frozen": gate_status["all_model_sampling_frozen"],
        "all_model_budgets_approved": gate_status["all_model_budgets_approved"],
        "authorization_status": resolved_status,
        "real_model_execution_authorized": bool(auth.get("real_model_execution_authorized")),
        "preflight_status": preflight_status,
        "p1_execution_status": "authorized" if preflight_status == "authorized" else "blocked",
        "ready_for_authorization": all_ok and resolved_status == "blocked",
        "per_model_gate_status": per_model_gate_status,
        "per_model_contract_hashes": compute_per_model_contract_hashes(contracts),
        "provider_adapter_hashes": compute_provider_adapter_hashes(contracts),
        "shared_contract_hash": compute_shared_contract_hash(contracts),
        "aggregate_contract_hash": compute_aggregate_contract_hash(contracts),
        "package_hash": compute_package_hash(contracts, manifest),
        "resolved_gates": resolved_gates,
        "blocking_gates": blocking_gates,
    }


def main() -> None:  # pragma: no cover
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
