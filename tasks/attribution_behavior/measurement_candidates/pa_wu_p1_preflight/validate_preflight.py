"""Static, offline validator for the PA-Wu R1 P1 preflight gate package.

STRICT boundaries:
- NO network I/O; NEVER reads an API key; NEVER imports a real-model SDK;
- NEVER executes a model; NEVER produces model output; NEVER rewrites a contract;
- NEVER auto-enables authorization.

Authorization state has a SINGLE source of truth: ``authorization_gate.yaml``
(authorization_status / real_model_execution_authorized / authorized_by /
authorized_at / required_gates). ``p1_execution_status`` is NOT persisted in any
contract or manifest; it is derived only by ``build_preflight_report()``.
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


def _mc_dir() -> Path:
    """The measurement_candidates dir, derived dynamically from PACKAGE_DIR so
    tests can relocate the package (and its P0 / templates roots) into tmp."""
    return PACKAGE_DIR.parent


R1_MOCK_HASH = "7c83def4c93ad26f"

# The complete, fixed-order P0 source bundle that item_block must bind to.
# Covers both the combined and wu19_only sources.
ITEM_BLOCK_P0_BUNDLE = (
    "pa_wu_p0/items_pa_2024.yaml",
    "pa_wu_p0/items_wu_shen_2026.yaml",
    "pa_wu_p0/forms.yaml",
)

def _r1_mock_dir() -> Path:
    return _mc_dir() / "pa_wu_r1_mock"


def _p0_dir() -> Path:
    return _mc_dir() / "pa_wu_p0"


_PLACEHOLDERS = frozenset({"", "x", "xx", "placeholder", "todo", "tbd", "none", "null"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

REQUIRED_FILES = (
    "README.md",
    "preflight_manifest.yaml",
    "route_freeze.yaml",
    "model_selection_decision.yaml",
    "prompt_freeze_contract.yaml",
    "sampling_and_repeat_contract.yaml",
    "budget_and_rate_limit_contract.yaml",
    "retry_and_recovery_contract.yaml",
    "provenance_and_logging_contract.yaml",
    "stop_conditions.yaml",
    "authorization_gate.yaml",
    "environment_acceptance.yaml",
    "validate_preflight.py",
)

CONTRACT_FILES = (
    "route_freeze.yaml",
    "model_selection_decision.yaml",
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
    "model_frozen",
    "prompt_frozen",
    "sampling_frozen",
    "budget_approved",
    "retry_policy_frozen",
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

# Complete expected frozen-field set for the model selection decision.
MODEL_FROZEN_FIELDS = (
    "provider",
    "model_id",
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
)
_MODEL_STRING_FIELDS = (
    "provider",
    "model_id",
    "exact_model_version_or_snapshot",
    "endpoint_type",
    "access_method",
    "pricing_snapshot_date",
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

REQUIRED_LOG_FIELDS = (
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

IMMEDIATE_STOP_CONDITIONS = (
    "model_version_changed",
    "prompt_hash_mismatch",
    "administration_hash_mismatch",
    "item_set_version_mismatch",
    "budget_hard_limit_reached",
    "unauthorized_execution",
    "secret_detected",
    "source_contract_changed",
)
THRESHOLD_STOP_CONDITIONS = (
    "schema_failure_rate",
    "provider_error_rate",
    "missing_item_rate",
    "duplicate_response_rate",
    "cost_estimation_error",
)
# Rate-style thresholds constrained to (0, 1].
_RATE_STOP_CONDITIONS = frozenset(THRESHOLD_STOP_CONDITIONS)
_LEGAL_STOP_ACTIONS = frozenset({"hard_stop", "stop_and_review", "pause_and_alert"})

# Banned modules for the AST self-scan and package scan.
BANNED_MODULES = frozenset(
    {"openai", "anthropic", "httpx", "requests", "socket", "urllib"}
)
# Forbidden R2/R3 asset path fragments.
FORBIDDEN_PATH_FRAGMENTS = (
    "pa_wu_p1_prep",
    "provisional",
    "adaptation_candidates",
    "ai_human",
    "zh_cn",
    "zh-cn",
)
_NETWORK_CLI = ("curl", "wget", "powershell", "pwsh", "Invoke-WebRequest", "iwr")


class PreflightError(RuntimeError):
    """Raised when the preflight package is structurally inconsistent."""


# --------------------------------------------------------------------------
# Loading + value helpers
# --------------------------------------------------------------------------


def _load_yaml_from(base: Path, name: str) -> dict[str, Any]:
    with (base / name).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PreflightError(f"{name}: expected a mapping at top level")
    return data


def _load_yaml(name: str) -> dict[str, Any]:
    return _load_yaml_from(PACKAGE_DIR, name)


def load_manifest() -> dict[str, Any]:
    return _load_yaml("preflight_manifest.yaml")


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in _PLACEHOLDERS
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True


def _finite_number(value: Any) -> bool:
    """Real finite number: rejects bool, NaN, +inf, -inf."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _positive_number(value: Any) -> bool:
    return _finite_number(value) and value > 0


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


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


def _rate_ok(value: Any) -> bool:
    return _finite_number(value) and 0 < value <= 1


# --------------------------------------------------------------------------
# Template resolver (local whitelist only, no network, no escape)
# --------------------------------------------------------------------------


def _allowed_template_roots() -> list[Path]:
    # Roots are derived dynamically from PACKAGE_DIR (via _mc_dir) so a
    # relocated package (e.g. under tmp_path in tests) resolves against its OWN
    # sibling P0 source and its OWN controlled-template directory.
    mc = _mc_dir()
    return [
        (mc / "pa_wu_p0").resolve(),
        (mc / "pa_wu_p1_preflight" / "templates").resolve(),
    ]


def resolve_template(reference: str) -> Path:
    """Resolve a template_reference to a real local file inside a whitelist root.

    Raises PreflightError if it escapes the whitelist or does not exist.
    """
    if not isinstance(reference, str) or not reference.strip():
        raise PreflightError(f"invalid template_reference: {reference!r}")
    # Reference is relative to the (dynamic) measurement_candidates dir.
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
        raise PreflightError(f"template_reference escapes whitelist: {reference!r}")
    if not candidate.is_file():
        raise PreflightError(f"template_reference not found: {reference!r}")
    return candidate


def template_content_hash(reference: str) -> str:
    """sha256 of the normalized (utf-8 text) content of a resolved template."""
    path = resolve_template(reference)
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_bundle_hash(references: list[str]) -> str:
    """Fixed-order composite SHA-256 over a bundle of local P0 sources.

    Each entry contributes {relative_path, content} (normalized utf-8). The
    canonical JSON preserves order (list, not set), so a reordering, a missing
    or extra entry, or any content change alters the hash.
    """
    payload = []
    for ref in references:
        path = resolve_template(ref)
        payload.append(
            {"path": ref, "content": path.read_text(encoding="utf-8")}
        )
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Structural checks
# --------------------------------------------------------------------------


def check_required_files() -> None:
    missing = [n for n in REQUIRED_FILES if not (PACKAGE_DIR / n).is_file()]
    if missing:
        raise PreflightError(f"missing required preflight files: {missing}")


def check_route_boundary(route: dict[str, Any]) -> None:
    expected = {
        "route_id": "R1",
        "language": "en",
        "target_identity": "machine",
        "human_parallel_version": False,
        "translation_used": False,
        "is_construct_adaptation": False,
        "measurement_source": "pa_wu_p0",
    }
    for key, want in expected.items():
        if route.get(key) != want:
            raise PreflightError(
                f"route_freeze.{key} must be {want!r}, got {route.get(key)!r}"
            )
    for forbidden_key in ("real_model_execution_authorized", "p1_execution_status"):
        if forbidden_key in route:
            raise PreflightError(
                f"route_freeze must not carry {forbidden_key!r}; authorization state "
                "belongs only in authorization_gate.yaml"
            )
    forbidden = route.get("forbidden", {})
    if isinstance(forbidden, dict):
        for key, val in forbidden.items():
            if val is not True:
                raise PreflightError(f"route_freeze.forbidden.{key} must remain true")


# --------------------------------------------------------------------------
# R1 mock source verification (actual file + real validator)
# --------------------------------------------------------------------------


def load_r1_mock_manifest() -> dict[str, Any]:
    path = _r1_mock_dir() / "mock_manifest.yaml"
    if not path.is_file():
        raise PreflightError(f"R1 mock manifest not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PreflightError("R1 mock manifest is not a mapping")
    return data


def verify_r1_mock_source(route: dict[str, Any]) -> str:
    manifest = load_r1_mock_manifest()
    ref_hash = str(manifest.get("deterministic_run_hash_reference", ""))
    route_hash = str(route.get("mock_package_hash", ""))
    if ref_hash != route_hash:
        raise PreflightError(
            f"R1 mock hash mismatch: manifest {ref_hash!r} != route_freeze {route_hash!r}"
        )
    reuses = manifest.get("reuses", {})
    if not isinstance(reuses, dict) or not _nonempty(reuses.get("p0_scoring_version")):
        raise PreflightError("R1 mock manifest missing reuses.p0_scoring_version")
    if not manifest.get("forbidden_score_ids"):
        raise PreflightError("R1 mock manifest missing forbidden_score_ids")
    for fname in manifest.get("files", []):
        if not (_r1_mock_dir() / str(fname)).is_file():
            raise PreflightError(f"R1 mock file listed in manifest is missing: {fname}")
    return ref_hash


def run_r1_mock_validator() -> str:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pa_wu_r1_mock_validate_from_preflight",
        _r1_mock_dir() / "validate_mock_package.py",
    )
    if spec is None or spec.loader is None:
        raise PreflightError("cannot load R1 mock validate_mock_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validate_package()
    return str(report["deterministic_run_hash"])


# --------------------------------------------------------------------------
# Per-gate real satisfaction
# --------------------------------------------------------------------------


def check_model_frozen_fields_set(model: dict[str, Any]) -> None:
    """The declared frozen_fields_required must exactly equal the expected set."""
    declared = model.get("frozen_fields_required", [])
    if not isinstance(declared, list) or set(declared) != set(MODEL_FROZEN_FIELDS):
        raise PreflightError(
            "model_selection.frozen_fields_required must equal the expected set"
        )


def _model_frozen(model: dict[str, Any]) -> bool:
    if str(model.get("selection_status")) != "frozen":
        return False
    declared = model.get("frozen_fields_required", [])
    if not isinstance(declared, list) or set(declared) != set(MODEL_FROZEN_FIELDS):
        return False
    selected = model.get("selected_model")
    if not _nonempty(selected):
        return False
    dec = model.get("decision", {})
    if not isinstance(dec, dict):
        return False
    if str(selected) != str(dec.get("model_id")):
        return False
    for f in _MODEL_STRING_FIELDS:
        if not _nonempty(dec.get(f)):
            return False
    if not _positive_int(dec.get("context_window_requirement")):
        return False
    for f in _MODEL_BOOL_FIELDS:
        if not isinstance(dec.get(f), bool):
            return False
    for f in _MODEL_TRUE_FIELDS:
        if dec.get(f) is not True:
            return False
    if not _nonempty(dec.get("decided_by")):
        return False
    # decided_at must parse as a real ISO date/datetime.
    if not (_is_date(dec.get("decided_at"))):
        return False
    refs = dec.get("source_references")
    if not isinstance(refs, list) or not refs:
        return False
    # every source reference element must be non-empty and non-placeholder.
    if not all(_nonempty(r) for r in refs):
        return False
    return True


def _segment_ok(name: str, seg: dict[str, Any]) -> bool:
    if not isinstance(seg, dict) or seg.get("frozen") is not True:
        return False
    if not _nonempty(seg.get("owner")):
        return False
    if seg.get("change_requires_new_run_version") is not True:
        return False
    sha = str(seg.get("sha256", ""))
    if not _SHA256_RE.match(sha):
        return False

    if name == "item_block":
        # item_block binds the COMPLETE, fixed-order P0 source bundle. No inline
        # content, no single template_reference substitution allowed.
        if _nonempty(seg.get("content")) or _nonempty(seg.get("template_reference")):
            return False
        bundle = seg.get("source_bundle")
        if not isinstance(bundle, list) or list(bundle) != list(ITEM_BLOCK_P0_BUNDLE):
            return False
        try:
            actual = source_bundle_hash([str(x) for x in bundle])
        except PreflightError:
            return False
        return actual == sha

    # Non-item segments: exactly one of content / template_reference.
    content = seg.get("content")
    tref = seg.get("template_reference")
    has_content = _nonempty(content)
    has_tref = _nonempty(tref)
    if has_content == has_tref:
        return False
    try:
        if has_content:
            actual = hashlib.sha256(str(content).encode("utf-8")).hexdigest()
        else:
            actual = template_content_hash(str(tref))
    except PreflightError:
        return False
    return actual == sha


def _prompt_frozen(prompt: dict[str, Any]) -> bool:
    segments = prompt.get("segments", {})
    if not isinstance(segments, dict) or set(segments) != set(PROMPT_SEGMENTS):
        return False
    for name, seg in segments.items():
        if not _segment_ok(name, seg):
            return False
    c = prompt.get("constraints", {})
    return (
        c.get("request_hidden_reasoning") is False
        and c.get("request_structured_final_scores_only") is True
        and str(c.get("item_wording_source")) == "pa_wu_p0"
        and c.get("scenario_model_rewrite_allowed") is False
        and str(c.get("identity_presented")) == "machine"
        and c.get("change_requires_new_run_version") is True
        and c.get("block_on_prompt_hash_mismatch") is True
    )


def _sampling_frozen(sampling: dict[str, Any]) -> bool:
    if sampling.get("frozen") is not True:
        return False
    if sampling.get("seed_is_determinism_guarantee") is not False:
        return False
    if sampling.get("linked_to_budget_contract") is not True:
        return False
    temp = sampling.get("temperature")
    if not _finite_number(temp) or temp < 0:
        return False
    top_p = sampling.get("top_p")
    if not _finite_number(top_p) or not (0 < top_p <= 1):
        return False
    if not _positive_int(sampling.get("max_output_tokens")):
        return False
    seed_supported = sampling.get("seed_supported")
    if not isinstance(seed_supported, bool):
        return False
    seed = sampling.get("seed")
    if seed_supported:
        if not isinstance(seed, int) or isinstance(seed, bool):
            return False
    else:
        if seed is not None:
            return False
    if not _positive_int(sampling.get("repeats_per_case")):
        return False
    if not _positive_int(sampling.get("planned_case_count")):
        return False
    if not _positive_int(sampling.get("total_planned_requests")):
        return False
    if sampling["total_planned_requests"] != (
        sampling["planned_case_count"] * sampling["repeats_per_case"]
    ):
        return False
    if not _positive_int(sampling.get("concurrency")):
        return False
    if sampling["concurrency"] > sampling["total_planned_requests"]:
        return False
    if not _positive_number(sampling.get("request_timeout_seconds")):
        return False
    for policy in ("scenario_order_policy", "item_order_policy", "repeat_index_policy"):
        if not _nonempty(sampling.get(policy)):
            return False
    return True


def _budget_approved(budget: dict[str, Any], sampling: dict[str, Any]) -> bool:
    if budget.get("budget_approved") is not True:
        return False
    if not _nonempty(budget.get("currency")):
        return False
    mtb = budget.get("maximum_total_budget")
    if not _positive_number(mtb):
        return False
    wbt = budget.get("warning_budget_threshold")
    if not _positive_number(wbt) or wbt > mtb:
        return False
    mcpc = budget.get("maximum_cost_per_case")
    if not _positive_number(mcpc) or mcpc > mtb:
        return False
    if not _positive_int(budget.get("estimated_input_tokens")):
        return False
    if not _positive_int(budget.get("estimated_output_tokens")):
        return False
    if not _positive_int(budget.get("total_planned_requests")):
        return False
    if budget["total_planned_requests"] != sampling.get("total_planned_requests"):
        return False
    # maximum_cost_per_case * planned_case_count must not exceed hard limit.
    planned = sampling.get("planned_case_count")
    if _positive_int(planned) and mcpc * planned > mtb:
        return False
    if not _positive_int(budget.get("concurrency_limit")):
        return False
    if sampling.get("concurrency", 0) > budget["concurrency_limit"]:
        return False
    if not _positive_number(budget.get("requests_per_minute_limit")):
        return False
    if not _positive_number(budget.get("tokens_per_minute_limit")):
        return False
    if not _nonempty(budget.get("budget_owner")):
        return False
    if not _is_date(budget.get("approval_timestamp")):
        return False
    pricing = budget.get("pricing", {})
    if not isinstance(pricing, dict) or pricing.get("verified") is not True:
        return False
    if not _nonempty(pricing.get("source")):
        return False
    if not _is_date(pricing.get("snapshot_date")):
        return False
    return True


def _retry_frozen(retry: dict[str, Any]) -> bool:
    if retry.get("frozen") is not True:
        return False
    retryable = set(retry.get("retryable_codes", []))
    non_auto = set(retry.get("non_auto_retryable_codes", []))
    if retryable & non_auto:
        return False
    if non_auto != set(retry.get("manual_review_required_codes", [])):
        return False
    policy = retry.get("policy", {})
    if not isinstance(policy, dict) or not _positive_int(policy.get("max_attempts")):
        return False
    for f in (
        "exponential_backoff",
        "jitter",
        "retry_after_respected",
        "resume_from_checkpoint",
        "duplicate_request_detection",
        "partial_run_recovery",
    ):
        if not isinstance(policy.get(f), bool):
            return False
    if not _nonempty(policy.get("idempotency_key_policy")):
        return False
    return _positive_int(policy.get("checkpoint_interval"))


def _logging_frozen(logging_c: dict[str, Any]) -> bool:
    if logging_c.get("frozen") is not True:
        return False
    req = list(logging_c.get("required_log_fields", []))
    if set(req) != set(REQUIRED_LOG_FIELDS):
        return False
    crit = set(logging_c.get("critical_provenance_fields", []))
    if not crit or not crit.issubset(set(req)):
        return False
    rules = logging_c.get("rules", {})
    if not isinstance(rules, dict):
        return False
    for rule in (
        "never_log_api_key",
        "never_log_secret",
        "separate_raw_and_parsed_response",
        "no_silent_overwrite",
        "case_repeat_unique_within_run",
        "block_scoring_if_missing_provenance",
    ):
        if rules.get(rule) is not True:
            return False
    return True


def _privacy_review_completed(logging_c: dict[str, Any]) -> bool:
    pr = logging_c.get("privacy_review", {})
    if not isinstance(pr, dict):
        return False
    return (
        str(pr.get("status")) == "completed"
        and _nonempty(pr.get("reviewed_by"))
        # reviewed_at must be a REAL ISO date/datetime, not merely non-empty.
        and _is_date(pr.get("reviewed_at"))
    )


def _stop_conditions_frozen(stop: dict[str, Any]) -> bool:
    if stop.get("frozen") is not True:
        return False
    immediate = stop.get("immediate_stop", [])
    if not isinstance(immediate, list):
        return False
    conds = [str(e.get("condition")) for e in immediate if isinstance(e, dict)]
    if set(conds) != set(IMMEDIATE_STOP_CONDITIONS) or len(conds) != len(set(conds)):
        return False
    for e in immediate:
        for f in ("condition", "threshold", "action", "resume_requires", "owner"):
            if not _nonempty(e.get(f)):
                return False
        if str(e.get("action")) not in _LEGAL_STOP_ACTIONS:
            return False
    thresh = stop.get("threshold_stop", [])
    if not isinstance(thresh, list):
        return False
    tconds = [str(e.get("condition")) for e in thresh if isinstance(e, dict)]
    if set(tconds) != set(THRESHOLD_STOP_CONDITIONS) or len(tconds) != len(set(tconds)):
        return False
    for e in thresh:
        if str(e.get("threshold_status")) != "resolved":
            return False
        if str(e.get("condition")) in _RATE_STOP_CONDITIONS and not _rate_ok(
            e.get("threshold")
        ):
            return False
        for f in ("action", "resume_requires", "owner"):
            if not _nonempty(e.get(f)):
                return False
        if str(e.get("action")) not in _LEGAL_STOP_ACTIONS:
            return False
    return True


def _env_reviewed(env: dict[str, Any]) -> bool:
    """environment_review_completed is only true once THIS preflight branch's
    own Linux CI has succeeded and been recorded (not merely the R1 baseline).
    The honest recording of the Windows exceptions is also required."""
    baseline = env.get("r1_baseline_ci", env.get("linux_ci", {}))
    branch = env.get("preflight_branch_ci", {})
    win = env.get("windows_local", {})
    qual = env.get("windows_failure_qualification", {})
    honest_record = (
        baseline.get("status") == "success"
        and win.get("full_pytest_status") == "environment_specific_failures"
        and qual.get("in_pr_10_diff") is False
        and qual.get("is_r1_mock_regression") is False
        and qual.get("is_preflight_code_regression") is False
        and qual.get("is_fixed") is False
    )
    branch_ci_ok = (
        str(branch.get("status")) == "success"
        and _nonempty(branch.get("run_number"))
    )
    return bool(honest_record and branch_ci_ok)


def _cross_contract_consistent(contracts: dict[str, dict[str, Any]]) -> bool:
    """Cross-contract coherence between the model decision, sampling and budget.

    Only enforced when model / sampling / budget are individually satisfied; a
    mismatch flips model_frozen to false (the decision is not truly frozen if it
    contradicts the sampling/budget it will run under)."""
    model = contracts["model_selection_decision.yaml"]
    sampling = contracts["sampling_and_repeat_contract.yaml"]
    budget = contracts["budget_and_rate_limit_contract.yaml"]
    dec = model.get("decision", {})
    if not isinstance(dec, dict):
        return False
    # deterministic_seed_support must agree with sampling.seed_supported
    if bool(dec.get("deterministic_seed_support")) != bool(sampling.get("seed_supported")):
        return False
    # structured output is required for structured-final-scores-only
    if dec.get("structured_output_support") is not True:
        return False
    # temperature_support must agree with an actual temperature setting
    temp = sampling.get("temperature")
    if dec.get("temperature_support") is True:
        if not _finite_number(temp):
            return False
    else:
        # no temperature support -> temperature must be absent/None
        if temp is not None:
            return False
    # model pricing source/date must match the budget pricing record
    pricing = budget.get("pricing", {})
    if not isinstance(pricing, dict):
        return False
    if str(dec.get("pricing_source_recorded")) != str(pricing.get("source")):
        return False
    if str(dec.get("pricing_snapshot_date")) != str(pricing.get("snapshot_date")):
        return False
    return True


def compute_gate_status(
    contracts: dict[str, dict[str, Any]],
    mock_hash_verified: bool,
    source_hashes_verified: bool,
) -> dict[str, bool]:
    route = contracts["route_freeze.yaml"]
    model_ok = _model_frozen(contracts["model_selection_decision.yaml"])
    # Cross-contract coherence only matters once model itself is frozen AND the
    # counterpart contracts are frozen/approved; otherwise leave model gated on
    # its own completeness (avoids masking the real blocking reason).
    if model_ok and _sampling_frozen(
        contracts["sampling_and_repeat_contract.yaml"]
    ) and _budget_approved(
        contracts["budget_and_rate_limit_contract.yaml"],
        contracts["sampling_and_repeat_contract.yaml"],
    ):
        model_ok = _cross_contract_consistent(contracts)
    return {
        "route_frozen": bool(
            route.get("route_id") == "R1"
            and str(route.get("mock_package_hash")) == R1_MOCK_HASH
        ),
        "model_frozen": model_ok,
        "prompt_frozen": _prompt_frozen(contracts["prompt_freeze_contract.yaml"]),
        "sampling_frozen": _sampling_frozen(
            contracts["sampling_and_repeat_contract.yaml"]
        ),
        "budget_approved": _budget_approved(
            contracts["budget_and_rate_limit_contract.yaml"],
            contracts["sampling_and_repeat_contract.yaml"],
        ),
        "retry_policy_frozen": _retry_frozen(
            contracts["retry_and_recovery_contract.yaml"]
        ),
        "logging_contract_frozen": _logging_frozen(
            contracts["provenance_and_logging_contract.yaml"]
        ),
        "stop_conditions_frozen": _stop_conditions_frozen(
            contracts["stop_conditions.yaml"]
        ),
        "privacy_review_completed": _privacy_review_completed(
            contracts["provenance_and_logging_contract.yaml"]
        ),
        "environment_review_completed": _env_reviewed(
            contracts["environment_acceptance.yaml"]
        ),
        "mock_package_validated": bool(mock_hash_verified),
        "source_hashes_verified": bool(source_hashes_verified),
    }


# --------------------------------------------------------------------------
# Authorization state machine (single source of truth)
# --------------------------------------------------------------------------

VALID_AUTH_STATUSES = frozenset({"blocked", "authorized"})


def check_required_gates_exact(auth: dict[str, Any]) -> None:
    gates = auth.get("required_gates", {})
    if not isinstance(gates, dict):
        raise PreflightError("authorization_gate.required_gates must be a mapping")
    if set(gates) != set(REQUIRED_GATES):
        missing = sorted(set(REQUIRED_GATES) - set(gates))
        extra = sorted(set(gates) - set(REQUIRED_GATES))
        raise PreflightError(
            f"authorization_gate.required_gates must equal REQUIRED_GATES "
            f"(missing={missing}, extra={extra})"
        )


def check_declared_matches_computed(
    auth: dict[str, Any], gate_status: dict[str, bool]
) -> None:
    declared = auth.get("required_gates", {})
    for gate in REQUIRED_GATES:
        if bool(declared.get(gate)) != bool(gate_status[gate]):
            raise PreflightError(
                f"authorization_gate.required_gates.{gate}={declared.get(gate)!r} "
                f"does not match computed {gate_status[gate]!r}"
            )


def check_authorization_state_machine(
    auth: dict[str, Any], gate_status: dict[str, bool]
) -> str:
    status = str(auth.get("authorization_status"))
    if status not in VALID_AUTH_STATUSES:
        raise PreflightError(f"illegal authorization_status: {status!r}")
    flag = auth.get("real_model_execution_authorized")
    if not isinstance(flag, bool):
        raise PreflightError("real_model_execution_authorized must be a boolean")
    all_gates_ok = all(gate_status.values())
    if status == "authorized":
        if flag is not True:
            raise PreflightError("authorized status requires flag=true")
        if not all_gates_ok:
            failing = sorted(g for g, ok in gate_status.items() if not ok)
            raise PreflightError(f"authorized but gates still failing: {failing}")
        if not _nonempty(auth.get("authorized_by")):
            raise PreflightError("authorized status requires non-empty authorized_by")
        # authorized_at must be a REAL ISO date/datetime, not merely non-empty.
        if not _is_date(auth.get("authorized_at")):
            raise PreflightError(
                "authorized status requires ISO-parseable authorized_at"
            )
        return "authorized"
    if flag is True:
        raise PreflightError("blocked status must not carry flag=true")
    return "blocked"


# --------------------------------------------------------------------------
# AST-based security scan (formal production path; used by tests too)
# --------------------------------------------------------------------------

_SECRET_LITERAL = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)
_SECRET_ASSIGNMENT = re.compile(
    r"(api_key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", re.IGNORECASE
)
_SECRET_POLICY_ALLOWED = re.compile(
    r"(never_log_api_key|never_log_secret|secret_detected|no[_-]?api[_-]?key|"
    r"api_key|secret)\s*[:=]\s*(true|false|null|any|\[\])?\s*$",
    re.IGNORECASE,
)


def _ast_string_constants(tree: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def scan_python_source(path: Path) -> None:
    """Formal AST-based scan of a Python file. Raises PreflightError on any:

    - Import / ImportFrom of a banned module;
    - importlib.import_module(...) / __import__(...) of a banned module;
    - attribute calls into requests/httpx/urllib/socket;
    - subprocess invocation of a network CLI (curl/wget/powershell/...);
    - R2/R3 forbidden path fragment used in an Import/open/Path/import_module.

    Detection does NOT rely on comment markers and cannot be bypassed by adding
    a marker comment. String CONSTANTS that merely equal a module name are only
    flagged when they are the argument of an import/open/subprocess call.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))

    def _call_name(node: ast.Call) -> str:
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            parts = []
            cur: Any = f
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        return ""

    def _flat_str_args(node: ast.Call) -> list[str]:
        """All string constant args, INCLUDING those nested in list/tuple args
        (so subprocess.run(['curl', url]) is inspected element-wise)."""
        out: list[str] = []
        containers = list(node.args) + [k.value for k in node.keywords]
        for a in containers:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append(a.value)
            elif isinstance(a, (ast.List, ast.Tuple)):
                for elt in a.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        out.append(elt.value)
        return out

    # Track dynamic-import entry points regardless of alias:
    #   import importlib as X            -> X.import_module
    #   from importlib import import_module as Y  -> Y(...)
    importlib_aliases: set[str] = set()          # names bound to the importlib module
    import_module_aliases: set[str] = {"__import__"}  # names bound to import_module fn

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in BANNED_MODULES:
                    raise PreflightError(f"banned import: {alias.name} in {path.name}")
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or "importlib")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in BANNED_MODULES:
                raise PreflightError(f"banned import-from: {node.module} in {path.name}")
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_aliases.add(alias.asname or "import_module")

    dynamic_import_names = set(import_module_aliases)
    for a in importlib_aliases:
        dynamic_import_names.add(f"{a}.import_module")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        args = _flat_str_args(node)
        if name in dynamic_import_names or name.endswith(".import_module"):
            for a in args:
                if a.split(".")[0] in BANNED_MODULES:
                    raise PreflightError(f"banned dynamic import {a!r} in {path.name}")
                if any(frag in a for frag in FORBIDDEN_PATH_FRAGMENTS):
                    raise PreflightError(f"forbidden path import {a!r} in {path.name}")
        top = name.split(".")[0]
        if top in BANNED_MODULES:
            raise PreflightError(f"banned network call {name!r} in {path.name}")
        if name.startswith("subprocess.") or name in ("run", "Popen", "call", "check_output"):
            for a in args:
                low = a.lower().strip()
                first_token = low.split()[0] if low.split() else low
                if any(low == c or first_token == c or c in low.split() for c in (_c.lower() for _c in _NETWORK_CLI)):
                    raise PreflightError(f"network CLI via subprocess in {path.name}: {a!r}")
        if name in ("open", "Path") or name.endswith(".open"):
            for a in args:
                if any(frag in a for frag in FORBIDDEN_PATH_FRAGMENTS):
                    raise PreflightError(
                        f"forbidden R2/R3 path access {a!r} in {path.name}"
                    )


def scan_text_secrets(path: Path) -> None:
    """Secret scan that CANNOT be bypassed by appending a marker comment."""
    text = path.read_text(encoding="utf-8")
    if _SECRET_LITERAL.search(text):
        raise PreflightError(f"secret literal detected in {path.name}")
    for line in text.splitlines():
        # strip trailing comment before checking policy allow-list so that an
        # appended comment cannot turn a real assignment into an "allowed" one.
        code = line.split("#", 1)[0].strip()
        if _SECRET_ASSIGNMENT.search(code) and not _SECRET_POLICY_ALLOWED.search(code):
            raise PreflightError(f"secret assignment in {path.name}: {code!r}")


def check_no_secrets_no_clients_no_network() -> None:
    for path in PACKAGE_DIR.rglob("*"):
        suffix = path.suffix.lower()
        if suffix == ".py":
            scan_python_source(path)
            scan_text_secrets(path)
        elif suffix in (".yaml", ".yml", ".md"):
            scan_text_secrets(path)
            _scan_yaml_forbidden_refs(path)


def _scan_yaml_forbidden_refs(path: Path) -> None:
    declaration = re.compile(
        r"^\s*(r2_[a-z0-9_]+|r3_[a-z0-9_]+|human_identity_version|chinese_formal_scale|"
        r"du_effect_conclusion|measurement_invariance_conclusion)\s*:\s*(true|false|null)\s*$",
        re.IGNORECASE,
    )
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if declaration.match(raw_line):
            continue
        low = raw_line.lower()
        for frag in FORBIDDEN_PATH_FRAGMENTS:
            if frag in low:
                raise PreflightError(
                    f"forbidden R2/R3 reference {frag!r} in {path.name}: {raw_line.strip()!r}"
                )


def check_validator_self_ast() -> None:
    """AST-scan the validator IN THE CURRENT PACKAGE_DIR (so it matches the
    package being validated); banned modules as real nodes are rejected."""
    validator_path = PACKAGE_DIR / "validate_preflight.py"
    if not validator_path.is_file():
        raise PreflightError(
            f"validate_preflight.py not found in package dir: {validator_path}"
        )
    scan_python_source(validator_path)


# --------------------------------------------------------------------------
# Manifest + hashes
# --------------------------------------------------------------------------


_MANAGED_SUFFIXES = (".yaml", ".yml", ".py", ".md", ".txt", ".json")


def _managed_top_level_assets() -> set[str]:
    return {
        p.name
        for p in PACKAGE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in _MANAGED_SUFFIXES
    }


def _managed_nested_assets() -> set[str]:
    """Recursively collect managed assets BELOW the top level (e.g. templates/*),
    as POSIX relative paths from PACKAGE_DIR."""
    out: set[str] = set()
    for p in PACKAGE_DIR.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in _MANAGED_SUFFIXES:
            continue
        rel = p.relative_to(PACKAGE_DIR).as_posix()
        if "/" in rel:  # nested only
            out.add(rel)
    return out


def check_manifest() -> dict[str, Any]:
    m = load_manifest()
    if set(m.get("files", [])) != set(REQUIRED_FILES):
        raise PreflightError("manifest files list does not match required files")
    # Every physical top-level managed asset must be declared in files.
    stray = _managed_top_level_assets() - set(m.get("files", []))
    if stray:
        raise PreflightError(f"undeclared package assets present: {sorted(stray)}")
    # Nested assets (e.g. templates/*) must be declared in template_files.
    declared_nested = set(m.get("template_files", []))
    actual_nested = _managed_nested_assets()
    if actual_nested != declared_nested:
        missing = sorted(actual_nested - declared_nested)
        extra = sorted(declared_nested - actual_nested)
        raise PreflightError(
            f"manifest template_files mismatch (undeclared={missing}, stale={extra})"
        )
    if set(m.get("contract_files", [])) != set(CONTRACT_FILES):
        raise PreflightError("manifest contract_files does not match validator load list")
    if m.get("route_id") != "R1":
        raise PreflightError("manifest route_id must be R1")
    if m.get("package_status") != "preflight_only":
        raise PreflightError("manifest package_status must be preflight_only")
    if "p1_execution_status" in m:
        raise PreflightError("manifest must not persist p1_execution_status")
    reuses = m.get("reuses", {})
    if str(reuses.get("r1_mock_package_hash")) != R1_MOCK_HASH:
        raise PreflightError("manifest reuses.r1_mock_package_hash mismatch")
    if reuses.get("measurement_source") != "pa_wu_p0":
        raise PreflightError("manifest reuses.measurement_source must be pa_wu_p0")
    if "pa_wu_r1_mock" not in str(reuses.get("r1_mock_package", "")):
        raise PreflightError("manifest reuses.r1_mock_package path invalid")
    invariants = m.get("invariants", {})
    if not isinstance(invariants, dict) or not all(v is True for v in invariants.values()):
        raise PreflightError("manifest invariants must all be true")
    return m


def compute_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    payload = {name: contracts[name] for name in sorted(contracts)}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def compute_package_hash(
    contracts: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> str:
    """Package hash covering manifest + all contracts + the validator source
    IN THE CURRENT PACKAGE_DIR + every managed nested template asset. Any change
    to the (packaged) validator or a template therefore changes the hash."""
    validator_path = PACKAGE_DIR / "validate_preflight.py"
    if not validator_path.is_file():
        raise PreflightError(
            f"validate_preflight.py not found in package dir: {validator_path}"
        )
    validator_src = validator_path.read_text(encoding="utf-8")
    templates: dict[str, str] = {}
    for rel in sorted(_managed_nested_assets()):
        templates[rel] = (PACKAGE_DIR / rel).read_text(encoding="utf-8")
    payload = {
        "manifest": manifest,
        "contracts": {name: contracts[name] for name in sorted(contracts)},
        "validator_source": validator_src,
        "templates": templates,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Full report
# --------------------------------------------------------------------------


def build_preflight_report() -> dict[str, Any]:
    check_required_files()
    manifest = check_manifest()

    contracts = {name: _load_yaml(name) for name in CONTRACT_FILES}
    route = contracts["route_freeze.yaml"]
    auth = contracts["authorization_gate.yaml"]

    check_route_boundary(route)
    check_validator_self_ast()
    check_no_secrets_no_clients_no_network()
    check_required_gates_exact(auth)
    check_model_frozen_fields_set(contracts["model_selection_decision.yaml"])

    verified_hash = verify_r1_mock_source(route)
    validator_hash = run_r1_mock_validator()
    mock_ok = validator_hash == R1_MOCK_HASH
    source_ok = verified_hash == R1_MOCK_HASH and mock_ok

    gate_status = compute_gate_status(contracts, mock_ok, source_ok)
    check_declared_matches_computed(auth, gate_status)
    resolved_status = check_authorization_state_machine(auth, gate_status)

    resolved_gates = sorted(g for g, ok in gate_status.items() if ok)
    blocking_gates = sorted(g for g, ok in gate_status.items() if not ok)

    unresolved: list[str] = []
    label = {
        "model_frozen": "model_selection_unresolved",
        "budget_approved": "budget_not_approved",
        "prompt_frozen": "prompt_not_frozen",
        "sampling_frozen": "sampling_not_frozen",
        "stop_conditions_frozen": "stop_thresholds_unresolved",
        "privacy_review_completed": "privacy_review_pending",
        "retry_policy_frozen": "retry_policy_not_frozen",
        "logging_contract_frozen": "logging_contract_not_frozen",
    }
    for gate, name in label.items():
        if not gate_status[gate]:
            unresolved.append(name)

    preflight_status = "authorized" if resolved_status == "authorized" else "blocked"
    return {
        "preflight_status": preflight_status,
        "authorization_status": resolved_status,
        "blocking_gates": blocking_gates,
        "resolved_gates": resolved_gates,
        "unresolved_decisions": sorted(unresolved),
        "contract_hash": compute_contract_hash(contracts),
        "package_hash": compute_package_hash(contracts, manifest),
        "real_model_execution_authorized": bool(
            auth.get("real_model_execution_authorized")
        ),
        # Derived only here; never persisted in a contract/manifest.
        "p1_execution_status": "authorized"
        if preflight_status == "authorized"
        else "blocked",
        "route_id": route.get("route_id"),
        "mock_package_hash": route.get("mock_package_hash"),
        "r1_mock_validator_hash": validator_hash,
    }


def main() -> None:  # pragma: no cover
    print(json.dumps(build_preflight_report(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
