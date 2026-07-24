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

This validator HARDENS every frozen contract: field-level types, ISO dates,
real recomputed SHA-256 for adapters and prompt segments, finite-number sampling
ranges, budget cost formulas, aggregate/branch-CI evidence, an all-or-nothing
authorization state machine, and an AST security scan over EVERY python file in
the package (not just this file).
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from datetime import date, datetime
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

DUAL_DECISION_PACKAGE_PATH = (
    "tasks/attribution_behavior/measurement_candidates/"
    "pa_wu_r1_p1_decision_fill/dual_model_selection"
)
DUAL_DECISION_COMPAT_PATH = DUAL_DECISION_PACKAGE_PATH + "/parameter_compatibility.yaml"

# GPT-5.6 Terra long-context pricing threshold (from official evidence).
GPT_LONG_CONTEXT_INPUT_THRESHOLD = 272_000
GPT_LONG_CONTEXT_INPUT_MULTIPLIER = 2.0
GPT_LONG_CONTEXT_OUTPUT_MULTIPLIER = 1.5
GPT_EXPLICIT_CACHE_WRITE_MULTIPLIER = 1.25
_LONG_CONTEXT_APPLICABILITY = frozenset({"not_applicable", "applies"})

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

# --- prompt structural exclusivity -------------------------------------------
PROMPT_TOP_LEVEL_KEYS = frozenset(
    {"prompt_freeze_id", "constraints", "segments", "template_reference_allowed_roots", "notes"}
)
PROMPT_CONSTRAINT_KEYS = frozenset(
    {
        "request_hidden_reasoning",
        "request_structured_final_scores_only",
        "item_wording_source",
        "scenario_model_rewrite_allowed",
        "identity_presented",
        "change_requires_new_run_version",
        "block_on_prompt_hash_mismatch",
        "single_shared_prompt",
        "per_model_semantic_prompt_forbidden",
    }
)
PROMPT_SEGMENT_KEYS = frozenset(
    {"content", "template_reference", "sha256", "frozen", "owner", "change_requires_new_run_version"}
)
ITEM_SEGMENT_KEYS = frozenset(
    {"content", "template_reference", "source_bundle", "sha256", "frozen", "owner",
     "change_requires_new_run_version"}
)
# forbidden per-model prompt keys anywhere in the prompt contract.
_PROMPT_FORBIDDEN_KEYS = frozenset(
    {"model_prompts", "per_model_prompts", "adapters", "provider_overrides", "provider_override"}
    | set(EXPECTED_MODEL_IDS)
)

# --- model freeze field typing ------------------------------------------------
_MODEL_STRING_FIELDS = (
    "exact_model_version_or_snapshot",
    "endpoint_type",
    "access_method",
    "pricing_source_recorded",
)
_MODEL_BOOL_FIELDS = (
    "structured_output_support",
    "deterministic_seed_support",
    "temperature_support",
    "response_id_available",
)
_MODEL_TRUE_FIELDS = (
    "provider_retention_policy_reviewed",
    "regional_availability_reviewed",
    "terms_of_use_reviewed",
)

# --- model decision evidence binding -----------------------------------------
# Exact key set for each frozen/unresolved decision (structural exactness).
_DECISION_EXACT_KEYS = frozenset(
    {
        "freeze_status",
        "provider",
        "model_id",
        "role",
        "exact_model_version_or_snapshot",
        "endpoint_type",
        "access_method",
        "context_window_requirement",
        "structured_output_support",
        "deterministic_seed_support",
        "temperature_support",
        "response_id_available",
        "provider_retention_policy_reviewed",
        "pricing_snapshot_date",
        "pricing_source_recorded",
        "regional_availability_reviewed",
        "terms_of_use_reviewed",
        "decided_by",
        "decided_at",
        "source_references",
        "evidence_binding",
    }
)
# Fields that are unresolved / requires_interface_check in the decision package
# and therefore need complete supplemental_evidence before they can be frozen.
_SUPPLEMENTAL_REQUIRED_FIELDS = (
    "exact_model_version_or_snapshot",
    "deterministic_seed_support",
    "response_id_available",
)
_SUPPLEMENTAL_ITEM_KEYS = frozenset(
    {"evidence_id", "field", "model_id", "status", "value", "reviewed_by", "reviewed_at",
     "reference", "claim_scope"}
)
# Map decision field name -> the field name used in official evidence supports_fields.
_DECISION_FIELD_TO_EVIDENCE_FIELD = {
    "context_window_requirement": "context_window",
    "access_method": "documented_access_method",
    "endpoint_type": "endpoint_type",
    "structured_output_support": "structured_output_support",
    "temperature_support": "temperature_support",
}

# --- provider adapter ---------------------------------------------------------
# Canonical adapter payload contributes ONLY the semantic mapping fields, never
# the stored hash itself (which would be self-referential) nor the frozen flag.
_ADAPTER_MAPPING_FIELDS = (
    "request_endpoint_mapping",
    "request_schema_mapping",
    "structured_output_mapping",
    "response_parser_mapping",
    "token_usage_mapping",
    "response_id_mapping",
)
_ADAPTER_CANONICAL_FIELDS = ("provider",) + _ADAPTER_MAPPING_FIELDS
# A frozen adapter object must have EXACTLY this key set (plus adapter_sha256 and
# frozen). No role/fallback/rewrite/primary/secondary fields allowed.
_ADAPTER_EXACT_KEYS = frozenset(_ADAPTER_CANONICAL_FIELDS) | {"adapter_sha256", "frozen"}
_ADAPTER_SEMANTIC_INVARIANTS = (
    "scenario_semantics_unchanged",
    "identity_semantics_unchanged",
    "item_wording_unchanged",
    "response_field_meaning_unchanged",
    "hidden_reasoning_not_requested",
    "model_specific_content_rewrite_forbidden",
)

# --- logging ------------------------------------------------------------------
_LOGGING_DUAL_REQUIRED = (
    "dual_run_group_id",
    "model_contract_hash",
    "provider_adapter_hash",
    "model_sampling_hash",
    "model_budget_hash",
    "model_request_sequence",
    "cross_model_case_pair_id",
    "provider_response_format",
    "provider_token_usage_raw",
    "normalized_token_usage",
    "provider_cost_raw",
    "normalized_estimated_cost",
)
_LOGGING_BASE_REQUIRED = (
    "run_id",
    "run_version",
    "case_id",
    "scenario_id",
    "repeat_index",
    "request_timestamp",
    "response_timestamp",
    "provider",
    "model_id",
    "exact_model_version",
    "request_id_or_response_id",
    "prompt_hash",
    "administration_hash",
    "input_payload_hash",
    "raw_response_hash",
    "parsed_response_hash",
    "validation_status",
    "failure_code",
    "retry_count",
    "token_usage",
    "estimated_cost",
    "package_commit_sha",
)
_LOGGING_RULES = (
    "never_log_api_key",
    "never_log_secret",
    "separate_raw_and_parsed_response",
    "no_silent_overwrite",
    "case_repeat_unique_within_run",
    "block_scoring_if_missing_provenance",
    "every_request_has_provider_and_model_id",
    "cross_model_case_pair_required",
    "per_model_contract_hash_required",
    "single_global_model_hash_forbidden",
)

# --- stop conditions ----------------------------------------------------------
_STOP_BASE_CONDITIONS = (
    "model_version_changed",
    "prompt_hash_mismatch",
    "administration_hash_mismatch",
    "item_set_version_mismatch",
    "budget_hard_limit_reached",
    "unauthorized_execution",
    "secret_detected",
    "source_contract_changed",
)
_STOP_DUAL_CONDITIONS = (
    "any_model_contract_hash_changed",
    "any_provider_adapter_hash_changed",
    "cross_model_case_pair_missing",
    "one_model_request_count_diverged",
    "one_model_budget_limit_reached",
    "one_model_systematic_schema_failure",
)
_STOP_ACTIONS = frozenset({"hard_stop", "stop_and_review"})
# threshold_stop conditions classified as rate (0<t<=1) vs absolute (positive finite).
_STOP_THRESHOLD_RATE_CONDS = frozenset(
    {"schema_failure_rate", "provider_error_rate", "missing_item_rate", "duplicate_response_rate"}
)
_STOP_THRESHOLD_ABS_CONDS = frozenset({"cost_estimation_error"})
_STOP_THRESHOLD_CONDS = _STOP_THRESHOLD_RATE_CONDS | _STOP_THRESHOLD_ABS_CONDS
_STOP_DUAL_POLICY_KEYS = (
    "any_model_hard_stop_stops_all",
    "no_fallback_substitution",
    "resume_requires_human_review_only",
)

# --- retry --------------------------------------------------------------------
_RETRYABLE_KEY = "retryable_codes"
_NON_RETRYABLE_KEY = "non_auto_retryable_codes"

# --- pricing source binding ---------------------------------------------------
_PRICING_SOURCES = {
    "deepseek-v4-pro": {"ds_models_and_pricing", "ds_rate_limit"},
    "gpt-5.6-terra": {"oai_model_page", "oai_models_compare"},
}
_PRICING_REQUIRED_SOURCE = {
    "deepseek-v4-pro": "ds_models_and_pricing",
    "gpt-5.6-terra": ("oai_model_page", "oai_models_compare"),
}

# --- branch CI evidence -------------------------------------------------------
_CI_REQUIRED_JOBS = (
    "windows-latest / Python 3.12",
    "ubuntu-latest / Python 3.12",
)
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

DEEPSEEK_CONCURRENCY = 500

# --- AST security scan --------------------------------------------------------
BANNED_MODULES = frozenset(
    {
        "openai",
        "anthropic",
        "httpx",
        "requests",
        "socket",
        "urllib",
        "os",
        "subprocess",
        "shutil",
        "tempfile",
    }
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
# Write / mutate builtins and stdlib helpers that must never appear.
_WRITE_FUNC_NAMES = frozenset(
    {
        "write_text",
        "write_bytes",
        "unlink",
        "rename",
        "replace",
        "touch",
        "mkdir",
        "rmdir",
        "copy",
        "copy2",
        "copytree",
        "move",
        "rmtree",
    }
)
_ENV_READ_NAMES = frozenset({"getenv", "getenvb"})
_WRITE_OPEN_MODES = ("w", "a", "x", "+")

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_PLACEHOLDERS = frozenset({"", "x", "xx", "placeholder", "todo", "tbd", "none", "null"})
_ROLE_FORBIDDEN_KEYS = ("fallback", "primary_model", "secondary_model", "winner")


class DualPreflightError(RuntimeError):
    """Raised when the dual-model preflight package is inconsistent."""


# --------------------------------------------------------------------------
# Loading + primitive helpers
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
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip().lower() not in _PLACEHOLDERS
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def _nonplaceholder_str(value: Any) -> bool:
    """A real, non-placeholder string (rejects bool and non-str)."""
    return isinstance(value, str) and value.strip().lower() not in _PLACEHOLDERS


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonneg_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_number(value: Any) -> bool:
    """Real finite number: rejects bool, NaN, +inf, -inf."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _positive_number(value: Any) -> bool:
    return _finite_number(value) and value > 0


def _nonneg_number(value: Any) -> bool:
    return _finite_number(value) and value >= 0


def _rate_ok(value: Any) -> bool:
    return _finite_number(value) and 0 < value <= 1


def _is_date(value: Any) -> bool:
    """Real ISO date/datetime parse via fromisoformat (not just a regex)."""
    if not isinstance(value, str) or not value.strip():
        return False
    text = value.strip()
    for parser in (date.fromisoformat, datetime.fromisoformat):
        try:
            parser(text)
            return True
        except ValueError:
            continue
    return False


def _unique_nonempty_str_list(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    seen: list[str] = []
    for v in value:
        if not _nonplaceholder_str(v):
            return False
        seen.append(v)
    return len(seen) == len(set(seen))


def _has_role_forbidden(container: Any) -> bool:
    if not isinstance(container, dict):
        return False
    return any(bad in container for bad in _ROLE_FORBIDDEN_KEYS)


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
    exts = m.get("managed_asset_extensions")
    if not isinstance(exts, list) or set(exts) != {".md", ".yaml", ".py", ".json", ".txt"}:
        raise DualPreflightError("manifest managed_asset_extensions mismatch")
    if "template_files" not in m or not isinstance(m.get("template_files"), list):
        raise DualPreflightError("manifest template_files must be a list")
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
            raise DualPreflightError(f"route_freeze must not carry {forbidden_key!r}")
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
# Official evidence + parameter compatibility loading (from merged decision pkg)
# --------------------------------------------------------------------------


def load_official_evidence() -> dict[str, Any]:
    path = _dual_decision_dir() / "official_evidence.yaml"
    if not path.is_file():
        raise DualPreflightError("official_evidence.yaml missing in decision package")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise DualPreflightError("official_evidence.yaml is not a mapping")
    return data


def load_parameter_compatibility() -> dict[str, Any]:
    path = _dual_decision_dir() / "parameter_compatibility.yaml"
    if not path.is_file():
        raise DualPreflightError("parameter_compatibility.yaml missing in decision package")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise DualPreflightError("parameter_compatibility.yaml is not a mapping")
    return data


def _index_sources(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for s in evidence.get("sources", []):
        if isinstance(s, dict) and _nonplaceholder_str(s.get("source_id")):
            out[str(s["source_id"])] = s
    return out


def _index_model_evidence(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for m in evidence.get("models", []):
        if isinstance(m, dict) and _nonplaceholder_str(m.get("model_id")):
            out[str(m["model_id"])] = m
    return out


def _source_supports_field(src: dict[str, Any], field: str) -> bool:
    supported = src.get("supports_fields", [])
    if not isinstance(supported, list):
        return False
    # allow "endpoint_type.<sub>" prefix matching for the endpoint_type family.
    for sf in supported:
        s = str(sf)
        if s == field:
            return True
        if field == "endpoint_type" and s.startswith("endpoint_type."):
            return True
    return False


# --------------------------------------------------------------------------
# Dual-model decision (selection vs freeze separation) + field typing
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
        if _has_role_forbidden(m):
            raise DualPreflightError("selected model must not carry role/fallback keys")
        got.add((str(m.get("provider")), str(m.get("model_id"))))
    if got != set(EXPECTED_MODELS):
        raise DualPreflightError(f"selected_models must equal {set(EXPECTED_MODELS)}")


def _supplemental_ok(item: Any, field: str, model_id: str) -> bool:
    if not isinstance(item, dict) or set(item) != _SUPPLEMENTAL_ITEM_KEYS:
        return False
    if str(item.get("field")) != field:
        return False
    if str(item.get("model_id")) != model_id:
        return False
    if str(item.get("status")) != "reviewed":
        return False
    if not _nonempty(item.get("value")):
        return False
    if not _nonplaceholder_str(item.get("reviewed_by")):
        return False
    if not _is_date(item.get("reviewed_at")):
        return False
    if not _nonplaceholder_str(item.get("reference")):
        return False
    if not _nonplaceholder_str(item.get("claim_scope")):
        return False
    return True


def _decision_frozen(
    dec: dict[str, Any],
    model_id: str,
    sources: dict[str, dict[str, Any]],
    model_evidence: dict[str, Any],
) -> bool:
    """A single model's decision is frozen only when freeze_status == frozen AND
    every field is correctly typed AND every field is bound to real official
    evidence (or complete supplemental evidence for unresolved fields)."""
    if not isinstance(dec, dict) or set(dec) != _DECISION_EXACT_KEYS:
        return False
    if str(dec.get("freeze_status")) != "frozen":
        return False
    if str(dec.get("provider")) != PROVIDER_OF.get(model_id):
        return False
    if str(dec.get("model_id")) != model_id:
        return False
    if str(dec.get("role")) != "co_primary":
        return False
    provider = PROVIDER_OF[model_id]

    # ---- evidence_binding structure ----
    eb = dec.get("evidence_binding")
    if not isinstance(eb, dict):
        return False
    if str(eb.get("official_evidence_package_hash")) != DUAL_DECISION_PACKAGE_HASH:
        return False
    fsi = eb.get("field_source_ids")
    supplemental = eb.get("supplemental_evidence")
    if not isinstance(fsi, dict) or not isinstance(supplemental, dict):
        return False

    def _binding_sources(field: str) -> list[str] | None:
        raw = fsi.get(field)
        if not isinstance(raw, list) or not raw:
            return None
        ids = [str(x) for x in raw]
        if len(ids) != len(set(ids)):  # no duplicates
            return None
        ev_field = _DECISION_FIELD_TO_EVIDENCE_FIELD.get(field, field)
        for sid in ids:
            src = sources.get(sid)
            if src is None:  # source must actually exist
                return None
            if str(src.get("provider")) != provider:  # provider must match
                return None
            if not _source_supports_field(src, ev_field):  # field must be supported
                return None
        return ids

    # context window: positive int not exceeding official context_window.
    ctx = dec.get("context_window_requirement")
    if not _positive_int(ctx):
        return False
    official_ctx = model_evidence.get("context_window")
    if not _positive_int(official_ctx) or ctx > official_ctx:
        return False
    if _binding_sources("context_window_requirement") is None:
        return False

    # endpoint_type must be one confirmed in official evidence.
    endpoint = dec.get("endpoint_type")
    official_endpoints = {str(e) for e in model_evidence.get("endpoint_type", [])}
    if str(endpoint) not in official_endpoints:
        return False
    if _binding_sources("endpoint_type") is None:
        return False

    # access_method bound.
    if not _nonplaceholder_str(dec.get("access_method")):
        return False
    if _binding_sources("access_method") is None:
        return False

    # structured_output_support must match confirmed evidence and be bool.
    if not isinstance(dec.get("structured_output_support"), bool):
        return False
    official_sos = str(model_evidence.get("structured_output_support"))
    fe_sos = model_evidence.get("field_evidence", {}).get("structured_output_support", {})
    confirmed_sos = str(fe_sos.get("status")) == "confirmed_official_documentation"
    if dec["structured_output_support"] != (confirmed_sos and official_sos == "documented"):
        return False
    if _binding_sources("structured_output_support") is None:
        return False

    # temperature_support / response_id_available bool.
    if not isinstance(dec.get("temperature_support"), bool):
        return False
    if _binding_sources("temperature_support") is None:
        return False
    if not isinstance(dec.get("response_id_available"), bool):
        return False

    # deterministic_seed_support bool.
    if not isinstance(dec.get("deterministic_seed_support"), bool):
        return False

    for f in _MODEL_TRUE_FIELDS:
        if dec.get(f) is not True:
            return False

    # pricing_snapshot_date ISO date; bound to a source.
    ps = dec.get("pricing_snapshot_date")
    if not isinstance(ps, str):
        return False
    try:
        date.fromisoformat(ps.strip())
    except (ValueError, AttributeError):
        return False

    # pricing_source_recorded must reference a REAL source id, not an arbitrary URL.
    psr = dec.get("pricing_source_recorded")
    if not _nonplaceholder_str(psr) or psr not in sources:
        return False
    if str(sources[psr].get("provider")) != provider:
        return False

    # decided_by / decided_at.
    if not _nonplaceholder_str(dec.get("decided_by")):
        return False
    if not _is_date(dec.get("decided_at")):
        return False

    # source_references must be REAL source ids (not example URLs), no dupes.
    refs = dec.get("source_references")
    if not _unique_nonempty_str_list(refs):
        return False
    for r in refs:
        if r not in sources or str(sources[r].get("provider")) != provider:
            return False

    # fields still unresolved / requires_interface_check in the decision package
    # can only be frozen with complete supplemental evidence.
    unresolved = set(map(str, model_evidence.get("unresolved_fields", [])))
    for field in _SUPPLEMENTAL_REQUIRED_FIELDS:
        needs_supp = field in unresolved
        if field == "exact_model_version_or_snapshot":
            needs_supp = "exact_snapshot_available" in unresolved or "exact_snapshot_identifier" in unresolved
        elif field == "deterministic_seed_support":
            needs_supp = "seed_support" in unresolved
        elif field == "response_id_available":
            needs_supp = "response_id_support" in unresolved
        if needs_supp:
            item = supplemental.get(field)
            if not _supplemental_ok(item, field, model_id):
                return False
    return True


def check_model_selection(
    model_sel: dict[str, Any],
    evidence: dict[str, Any] | None = None,
) -> dict[str, bool]:
    if evidence is None:
        evidence = load_official_evidence()
    sources = _index_sources(evidence)
    model_ev = _index_model_evidence(evidence)
    if str(model_sel.get("selection_status")) != "human_selected":
        raise DualPreflightError("selection_status must be human_selected")
    if "selected_model" in model_sel:
        raise DualPreflightError("must not use singular selected_model")
    if model_sel.get("decision_reference_verified") is not True:
        raise DualPreflightError("decision_reference_verified must be true")
    if _has_role_forbidden(model_sel):
        raise DualPreflightError("model_selection must not carry role/fallback keys")
    _check_selected_models(model_sel.get("selected_models"))
    decisions = model_sel.get("decisions", {})
    if not isinstance(decisions, dict) or set(decisions) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("decisions keys must equal the two selected models")
    per_model_frozen: dict[str, bool] = {}
    for mid in EXPECTED_MODEL_IDS:
        dec = decisions[mid]
        if _has_role_forbidden(dec):
            raise DualPreflightError(f"{mid}: decision must not carry role/fallback keys")
        fs = str(dec.get("freeze_status"))
        if fs not in ("unresolved", "frozen"):
            raise DualPreflightError(f"{mid}: illegal freeze_status {fs!r}")
        per_model_frozen[mid] = _decision_frozen(dec, mid, sources, model_ev.get(mid, {}))
    declared_all = model_sel.get("all_models_frozen")
    derived_all = all(per_model_frozen.values())
    if bool(declared_all) != bool(derived_all):
        raise DualPreflightError(
            f"all_models_frozen={declared_all!r} != derived {derived_all!r}"
        )
    return per_model_frozen


# --------------------------------------------------------------------------
# Provider adapter contract + real SHA-256
# --------------------------------------------------------------------------


def _canonical_adapter_payload(adapter: dict[str, Any]) -> dict[str, Any]:
    """Canonical payload: ONLY provider + the six mapping fields. Excludes the
    stored adapter_sha256 (self-reference) and frozen."""
    return {k: adapter.get(k) for k in _ADAPTER_CANONICAL_FIELDS}


def compute_adapter_sha256(adapter: dict[str, Any]) -> str:
    """64-char lowercase SHA-256 over the canonical adapter payload."""
    blob = json.dumps(
        _canonical_adapter_payload(adapter),
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _adapter_frozen(mid: str, a: dict[str, Any]) -> bool:
    """Return whether adapter is validly frozen; raise on structural violations."""
    if not isinstance(a, dict):
        raise DualPreflightError(f"{mid}: adapter must be a mapping")
    if str(a.get("provider")) != PROVIDER_OF[mid]:
        raise DualPreflightError(f"{mid}: adapter provider mismatch")
    if _has_role_forbidden(a):
        raise DualPreflightError(f"{mid}: adapter must not carry role/fallback keys")
    frozen = a.get("frozen")
    if not isinstance(frozen, bool):
        raise DualPreflightError(f"{mid}: adapter frozen must be boolean")
    if not frozen:
        return False
    # exact key set: no scenario_rewrite / role / primary / secondary etc.
    if set(a) != _ADAPTER_EXACT_KEYS:
        extra = set(a) - _ADAPTER_EXACT_KEYS
        missing = _ADAPTER_EXACT_KEYS - set(a)
        raise DualPreflightError(
            f"{mid}: frozen adapter key set invalid (extra={sorted(extra)}, "
            f"missing={sorted(missing)})"
        )
    for f in _ADAPTER_MAPPING_FIELDS:
        if not _nonempty(a.get(f)):
            raise DualPreflightError(f"{mid}: frozen adapter missing mapping {f!r}")
    stored = a.get("adapter_sha256")
    if not isinstance(stored, str) or not _SHA256_RE.match(stored):
        raise DualPreflightError(f"{mid}: adapter_sha256 must be 64 lowercase hex")
    if stored != compute_adapter_sha256(a):
        raise DualPreflightError(f"{mid}: adapter_sha256 does not match canonical payload")
    return True


def check_provider_adapters(adapter: dict[str, Any]) -> dict[str, bool]:
    inv = adapter.get("semantic_invariants", {})
    if not isinstance(inv, dict) or set(inv) != set(_ADAPTER_SEMANTIC_INVARIANTS):
        raise DualPreflightError("adapter semantic_invariants key set invalid")
    for key in _ADAPTER_SEMANTIC_INVARIANTS:
        if inv.get(key) is not True:
            raise DualPreflightError(f"adapter semantic invariant {key!r} must be true")
    ref = adapter.get("compatibility_reference", {})
    if not isinstance(ref, dict):
        raise DualPreflightError("adapter compatibility_reference must be a mapping")
    if str(ref.get("path")) != DUAL_DECISION_COMPAT_PATH:
        raise DualPreflightError("adapter compatibility_reference.path mismatch")
    if str(ref.get("package_hash")) != DUAL_DECISION_PACKAGE_HASH:
        raise DualPreflightError("adapter compatibility_reference package_hash mismatch")
    adapters = adapter.get("adapters", {})
    if not isinstance(adapters, dict) or set(adapters) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("adapters keys must equal the two models")
    per_model_frozen = {mid: _adapter_frozen(mid, adapters[mid]) for mid in EXPECTED_MODEL_IDS}
    declared = adapter.get("all_adapters_frozen")
    if bool(declared) != all(per_model_frozen.values()):
        raise DualPreflightError("all_adapters_frozen != derived")
    return per_model_frozen


# --------------------------------------------------------------------------
# Shared prompt: real content hash + fixed P0 bundle
# --------------------------------------------------------------------------


def _allowed_template_roots() -> list[Path]:
    mc = _mc_dir()
    return [
        (mc / "pa_wu_p0").resolve(),
        (mc / "pa_wu_p1_dual_preflight" / "templates").resolve(),
    ]


def resolve_template(reference: str) -> Path:
    """Resolve a template_reference to a real local file inside a whitelist root.
    Raises DualPreflightError if it escapes the whitelist or does not exist."""
    if not isinstance(reference, str) or not reference.strip():
        raise DualPreflightError(f"invalid template_reference: {reference!r}")
    candidate = (_mc_dir() / reference).resolve()
    roots = _allowed_template_roots()

    def _within(child: Path, root: Path) -> bool:
        if child == root:
            return True
        try:
            child.relative_to(root)
            return True
        except ValueError:
            return False

    if not any(_within(candidate, root) for root in roots):
        raise DualPreflightError(f"template_reference escapes whitelist: {reference!r}")
    if not candidate.is_file():
        raise DualPreflightError(f"template_reference not found: {reference!r}")
    return candidate


def template_content_hash(reference: str) -> str:
    path = resolve_template(reference)
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_bundle_hash(references: list[str]) -> str:
    """Fixed-order composite SHA-256 over the P0 bundle. Reorder / miss / extra /
    content change all alter the hash."""
    payload = []
    for ref in references:
        path = resolve_template(ref)
        payload.append({"path": ref, "content": path.read_text(encoding="utf-8")})
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _segment_ok(name: str, seg: dict[str, Any]) -> bool:
    if not isinstance(seg, dict) or seg.get("frozen") is not True:
        return False
    if not _nonplaceholder_str(seg.get("owner")):
        return False
    if seg.get("change_requires_new_run_version") is not True:
        return False
    sha = str(seg.get("sha256", ""))
    if not _SHA256_RE.match(sha):
        return False

    if name == "item_block":
        # item_block key set exact; binds COMPLETE fixed-order P0 bundle.
        if set(seg) != ITEM_SEGMENT_KEYS:
            return False
        if _nonempty(seg.get("content")) or _nonempty(seg.get("template_reference")):
            return False
        bundle = seg.get("source_bundle")
        if not isinstance(bundle, list) or list(bundle) != list(ITEM_BLOCK_P0_BUNDLE):
            return False
        try:
            actual = source_bundle_hash([str(x) for x in bundle])
        except DualPreflightError:
            return False
        return actual == sha

    # Non-item segments: exact key set; exactly one of content / template_reference.
    if set(seg) != PROMPT_SEGMENT_KEYS:
        return False
    content = seg.get("content")
    tref = seg.get("template_reference")
    # inline content, if present, MUST be a non-placeholder string (reject bool,
    # number, list, mapping). template_reference must be a non-placeholder string.
    has_content = content is not None
    has_tref = tref is not None
    if has_content == has_tref:  # strictly one of the two
        return False
    if has_content:
        if not _nonplaceholder_str(content):
            return False
        actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
    else:
        if not _nonplaceholder_str(tref):
            return False
        try:
            actual = template_content_hash(tref)
        except DualPreflightError:
            return False
    return actual == sha


def check_prompt(prompt: dict[str, Any]) -> bool:
    # top-level key set exact; no per-model prompt keys anywhere.
    if set(prompt) != PROMPT_TOP_LEVEL_KEYS:
        extra = set(prompt) - PROMPT_TOP_LEVEL_KEYS
        raise DualPreflightError(f"prompt top-level keys invalid (extra={sorted(extra)})")
    if set(prompt) & _PROMPT_FORBIDDEN_KEYS:
        raise DualPreflightError("prompt must not carry per-model / adapter keys")
    c = prompt.get("constraints", {})
    if not isinstance(c, dict) or set(c) != PROMPT_CONSTRAINT_KEYS:
        raise DualPreflightError("prompt constraints key set invalid")
    if set(c) & _PROMPT_FORBIDDEN_KEYS:
        raise DualPreflightError("constraints must not carry per-model / override keys")
    if c.get("request_hidden_reasoning") is not False:
        raise DualPreflightError("prompt must set request_hidden_reasoning=false")
    if c.get("request_structured_final_scores_only") is not True:
        raise DualPreflightError("prompt must request structured final scores only")
    if c.get("scenario_model_rewrite_allowed") is not False:
        raise DualPreflightError("scenario_model_rewrite_allowed must be false")
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
    if set(segments) & _PROMPT_FORBIDDEN_KEYS:
        raise DualPreflightError("segments must not carry per-model keys")
    item = segments["item_block"]
    if list(item.get("source_bundle", [])) != list(ITEM_BLOCK_P0_BUNDLE):
        raise DualPreflightError("item_block must bind the fixed-order P0 bundle")
    # prompt_frozen only when every segment validly frozen with a real recomputed sha.
    return all(_segment_ok(name, seg) for name, seg in segments.items())


# --------------------------------------------------------------------------
# Sampling (shared design + per-model), finite ranges
# --------------------------------------------------------------------------


def _sampling_model_frozen(shared: dict[str, Any], sm: dict[str, Any]) -> bool:
    if not isinstance(sm, dict) or sm.get("frozen") is not True:
        return False
    if sm.get("seed_is_determinism_guarantee") is not False:
        return False
    # finite numeric ranges.
    temperature = sm.get("temperature")
    if not (_finite_number(temperature) and temperature >= 0):
        return False
    if not _rate_ok(sm.get("top_p")):
        return False
    if not _positive_int(sm.get("max_output_tokens")):
        return False
    if not _positive_int(sm.get("concurrency")):
        return False
    if not _positive_number(sm.get("request_timeout_seconds")):
        return False
    if not _positive_int(sm.get("planned_request_count")):
        return False
    if sm["concurrency"] > sm["planned_request_count"]:
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
    # shared design.
    pc = shared.get("planned_case_count")
    rp = shared.get("repeats_per_case")
    if not (_positive_int(pc) and _positive_int(rp)):
        return False
    for f in ("scenario_order_policy", "item_order_policy", "repeat_index_policy"):
        if not _nonplaceholder_str(shared.get(f)):
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
# Budget (per-model + aggregate), cost formula
# --------------------------------------------------------------------------

# estimated_cost = (uncached_in/1e6)*uncached_price + (cached_in/1e6)*cached_price
#                  + (out/1e6)*output_price ; allow small fixed decimal tolerance.
_COST_TOLERANCE = 1e-6


def _pricing_inputs_ok(pi: Any) -> bool:
    if not isinstance(pi, dict):
        return False
    counts = ("estimated_cached_input_tokens", "estimated_uncached_input_tokens")
    prices = (
        "uncached_input_price_per_million",
        "cached_input_price_per_million",
        "output_price_per_million",
    )
    for f in counts:
        if not _nonneg_int(pi.get(f)):
            return False
    for f in prices:
        if not _nonneg_number(pi.get(f)):
            return False
    return True


def _official_prices(mid: str, model_evidence: dict[str, Any]) -> dict[str, float] | None:
    """Confirmed cached/uncached/output prices for a model from official evidence."""
    out: dict[str, float] = {}
    for key, ev_key in (
        ("cached", "cached_input_price"),
        ("uncached", "uncached_input_price"),
        ("output", "output_price"),
    ):
        val = model_evidence.get(ev_key)
        if not _nonneg_number(val):
            return None
        out[key] = float(val)
    return out


def _recompute_cost(
    pi: dict[str, Any],
    out_tokens: int,
    input_mult: float = 1.0,
    output_mult: float = 1.0,
    cache_write_mult: float = 1.0,
) -> float:
    unc = pi["estimated_uncached_input_tokens"]
    cac = pi["estimated_cached_input_tokens"]
    return (
        (unc / 1_000_000) * pi["uncached_input_price_per_million"] * input_mult * cache_write_mult
        + (cac / 1_000_000) * pi["cached_input_price_per_million"] * input_mult
        + (out_tokens / 1_000_000) * pi["output_price_per_million"] * output_mult
    )


def _pricing_policy_ok(mid: str, bm: dict[str, Any]) -> tuple[bool, float, float, float]:
    """Validate pricing_policy and return (ok, input_mult, output_mult, cache_write_mult)."""
    pp = bm.get("pricing_policy")
    if not isinstance(pp, dict):
        return (False, 1.0, 1.0, 1.0)
    base_src = pp.get("base_price_source_ids")
    if not isinstance(base_src, list) or not base_src:
        return (False, 1.0, 1.0, 1.0)
    applic = str(pp.get("long_context_pricing_applicability"))
    max_unc = pp.get("maximum_uncached_input_tokens_per_request")
    cache_write = pp.get("explicit_cache_write_used")
    cache_write_mult = 1.0
    if mid == "deepseek-v4-pro":
        # DeepSeek: fixed not_applicable, never applies OpenAI multipliers.
        if applic != "not_applicable":
            return (False, 1.0, 1.0, 1.0)
        return (True, 1.0, 1.0, 1.0)
    # gpt-5.6-terra
    if applic not in _LONG_CONTEXT_APPLICABILITY:
        return (False, 1.0, 1.0, 1.0)  # unresolved etc. -> cannot approve
    if isinstance(cache_write, bool) and cache_write:
        cache_write_mult = GPT_EXPLICIT_CACHE_WRITE_MULTIPLIER
    if applic == "not_applicable":
        # must prove max uncached input per request <= 272000.
        if not _positive_int(max_unc) or max_unc > GPT_LONG_CONTEXT_INPUT_THRESHOLD:
            return (False, 1.0, 1.0, 1.0)
        return (True, 1.0, 1.0, cache_write_mult)
    # applies -> long-context multipliers.
    return (True, GPT_LONG_CONTEXT_INPUT_MULTIPLIER, GPT_LONG_CONTEXT_OUTPUT_MULTIPLIER, cache_write_mult)


def _budget_model_ok(mid: str, bm: dict[str, Any], official: dict[str, float] | None) -> bool:
    if not isinstance(bm, dict):
        return False
    if bm.get("budget_approved") is not True:
        return False
    if str(bm.get("currency")) != "USD" or str(bm.get("pricing_unit")) != "per_million_tokens":
        return False
    if official is None:
        return False
    # pricing evidence reference: package path + provider-locked non-empty source_ids.
    ref = bm.get("pricing_evidence_reference", {})
    if not isinstance(ref, dict):
        return False
    if str(ref.get("package_path")) != DUAL_DECISION_PACKAGE_PATH:
        return False
    sids = ref.get("source_ids", [])
    if not isinstance(sids, list) or not sids:
        return False
    sid_set = set(map(str, sids))
    if not sid_set <= _PRICING_SOURCES[mid]:
        return False
    required = _PRICING_REQUIRED_SOURCE[mid]
    if isinstance(required, tuple):
        if not (sid_set & set(required)):
            return False
    elif required not in sid_set:
        return False
    if not _is_date(bm.get("pricing_snapshot_date")):
        return False
    # pricing_inputs prices MUST equal confirmed official prices exactly.
    pi = bm.get("pricing_inputs")
    if not _pricing_inputs_ok(pi):
        return False
    if abs(pi["cached_input_price_per_million"] - official["cached"]) > _COST_TOLERANCE:
        return False
    if abs(pi["uncached_input_price_per_million"] - official["uncached"]) > _COST_TOLERANCE:
        return False
    if abs(pi["output_price_per_million"] - official["output"]) > _COST_TOLERANCE:
        return False
    # pricing_policy + long-context multipliers.
    policy_ok, in_mult, out_mult, cw_mult = _pricing_policy_ok(mid, bm)
    if not policy_ok:
        return False
    # token counts positive ints; total input relation consistent.
    for f in ("estimated_input_tokens", "estimated_output_tokens", "planned_request_count"):
        if not _positive_int(bm.get(f)):
            return False
    total_in = pi["estimated_cached_input_tokens"] + pi["estimated_uncached_input_tokens"]
    if total_in != bm["estimated_input_tokens"]:
        return False
    # recompute cost with applicable multipliers.
    est = bm.get("estimated_cost")
    if not _nonneg_number(est):
        return False
    recomputed = _recompute_cost(pi, bm["estimated_output_tokens"], in_mult, out_mult, cw_mult)
    if abs(recomputed - est) > _COST_TOLERANCE:
        return False
    # budget hard/soft limits.
    if not _positive_number(bm.get("maximum_model_budget")):
        return False
    if not _positive_number(bm.get("warning_threshold")):
        return False
    if bm["warning_threshold"] > bm["maximum_model_budget"]:
        return False
    if est > bm["maximum_model_budget"]:
        return False
    # rate limits positive.
    for f in ("concurrency_limit", "requests_per_minute_limit", "tokens_per_minute_limit"):
        if not _positive_number(bm.get(f)):
            return False
    if not _nonplaceholder_str(bm.get("budget_owner")):
        return False
    if not _is_date(bm.get("approval_timestamp")):
        return False
    return True


def _aggregate_budget_ok(agg: dict[str, Any], models: dict[str, Any]) -> bool:
    if not isinstance(agg, dict) or agg.get("aggregate_budget_approved") is not True:
        return False
    if str(agg.get("currency")) != "USD":
        return False
    exp_req = sum(models[mid]["planned_request_count"] for mid in EXPECTED_MODEL_IDS)
    if agg.get("total_planned_requests") != exp_req:
        return False
    exp_cost = sum(models[mid]["estimated_cost"] for mid in EXPECTED_MODEL_IDS)
    tot_cost = agg.get("estimated_total_cost")
    if not _nonneg_number(tot_cost) or abs(tot_cost - exp_cost) > _COST_TOLERANCE:
        return False
    max_total = agg.get("maximum_total_budget")
    if not _positive_number(max_total):
        return False
    sum_max = sum(models[mid]["maximum_model_budget"] for mid in EXPECTED_MODEL_IDS)
    if max_total < sum_max:
        return False
    warn = agg.get("warning_total_threshold")
    if not _positive_number(warn) or warn > max_total:
        return False
    if not _nonplaceholder_str(agg.get("aggregate_budget_owner")):
        return False
    if not _is_date(agg.get("aggregate_approval_timestamp")):
        return False
    return True


def check_budget(
    budget: dict[str, Any],
    sampling_models: dict[str, Any],
    evidence: dict[str, Any] | None = None,
) -> dict[str, bool]:
    if evidence is None:
        evidence = load_official_evidence()
    model_ev = _index_model_evidence(evidence)
    models = budget.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("budget models keys must equal the two models")
    # cross-provider price rules forbidden; enforce per-model source binding early.
    for mid in EXPECTED_MODEL_IDS:
        ref = models[mid].get("pricing_evidence_reference", {})
        sids = set(map(str, ref.get("source_ids", []))) if isinstance(ref, dict) else set()
        if sids and not sids <= _PRICING_SOURCES[mid]:
            raise DualPreflightError(f"{mid}: pricing source_ids cross-provider")
    # DeepSeek concurrency must not exceed 500.
    ds = models["deepseek-v4-pro"]
    cl = ds.get("concurrency_limit")
    if cl is not None and (not _positive_number(cl) or cl > DEEPSEEK_CONCURRENCY):
        raise DualPreflightError("deepseek concurrency_limit must not exceed 500")
    per_model: dict[str, bool] = {}
    for mid in EXPECTED_MODEL_IDS:
        official = _official_prices(mid, model_ev.get(mid, {}))
        per_model[mid] = _budget_model_ok(mid, models[mid], official)
        # As soon as a single model is budget_approved=true, immediately cross-check
        # its sampling alignment (do NOT wait for the other model / aggregate).
        if models[mid].get("budget_approved") is True and per_model[mid]:
            sm = sampling_models.get(mid, {})
            if models[mid]["planned_request_count"] != sm.get("planned_request_count"):
                raise DualPreflightError(f"{mid}: budget request count != sampling")
            if sm.get("concurrency") is not None and models[mid].get("concurrency_limit") is not None:
                if sm["concurrency"] > models[mid]["concurrency_limit"]:
                    raise DualPreflightError(f"{mid}: sampling concurrency > concurrency_limit")
    agg = budget.get("aggregate", {})
    agg_ok = all(per_model.values()) and _aggregate_budget_ok(agg, models)
    declared = budget.get("all_model_budgets_approved")
    if bool(declared) != agg_ok:
        raise DualPreflightError("all_model_budgets_approved != derived")
    return per_model


# --------------------------------------------------------------------------
# Retry / logging / stop / privacy / environment
# --------------------------------------------------------------------------


def _retry_model_frozen(mid: str, rm: dict[str, Any], shared: dict[str, Any]) -> bool:
    if not isinstance(rm, dict):
        raise DualPreflightError(f"{mid}: retry model must be a mapping")
    if str(rm.get("provider")) != PROVIDER_OF[mid]:
        raise DualPreflightError(f"{mid}: retry provider mismatch")
    frozen = rm.get("frozen")
    if not isinstance(frozen, bool):
        raise DualPreflightError(f"{mid}: retry frozen must be boolean")
    if not frozen:
        return False
    if not _positive_int(shared.get("max_attempts")):
        return False
    if not _nonempty(shared.get("exponential_backoff")):
        return False
    if not _nonempty(rm.get("provider_error_taxonomy")):
        return False
    retryable = rm.get(_RETRYABLE_KEY)
    non_retry = rm.get(_NON_RETRYABLE_KEY)
    if not _unique_nonempty_str_list(retryable):
        return False
    if not _unique_nonempty_str_list(non_retry):
        return False
    if set(map(str, retryable)) & set(map(str, non_retry)):
        return False
    return True


def check_retry(retry: dict[str, Any]) -> dict[str, bool]:
    models = retry.get("models", {})
    if not isinstance(models, dict) or set(models) != set(EXPECTED_MODEL_IDS):
        raise DualPreflightError("retry models keys must equal the two models")
    shared = retry.get("shared_policy", {})
    if not isinstance(shared, dict):
        raise DualPreflightError("retry shared_policy must be a mapping")
    per_model = {mid: _retry_model_frozen(mid, models[mid], shared) for mid in EXPECTED_MODEL_IDS}
    declared = retry.get("all_model_retry_policies_frozen")
    if bool(declared) != all(per_model.values()):
        raise DualPreflightError("all_model_retry_policies_frozen != derived")
    return per_model


def compute_logging_contract_hash(logging_c: dict[str, Any]) -> str:
    """64-char SHA-256 over the canonical logging payload EXCLUDING the stored
    hash and the frozen flag (avoids self-reference)."""
    payload = {k: v for k, v in logging_c.items() if k not in ("logging_contract_hash", "frozen")}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def check_logging_frozen(logging_c: dict[str, Any]) -> bool:
    rules = logging_c.get("rules", {})
    if not isinstance(rules, dict) or set(rules) != set(_LOGGING_RULES):
        raise DualPreflightError("logging rules key set invalid")
    for rule in _LOGGING_RULES:
        if rules.get(rule) is not True:
            raise DualPreflightError(f"logging rule {rule!r} must be true")
    base = logging_c.get("base_required_log_fields", [])
    if not isinstance(base, list) or len(base) != len(set(base)):
        raise DualPreflightError("logging base fields must be a unique list")
    if not set(_LOGGING_BASE_REQUIRED).issubset(set(base)):
        raise DualPreflightError("logging missing original single-model fields")
    dual = logging_c.get("dual_model_required_log_fields", [])
    if not isinstance(dual, list) or len(dual) != len(set(dual)):
        raise DualPreflightError("logging dual fields must be a unique list")
    if not set(_LOGGING_DUAL_REQUIRED).issubset(set(dual)):
        raise DualPreflightError("logging missing dual-model provenance fields")
    if logging_c.get("frozen") is not True:
        return False
    # when frozen: owner / version non-placeholder.
    for f in ("frozen_by", "logging_contract_version"):
        if not _nonplaceholder_str(logging_c.get(f)):
            return False
    # logging_contract_hash MUST be a 64-char SHA-256 == recomputed canonical hash.
    stored = logging_c.get("logging_contract_hash")
    if not isinstance(stored, str) or not _SHA256_RE.match(stored):
        return False
    return stored == compute_logging_contract_hash(logging_c)


def check_privacy_completed(logging_c: dict[str, Any]) -> bool:
    pr = logging_c.get("privacy_review", {})
    return (
        isinstance(pr, dict)
        and str(pr.get("status")) == "completed"
        and _nonplaceholder_str(pr.get("reviewed_by"))
        and _is_date(pr.get("reviewed_at"))
    )


def check_stop_frozen(stop: dict[str, Any]) -> bool:
    immediate = stop.get("immediate_stop", [])
    if not isinstance(immediate, list):
        raise DualPreflightError("stop immediate_stop must be a list")
    conds = [str(e.get("condition")) for e in immediate if isinstance(e, dict)]
    if len(conds) != len(set(conds)):
        raise DualPreflightError("stop conditions must be unique")
    cond_set = set(conds)
    # immediate condition set must be EXACTLY base + dual (not just a subset).
    if cond_set != set(_STOP_BASE_CONDITIONS) | set(_STOP_DUAL_CONDITIONS):
        raise DualPreflightError("immediate_stop condition set must equal base+dual exactly")
    threshold = stop.get("threshold_stop", [])
    if not isinstance(threshold, list):
        raise DualPreflightError("stop threshold_stop must be a list")
    tconds = [str(e.get("condition")) for e in threshold if isinstance(e, dict)]
    if len(tconds) != len(set(tconds)):
        raise DualPreflightError("threshold conditions must be unique")
    if set(tconds) != _STOP_THRESHOLD_CONDS:
        raise DualPreflightError("threshold_stop condition set must be exact")
    for e in immediate + threshold:
        if isinstance(e, dict) and str(e.get("action")) not in _STOP_ACTIONS:
            raise DualPreflightError(f"illegal stop action: {e.get('action')!r}")
    policy = stop.get("dual_model_stop_policy", {})
    if not isinstance(policy, dict):
        raise DualPreflightError("stop dual_model_stop_policy must be a mapping")
    for key in _STOP_DUAL_POLICY_KEYS:
        if policy.get(key) is not True:
            raise DualPreflightError(f"dual_model_stop_policy.{key} must be true")
    # frozen state strictly derived from ALL conditions being resolved with valid values.
    if stop.get("frozen") is not True:
        return False
    for e in threshold:
        if not isinstance(e, dict):
            return False
        if str(e.get("threshold_status")) != "resolved":
            return False
        cond = str(e.get("condition"))
        t = e.get("threshold")
        if cond in _STOP_THRESHOLD_RATE_CONDS:
            if not _rate_ok(t):  # 0 < t <= 1
                return False
        elif cond in _STOP_THRESHOLD_ABS_CONDS:
            if not _positive_number(t):
                return False
        else:
            return False
    return True


def check_environment_reviewed(env: dict[str, Any], expected_subject_hash: str) -> bool:
    """environment_review_completed is strictly derived from whether branch_ci is a
    complete, valid structured CI evidence mapping whose validated_subject_hash
    equals the current ci_subject_hash. Inherited baseline CI can NOT pass."""
    ci = env.get("branch_ci")
    ci_ok = _branch_ci_ok(ci, expected_subject_hash)
    declared = env.get("environment_review_completed")
    if bool(declared) != ci_ok:
        raise DualPreflightError("environment_review_completed != branch_ci evidence")
    return ci_ok


def _branch_ci_ok(ci: Any, expected_subject_hash: str) -> bool:
    if not isinstance(ci, dict):
        return False
    if str(ci.get("workflow")) != "CI":
        return False
    if not _positive_int(ci.get("run_number")):
        return False
    if not _positive_int(ci.get("run_id")):
        return False
    if str(ci.get("status")) != "completed":
        return False
    if str(ci.get("conclusion")) != "success":
        return False
    head = ci.get("verified_head_sha")
    if not isinstance(head, str) or not _SHA40_RE.match(head):
        return False
    jobs = ci.get("jobs")
    if not isinstance(jobs, dict):
        return False
    for job in _CI_REQUIRED_JOBS:
        if str(jobs.get(job)) != "success":
            return False
    # validated_subject_hash must equal the CURRENT ci_subject_hash: any contract /
    # validator / template change invalidates old CI evidence; merely rewriting the
    # branch_ci record does not (subject hash excludes branch_ci + authorization).
    vsh = ci.get("validated_subject_hash")
    if not isinstance(vsh, str) or vsh != expected_subject_hash:
        return False
    return True


# --------------------------------------------------------------------------
# Per-model + shared + aggregate + package hashes (canonical structures)
# --------------------------------------------------------------------------


def _hash16(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def compute_per_model_contract_hashes(contracts: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Each model's hash covers ONLY that model's sub-contracts (decision,
    adapter, sampling, budget, retry) using canonical structures. Changing one
    model's sub-contract changes only that model's hash (and the aggregate)."""
    out: dict[str, str] = {}
    adapters = contracts["provider_adapter_contract.yaml"]["adapters"]
    for mid in EXPECTED_MODEL_IDS:
        payload = {
            "decision": contracts["model_selection_decision.yaml"]["decisions"][mid],
            # adapter contributes its CANONICAL payload only (never the stored hash).
            "adapter": _canonical_adapter_payload(adapters[mid]),
            "sampling": contracts["sampling_and_repeat_contract.yaml"]["models"][mid],
            "budget": contracts["budget_and_rate_limit_contract.yaml"]["models"][mid],
            "retry": contracts["retry_and_recovery_contract.yaml"]["models"][mid],
        }
        out[mid] = _hash16(payload)
    return out


def compute_provider_adapter_hashes(contracts: dict[str, dict[str, Any]]) -> dict[str, str]:
    """16-char digest DERIVED from the canonical adapter payload (never from the
    stored adapter_sha256, which would be self-referential)."""
    adapters = contracts["provider_adapter_contract.yaml"]["adapters"]
    return {mid: _hash16(_canonical_adapter_payload(adapters[mid])) for mid in EXPECTED_MODEL_IDS}


def compute_shared_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    """Shared (non per-model) design: route, full prompt, adapter semantic
    invariants + compatibility_reference, shared sampling design, shared retry
    policy, logging, stop."""
    adapter = contracts["provider_adapter_contract.yaml"]
    payload = {
        "route": contracts["route_freeze.yaml"],
        "prompt": contracts["prompt_freeze_contract.yaml"],
        "adapter_semantic_invariants": adapter.get("semantic_invariants"),
        "adapter_compatibility_reference": adapter.get("compatibility_reference"),
        "shared_sampling": contracts["sampling_and_repeat_contract.yaml"].get("shared_design"),
        "shared_retry": contracts["retry_and_recovery_contract.yaml"].get("shared_policy"),
        "logging": contracts["provenance_and_logging_contract.yaml"],
        "stop": contracts["stop_conditions.yaml"],
    }
    return _hash16(payload)


def compute_aggregate_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    """Aggregate covers per-model hashes, provider adapter hashes, shared hash,
    sampling.aggregate, budget.aggregate, the FULL authorization_gate contract,
    and the FULL environment_acceptance contract (incl. branch_ci)."""
    per_model = compute_per_model_contract_hashes(contracts)
    adapters = compute_provider_adapter_hashes(contracts)
    shared = compute_shared_contract_hash(contracts)
    payload = {
        "per_model": per_model,
        "provider_adapter": adapters,
        "shared": shared,
        "sampling_aggregate": contracts["sampling_and_repeat_contract.yaml"].get("aggregate"),
        "budget_aggregate": contracts["budget_and_rate_limit_contract.yaml"].get("aggregate"),
        "authorization_gate": contracts["authorization_gate.yaml"],
        "environment_acceptance": contracts["environment_acceptance.yaml"],
    }
    return _hash16(payload)


def _template_files(manifest: dict[str, Any]) -> list[str]:
    tf = manifest.get("template_files", [])
    if not isinstance(tf, list):
        raise DualPreflightError("manifest template_files must be a list")
    return [str(x) for x in tf]


def _managed_asset_payload(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Fixed-order canonical payload of every managed asset (relative_path + raw
    UTF-8 content): README, manifest, all contract files, validator, all
    template_files. Order is deterministic (README, manifest, sorted contracts,
    validator, sorted template_files)."""
    ordered: list[str] = ["README.md", "preflight_manifest.yaml"]
    ordered += sorted(CONTRACT_FILES)
    ordered.append("validate_dual_preflight.py")
    ordered += sorted(_template_files(manifest))
    payload: list[dict[str, str]] = []
    for rel in ordered:
        p = PACKAGE_DIR / rel
        if not p.is_file():
            raise DualPreflightError(f"managed asset missing: {rel}")
        payload.append({"path": rel, "content": p.read_text(encoding="utf-8")})
    return payload


def compute_package_hash(contracts: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> str:
    """Package hash covers README, manifest, ALL contract files, validator, and
    ALL template_files, each as relative_path + raw UTF-8 content in fixed order."""
    payload = {"managed_assets": _managed_asset_payload(manifest)}
    return _hash16(payload)


# --------------------------------------------------------------------------
# Stable CI subject hash (excludes CI evidence + authorization to avoid self-ref)
# --------------------------------------------------------------------------

_MANIFEST_STRUCTURAL_KEYS = (
    "manifest_id",
    "route_id",
    "package_status",
    "selected_model_ids",
    "role_policy",
    "all_or_nothing_execution",
    "source_packages",
    "migration_declarations",
    "files",
    "contract_files",
    "managed_asset_extensions",
    "template_files",
)


def compute_ci_subject_hash(
    contracts: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> str:
    """Stable subject hash over everything that CI actually validates, EXCLUDING
    environment_acceptance.branch_ci / environment_review_completed and all
    authorization status fields. Recording CI evidence therefore does not change
    the subject hash (no self-reference); any contract / validator / template
    change does change it and invalidates prior CI evidence."""
    validator_path = PACKAGE_DIR / "validate_dual_preflight.py"
    if not validator_path.is_file():
        raise DualPreflightError("validator source missing for ci subject hash")
    manifest_structural = {k: manifest.get(k) for k in _MANIFEST_STRUCTURAL_KEYS}
    payload = {
        "manifest_structural": manifest_structural,
        "route": contracts["route_freeze.yaml"],
        "model_selection": contracts["model_selection_decision.yaml"],
        "provider_adapter": contracts["provider_adapter_contract.yaml"],
        "prompt": contracts["prompt_freeze_contract.yaml"],
        "sampling": contracts["sampling_and_repeat_contract.yaml"],
        "budget": contracts["budget_and_rate_limit_contract.yaml"],
        "retry": contracts["retry_and_recovery_contract.yaml"],
        "logging": contracts["provenance_and_logging_contract.yaml"],
        "stop": contracts["stop_conditions.yaml"],
        "validator_source": validator_path.read_text(encoding="utf-8"),
        "template_assets": [
            {"path": rel, "content": (PACKAGE_DIR / rel).read_text(encoding="utf-8")}
            for rel in sorted(_template_files(manifest))
            if (PACKAGE_DIR / rel).is_file()
        ],
    }
    return _hash16(payload)


# --------------------------------------------------------------------------
# Authorization state machine (single human source)
# --------------------------------------------------------------------------

VALID_AUTH_STATUSES = frozenset({"blocked", "authorized"})
_AUTH_FORBIDDEN_KEYS = ("per_model_authorization", "authorized_model_ids")


def check_required_gates_exact(auth: dict[str, Any]) -> None:
    gates = auth.get("required_gates", [])
    if not isinstance(gates, list):
        raise DualPreflightError("authorization required_gates must be a list")
    if list(gates) != list(REQUIRED_GATES):
        raise DualPreflightError("authorization required_gates must equal REQUIRED_GATES exactly (ordered, no dupes)")
    if list(auth.get("required_model_ids", [])) != list(EXPECTED_MODEL_IDS):
        raise DualPreflightError("authorization required_model_ids mismatch (ordered, no dupes)")
    if auth.get("all_or_nothing_execution") is not True:
        raise DualPreflightError("authorization all_or_nothing_execution must be true")
    for bad in _AUTH_FORBIDDEN_KEYS:
        if bad in auth:
            raise DualPreflightError(f"authorization must not carry {bad!r}")


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
        if not _nonplaceholder_str(auth.get("authorized_by")):
            raise DualPreflightError("authorized requires authorized_by")
        if not _is_date(auth.get("authorized_at")):
            raise DualPreflightError("authorized_at must be an ISO date/datetime")
        return "authorized"
    if flag is True:
        raise DualPreflightError("blocked status must not carry flag=true")
    if _nonempty(auth.get("authorized_by")) or _nonempty(auth.get("authorized_at")):
        raise DualPreflightError("blocked status must have empty authorized_by/at")
    return "blocked"


# --------------------------------------------------------------------------
# AST security scan (write / mutate / subprocess / os / env)
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

    def _open_mode_node(node: ast.Call, mode_index: int) -> tuple[bool, Any]:
        """Return (present, mode_ast_node) for open-style calls. mode_index is the
        positional index of the mode argument (1 for builtins/io.open, 0 for
        Path.open). mode= keyword takes precedence."""
        for kw in node.keywords:
            if kw.arg == "mode":
                return (True, kw.value)
        if len(node.args) > mode_index:
            return (True, node.args[mode_index])
        return (False, None)

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
        # attribute reads of banned modules (e.g. os.environ, subprocess.PIPE).
        if isinstance(node, ast.Attribute):
            cur: Any = node
            while isinstance(cur, ast.Attribute):
                cur = cur.value
            if isinstance(cur, ast.Name) and cur.id in BANNED_MODULES:
                raise DualPreflightError(f"banned module attribute {cur.id!r} in {path.name}")
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        short = name.rsplit(".", 1)[-1]
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
        # write / mutate helpers anywhere.
        if short in _WRITE_FUNC_NAMES:
            raise DualPreflightError(f"file write/mutate call {name!r} in {path.name}")
        # getattr(obj, "<write method>") is forbidden (dynamic write dispatch).
        if short == "getattr":
            for a in args:
                if a in _WRITE_FUNC_NAMES:
                    raise DualPreflightError(f"getattr write dispatch {a!r} in {path.name}")
        # open-style calls: only explicit constant r / rb / rt allowed; a missing
        # mode means default 'r' (ok); a variable / non-static mode fails.
        is_open = name in ("open", "io.open") or name.endswith(".open")
        if is_open:
            mode_index = 0 if name.endswith(".open") and name not in ("io.open",) else 1
            present, mode_node = _open_mode_node(node, mode_index)
            if present:
                if not (isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str)):
                    raise DualPreflightError(f"non-static open mode in {path.name}")
                if mode_node.value not in ("r", "rb", "rt"):
                    raise DualPreflightError(f"non-read open mode {mode_node.value!r} in {path.name}")
            # missing mode -> default 'r' (allowed).
        if name.startswith("subprocess.") or short in ("run", "Popen", "call", "check_output"):
            raise DualPreflightError(f"subprocess/shell execution {name!r} in {path.name}")
        if name in ("open", "io.open", "Path") or name.endswith(".open"):
            for a in args:
                if any(frag in a for frag in FORBIDDEN_PATH_FRAGMENTS):
                    raise DualPreflightError(f"forbidden R2/R3 path access {a!r} in {path.name}")
        if short in _ENV_READ_NAMES or name.endswith("environ.get"):
            raise DualPreflightError(f"environment variable read in {path.name}")


def check_package_python_scan() -> None:
    """Recursively scan EVERY python file in the package (rglob), not just this
    validator and not only the top level."""
    for py in sorted(PACKAGE_DIR.rglob("*.py")):
        scan_python_source(py)


def check_validator_self_scan() -> None:
    scan_python_source(PACKAGE_DIR / "validate_dual_preflight.py")


def check_original_preflight_untouched() -> None:
    if not (_single_preflight_dir() / "validate_preflight.py").is_file():
        raise DualPreflightError("original single-model preflight must remain present")


# --------------------------------------------------------------------------
# Recursive managed asset inventory
# --------------------------------------------------------------------------

# only these nested directories may exist (declared in manifest).
_ALLOWED_NESTED_DIRS = frozenset({"templates"})


def check_managed_assets(manifest: dict[str, Any]) -> None:
    """Recursively verify the package asset inventory:
    - manifest.files is an ordered, no-duplicate list equal to the top-level files;
    - actual top-level files exactly equal manifest.files;
    - only declared nested directories (e.g. templates) may exist;
    - every asset under templates is listed in template_files;
    - no undeclared files, no undeclared nested dirs, no symlinks."""
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise DualPreflightError("manifest.files must be a list")
    if list(files) != list(REQUIRED_FILES):
        raise DualPreflightError("manifest.files must equal REQUIRED_FILES in fixed order")
    if len(files) != len(set(files)):
        raise DualPreflightError("manifest.files must have no duplicates")

    template_files = set(_template_files(manifest))

    # walk the package tree.
    actual_top_files: set[str] = set()
    actual_nested_dirs: set[str] = set()
    actual_template_assets: set[str] = set()
    for p in sorted(PACKAGE_DIR.rglob("*")):
        if p.is_symlink():
            raise DualPreflightError(f"symlink not allowed: {p.name}")
        rel = p.relative_to(PACKAGE_DIR).as_posix()
        # ignore pycache artefacts.
        if "__pycache__" in rel.split("/"):
            continue
        if p.is_dir():
            top = rel.split("/")[0]
            if "/" not in rel:  # a top-level directory
                if top not in _ALLOWED_NESTED_DIRS:
                    raise DualPreflightError(f"undeclared nested directory: {rel}")
                actual_nested_dirs.add(top)
            continue
        # a file.
        if "/" not in rel:
            actual_top_files.add(rel)
        else:
            top = rel.split("/")[0]
            if top not in _ALLOWED_NESTED_DIRS:
                raise DualPreflightError(f"undeclared nested file: {rel}")
            actual_template_assets.add(rel)

    if actual_top_files != set(REQUIRED_FILES):
        extra = actual_top_files - set(REQUIRED_FILES)
        missing = set(REQUIRED_FILES) - actual_top_files
        raise DualPreflightError(
            f"top-level files mismatch (extra={sorted(extra)}, missing={sorted(missing)})"
        )
    # every actual template asset must be declared, and every declared present.
    if actual_template_assets != template_files:
        undeclared = actual_template_assets - template_files
        missing = template_files - actual_template_assets
        raise DualPreflightError(
            f"template_files mismatch (undeclared={sorted(undeclared)}, missing={sorted(missing)})"
        )


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
    budget_agg = contracts["budget_and_rate_limit_contract.yaml"].get("aggregate", {})
    return {
        "route_frozen": bool(
            route.get("route_id") == "R1"
            and str(route.get("mock_package_hash")) == R1_MOCK_HASH
        ),
        "dual_model_decision_verified": bool(decision_verified),
        "all_models_frozen": all(per_model_frozen.values()),
        "provider_adapters_frozen": all(per_adapter_frozen.values()),
        "prompt_frozen": bool(prompt_frozen),
        "all_model_sampling_frozen": all(per_sampling_frozen.values()),
        "all_model_budgets_approved": all(per_budget_ok.values())
        and budget_agg.get("aggregate_budget_approved") is True,
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
    check_package_python_scan()
    check_original_preflight_untouched()
    manifest = check_manifest()
    check_managed_assets(manifest)

    contracts = {n: _load_yaml(n) for n in CONTRACT_FILES}
    check_route_boundary(contracts["route_freeze.yaml"])

    evidence = load_official_evidence()
    load_parameter_compatibility()  # structural presence check (read-only)

    # source verifications
    mock_hash = verify_r1_mock()
    mock_ok = mock_hash == R1_MOCK_HASH
    single_ok = verify_single_preflight_source()
    decision_ok = verify_dual_decision_source()
    source_ok = mock_ok and single_ok and decision_ok

    per_model_frozen = check_model_selection(contracts["model_selection_decision.yaml"], evidence)
    per_adapter_frozen = check_provider_adapters(contracts["provider_adapter_contract.yaml"])
    prompt_frozen = check_prompt(contracts["prompt_freeze_contract.yaml"])
    per_sampling_frozen = check_sampling(contracts["sampling_and_repeat_contract.yaml"])
    per_budget_ok = check_budget(
        contracts["budget_and_rate_limit_contract.yaml"],
        contracts["sampling_and_repeat_contract.yaml"]["models"],
        evidence,
    )
    per_retry_frozen = check_retry(contracts["retry_and_recovery_contract.yaml"])
    logging_frozen = check_logging_frozen(contracts["provenance_and_logging_contract.yaml"])
    privacy_completed = check_privacy_completed(contracts["provenance_and_logging_contract.yaml"])
    stop_frozen = check_stop_frozen(contracts["stop_conditions.yaml"])
    ci_subject_hash = compute_ci_subject_hash(contracts, manifest)
    env_reviewed = check_environment_reviewed(contracts["environment_acceptance.yaml"], ci_subject_hash)

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
        "ci_subject_hash": ci_subject_hash,
        "package_hash": compute_package_hash(contracts, manifest),
        "resolved_gates": resolved_gates,
        "blocking_gates": blocking_gates,
    }


def main() -> None:  # pragma: no cover
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
