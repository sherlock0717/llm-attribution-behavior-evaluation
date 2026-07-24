"""Static, offline validator for the PA-Wu R1 P1 preflight gate package.

STRICT boundaries:
- NO network I/O of any kind.
- NEVER reads an API key from the environment.
- NEVER imports a real-model SDK (openai / anthropic / httpx / requests / ...).
- NEVER executes a model and NEVER produces model output.
- NEVER rewrites any contract file (read-only).
- NEVER auto-enables authorization.

Authorization state has a SINGLE source of truth: ``authorization_gate.yaml``.
``route_freeze.yaml`` only freezes the research route. Every required gate is
recomputed from its own source contract; the declared ``required_gates`` values
in ``authorization_gate.yaml`` must match the recomputed ``gate_status`` exactly.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
# PACKAGE_DIR = <repo>/tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight
# Its sibling R1 mock package lives next to it under measurement_candidates.
MEASUREMENT_CANDIDATES_DIR = PACKAGE_DIR.parent
R1_MOCK_DIR = MEASUREMENT_CANDIDATES_DIR / "pa_wu_r1_mock"

R1_MOCK_HASH = "7c83def4c93ad26f"

# Placeholder values that must NOT satisfy any "field present" check.
_PLACEHOLDERS = frozenset({"", "x", "xx", "placeholder", "todo", "tbd", "none", "null"})

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_LIKE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

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


class PreflightError(RuntimeError):
    """Raised when the preflight package is structurally inconsistent."""


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def _load_yaml(name: str) -> dict[str, Any]:
    with (PACKAGE_DIR / name).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PreflightError(f"{name}: expected a mapping at top level")
    return data


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


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


# --------------------------------------------------------------------------
# Structural checks (raise on violation)
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
    # Authorization state must NOT live in route_freeze (single source of truth).
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
# R1 mock source verification (actual file + real validator, no hardcode-only)
# --------------------------------------------------------------------------


def load_r1_mock_manifest() -> dict[str, Any]:
    path = R1_MOCK_DIR / "mock_manifest.yaml"
    if not path.is_file():
        raise PreflightError(f"R1 mock manifest not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PreflightError("R1 mock manifest is not a mapping")
    return data


def verify_r1_mock_source(route: dict[str, Any]) -> str:
    """Read the R1 mock manifest and cross-check hash + key source fields.

    Returns the R1 deterministic hash on success. Raises on any mismatch or
    missing key source field. Also asserts required R1 files exist.
    """
    manifest = load_r1_mock_manifest()
    ref_hash = str(manifest.get("deterministic_run_hash_reference", ""))
    route_hash = str(route.get("mock_package_hash", ""))
    if ref_hash != route_hash:
        raise PreflightError(
            f"R1 mock hash mismatch: manifest {ref_hash!r} != route_freeze {route_hash!r}"
        )
    # Key source fields must be present in the R1 manifest.
    reuses = manifest.get("reuses", {})
    if not isinstance(reuses, dict) or not _nonempty(reuses.get("p0_scoring_version")):
        raise PreflightError("R1 mock manifest missing reuses.p0_scoring_version")
    forbidden_ids = manifest.get("forbidden_score_ids", [])
    if not isinstance(forbidden_ids, list) or not forbidden_ids:
        raise PreflightError("R1 mock manifest missing forbidden_score_ids")
    # Required R1 mock files must exist on disk.
    for fname in manifest.get("files", []):
        if not (R1_MOCK_DIR / str(fname)).is_file():
            raise PreflightError(f"R1 mock file listed in manifest is missing: {fname}")
    return ref_hash


def run_r1_mock_validator() -> str:
    """Reuse the R1 mock package's own static validator; return its hash.

    Pure local static validation, no network, no model execution.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "pa_wu_r1_mock_validate_from_preflight",
        R1_MOCK_DIR / "validate_mock_package.py",
    )
    if spec is None or spec.loader is None:
        raise PreflightError("cannot load R1 mock validate_mock_package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validate_package()
    return str(report["deterministic_run_hash"])


# --------------------------------------------------------------------------
# Per-gate real satisfaction checks
# --------------------------------------------------------------------------


def _model_frozen(model: dict[str, Any]) -> bool:
    if str(model.get("selection_status")) != "frozen":
        return False
    selected = model.get("selected_model")
    if not _nonempty(selected):
        return False
    dec = model.get("decision", {})
    if not isinstance(dec, dict):
        return False
    if str(selected) != str(dec.get("model_id")):
        return False
    required = (
        "provider",
        "model_id",
        "exact_model_version_or_snapshot",
        "endpoint_type",
        "access_method",
        "pricing_snapshot_date",
        "pricing_source_recorded",
        "decided_by",
        "decided_at",
    )
    for field_name in required:
        if not _nonempty(dec.get(field_name)):
            return False
    for bool_field in (
        "provider_retention_policy_reviewed",
        "regional_availability_reviewed",
        "terms_of_use_reviewed",
    ):
        if dec.get(bool_field) is not True:
            return False
    if not isinstance(dec.get("source_references"), list) or not dec["source_references"]:
        return False
    return True


def _prompt_frozen(prompt: dict[str, Any]) -> bool:
    segments = prompt.get("segments", {})
    if not isinstance(segments, dict):
        return False
    if set(segments) != set(PROMPT_SEGMENTS):
        return False
    for seg in segments.values():
        if not isinstance(seg, dict):
            return False
        if seg.get("frozen") is not True:
            return False
        content = seg.get("content")
        tref = seg.get("template_reference")
        has_content = _nonempty(content)
        has_tref = _nonempty(tref)
        # exactly one source of truth (no conflicting dual source)
        if has_content == has_tref:
            return False
        sha = str(seg.get("sha256", ""))
        if not _SHA256_RE.match(sha):
            return False
        # sha must match the actual content when content is inline.
        if has_content:
            actual = hashlib.sha256(str(content).encode("utf-8")).hexdigest()
            if actual != sha:
                return False
        if not _nonempty(seg.get("owner")):
            return False
        if seg.get("change_requires_new_run_version") is not True:
            return False
    # Hard constraint boundaries must be intact.
    c = prompt.get("constraints", {})
    if not (
        c.get("request_hidden_reasoning") is False
        and c.get("request_structured_final_scores_only") is True
        and str(c.get("item_wording_source")) == "pa_wu_p0"
        and c.get("scenario_model_rewrite_allowed") is False
        and str(c.get("identity_presented")) == "machine"
        and c.get("change_requires_new_run_version") is True
        and c.get("block_on_prompt_hash_mismatch") is True
    ):
        return False
    return True


def _sampling_frozen(sampling: dict[str, Any]) -> bool:
    if sampling.get("frozen") is not True:
        return False
    # seed can never be declared a determinism guarantee.
    if sampling.get("seed_is_determinism_guarantee") is not False:
        return False
    if not isinstance(sampling.get("temperature"), (int, float)) or isinstance(
        sampling.get("temperature"), bool
    ):
        return False
    if not isinstance(sampling.get("top_p"), (int, float)) or isinstance(
        sampling.get("top_p"), bool
    ):
        return False
    if not _positive_int(sampling.get("max_output_tokens")):
        return False
    if not isinstance(sampling.get("seed_supported"), bool):
        return False
    if sampling.get("seed_supported") is False and sampling.get("seed") is not None:
        # allowed to be null; but if declared unsupported, seed must be null
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
    if not _positive_number(budget.get("maximum_total_budget")):
        return False
    wbt = budget.get("warning_budget_threshold")
    if not _positive_number(wbt) or wbt > budget["maximum_total_budget"]:
        return False
    if not _positive_number(budget.get("maximum_cost_per_case")):
        return False
    if not _positive_int(budget.get("estimated_input_tokens")):
        return False
    if not _positive_int(budget.get("estimated_output_tokens")):
        return False
    if not _positive_int(budget.get("total_planned_requests")):
        return False
    # must agree with sampling
    if budget["total_planned_requests"] != sampling.get("total_planned_requests"):
        return False
    if not _positive_int(budget.get("concurrency_limit")):
        return False
    if not _positive_number(budget.get("requests_per_minute_limit")):
        return False
    if not _positive_number(budget.get("tokens_per_minute_limit")):
        return False
    if not _nonempty(budget.get("budget_owner")):
        return False
    if not _nonempty(budget.get("approval_timestamp")):
        return False
    pricing = budget.get("pricing", {})
    if not isinstance(pricing, dict):
        return False
    if pricing.get("verified") is not True:
        return False
    if not _nonempty(pricing.get("source")):
        return False
    if not _nonempty(pricing.get("snapshot_date")):
        return False
    return True


def _no_retry_overlap(retry: dict[str, Any]) -> bool:
    retryable = set(retry.get("retryable_codes", []))
    non_auto = set(retry.get("non_auto_retryable_codes", []))
    return not (retryable & non_auto)


def _retry_frozen(retry: dict[str, Any]) -> bool:
    if retry.get("frozen") is not True:
        return False
    if not _no_retry_overlap(retry):
        return False
    non_auto = set(retry.get("non_auto_retryable_codes", []))
    manual = set(retry.get("manual_review_required_codes", []))
    if non_auto != manual:
        return False
    policy = retry.get("policy", {})
    if not isinstance(policy, dict):
        return False
    if not _positive_int(policy.get("max_attempts")):
        return False
    for bool_field in (
        "exponential_backoff",
        "jitter",
        "retry_after_respected",
        "resume_from_checkpoint",
        "duplicate_request_detection",
        "partial_run_recovery",
    ):
        if not isinstance(policy.get(bool_field), bool):
            return False
    if not _nonempty(policy.get("idempotency_key_policy")):
        return False
    if not _positive_int(policy.get("checkpoint_interval")):
        return False
    return True


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
        and _nonempty(pr.get("reviewed_at"))
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
        for field_name in ("condition", "action", "resume_requires", "owner"):
            if not _nonempty(e.get(field_name)):
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
        if not _positive_number(e.get("threshold")):
            return False
        if not _nonempty(e.get("owner")):
            return False
    return True


def _env_reviewed(env: dict[str, Any]) -> bool:
    ci = env.get("linux_ci", {})
    win = env.get("windows_local", {})
    qual = env.get("windows_failure_qualification", {})
    return (
        ci.get("status") == "success"
        and win.get("full_pytest_status") == "environment_specific_failures"
        and qual.get("in_pr_10_diff") is False
        and qual.get("is_r1_mock_regression") is False
        and qual.get("is_fixed") is False
    )


def compute_gate_status(
    contracts: dict[str, dict[str, Any]],
    mock_hash_verified: bool,
    source_hashes_verified: bool,
) -> dict[str, bool]:
    route = contracts["route_freeze.yaml"]
    model = contracts["model_selection_decision.yaml"]
    prompt = contracts["prompt_freeze_contract.yaml"]
    sampling = contracts["sampling_and_repeat_contract.yaml"]
    budget = contracts["budget_and_rate_limit_contract.yaml"]
    retry = contracts["retry_and_recovery_contract.yaml"]
    logging_c = contracts["provenance_and_logging_contract.yaml"]
    stop = contracts["stop_conditions.yaml"]
    env = contracts["environment_acceptance.yaml"]

    route_frozen = (
        route.get("route_id") == "R1"
        and str(route.get("mock_package_hash")) == R1_MOCK_HASH
    )
    return {
        "route_frozen": bool(route_frozen),
        "model_frozen": _model_frozen(model),
        "prompt_frozen": _prompt_frozen(prompt),
        "sampling_frozen": _sampling_frozen(sampling),
        "budget_approved": _budget_approved(budget, sampling),
        "retry_policy_frozen": _retry_frozen(retry),
        "logging_contract_frozen": _logging_frozen(logging_c),
        "stop_conditions_frozen": _stop_conditions_frozen(stop),
        "privacy_review_completed": _privacy_review_completed(logging_c),
        "environment_review_completed": _env_reviewed(env),
        "mock_package_validated": bool(mock_hash_verified),
        "source_hashes_verified": bool(source_hashes_verified),
    }


# --------------------------------------------------------------------------
# Authorization state machine
# --------------------------------------------------------------------------

VALID_AUTH_STATUSES = frozenset({"blocked", "authorized"})


def check_required_gates_present(auth: dict[str, Any]) -> None:
    gates = auth.get("required_gates", {})
    if not isinstance(gates, dict):
        raise PreflightError("authorization_gate.required_gates must be a mapping")
    missing = [g for g in REQUIRED_GATES if g not in gates]
    if missing:
        raise PreflightError(f"authorization_gate missing required gates: {missing}")


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
    """Validate the authorization state machine; return the resolved status.

    Raises on any illegal combination.
    """
    status = str(auth.get("authorization_status"))
    if status not in VALID_AUTH_STATUSES:
        raise PreflightError(f"illegal authorization_status: {status!r}")
    flag = auth.get("real_model_execution_authorized")
    if not isinstance(flag, bool):
        raise PreflightError("real_model_execution_authorized must be a boolean")
    all_gates_ok = all(gate_status.values())
    authorized_by = auth.get("authorized_by")
    authorized_at = auth.get("authorized_at")

    if status == "authorized":
        if flag is not True:
            raise PreflightError("authorized status requires flag=true")
        if not all_gates_ok:
            failing = sorted(g for g, ok in gate_status.items() if not ok)
            raise PreflightError(f"authorized but gates still failing: {failing}")
        if not _nonempty(authorized_by):
            raise PreflightError("authorized status requires non-empty authorized_by")
        if not _nonempty(authorized_at):
            raise PreflightError("authorized status requires non-empty authorized_at")
        return "authorized"

    # status == "blocked"
    if flag is True:
        raise PreflightError("blocked status must not carry flag=true")
    return "blocked"


# --------------------------------------------------------------------------
# Security scans (AST-based for the validator itself; text for other files)
# --------------------------------------------------------------------------

_BANNED_IMPORT_MODULES = frozenset(
    {"openai", "anthropic", "httpx", "requests", "socket", "urllib"}  # preflight-detection-pattern
)
_BANNED_TEXT_PATTERNS = (
    re.compile(r"\bimport\s+(openai|anthropic|httpx|requests|socket)\b", re.IGNORECASE),  # preflight-detection-pattern
    re.compile(r"\bfrom\s+(openai|anthropic|httpx|urllib)\b", re.IGNORECASE),  # preflight-detection-pattern
    re.compile(r"requests\.(get|post)\s*\(", re.IGNORECASE),  # preflight-detection-pattern
    re.compile(r"urllib\.request", re.IGNORECASE),  # preflight-detection-pattern
    re.compile(r"chat\.completions", re.IGNORECASE),  # preflight-detection-pattern
)
_SECRET_LITERAL = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)  # preflight-detection-pattern
_SECRET_ASSIGNMENT = re.compile(
    r"(api_key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}", re.IGNORECASE  # preflight-detection-pattern
)
_SECRET_POLICY_ALLOWED = re.compile(
    r"(never_log_api_key|never_log_secret|secret_detected|no[_-]?api[_-]?key|"  # preflight-detection-pattern
    r"api_key|secret)\s*[:=]\s*(true|false|null|any|\[\])?\s*$",  # preflight-detection-pattern
    re.IGNORECASE,
)
_FORBIDDEN_REFS = (
    "pa_wu_p1_prep",  # preflight-detection-pattern
    "provisional",  # preflight-detection-pattern
    "zh-cn",  # preflight-detection-pattern
    "zh_cn",  # preflight-detection-pattern
    "adaptation_candidates",  # preflight-detection-pattern
    "ai_human",  # preflight-detection-pattern
    "ai/human",  # preflight-detection-pattern
)
# Lines that legitimately DEFINE the detection patterns (exempt only these lines).
_PATTERN_DEFINITION_MARKER = "# preflight-detection-pattern"


def check_validator_imports_ast() -> None:
    """AST-scan THIS validator's real Import/ImportFrom nodes for banned modules.

    This proves that adding e.g. ``import requests`` to the validator would be
    rejected, without exempting the whole file from scanning.
    """
    import ast

    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in _BANNED_IMPORT_MODULES:
                    raise PreflightError(f"validator imports banned module: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top in _BANNED_IMPORT_MODULES:
                raise PreflightError(f"validator imports banned module: {node.module}")


def _scan_text_for_bans(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pat in _BANNED_TEXT_PATTERNS:
        if pat.search(text):
            raise PreflightError(
                f"banned client/network pattern {pat.pattern!r} in {path.name}"
            )
    if _SECRET_LITERAL.search(text):
        raise PreflightError(f"secret literal detected in {path.name}")
    for line in text.splitlines():
        stripped = line.strip()
        if _SECRET_ASSIGNMENT.search(stripped) and not _SECRET_POLICY_ALLOWED.search(
            stripped
        ):
            raise PreflightError(
                f"secret assignment detected in {path.name}: {stripped!r}"
            )


def check_no_secrets_no_clients_no_network() -> None:
    """Scan all package files. The validator is scanned via AST for imports and
    via text for everything EXCEPT the specific lines that define detection
    patterns (marked with a trailing comment)."""
    check_validator_imports_ast()
    self_path = Path(__file__).resolve()
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".yml", ".md"):
            continue
        if path.resolve() == self_path:
            # scan the validator, but exempt only the pattern-definition lines
            for line in path.read_text(encoding="utf-8").splitlines():
                if _PATTERN_DEFINITION_MARKER in line:
                    continue
                stripped = line.strip()
                if _SECRET_LITERAL.search(stripped):
                    raise PreflightError(f"secret literal in {path.name}: {stripped!r}")
                if _SECRET_ASSIGNMENT.search(stripped) and not _SECRET_POLICY_ALLOWED.search(
                    stripped
                ):
                    raise PreflightError(
                        f"secret assignment in {path.name}: {stripped!r}"
                    )
            continue
        _scan_text_for_bans(path)


def check_no_r2_r3_reads() -> None:
    declaration = re.compile(
        r"^\s*(r2_[a-z0-9_]+|r3_[a-z0-9_]+|human_identity_version|chinese_formal_scale|"
        r"du_effect_conclusion|measurement_invariance_conclusion)\s*:\s*(true|false|null)\s*$",
        re.IGNORECASE,
    )
    self_path = Path(__file__).resolve()
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".yml"):
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if path.resolve() == self_path and _PATTERN_DEFINITION_MARKER in raw_line:
                continue  # exempt only the specific pattern-definition line
            if declaration.match(raw_line):
                continue  # lock-out declaration, not an asset read
            low = raw_line.lower()
            for ref in _FORBIDDEN_REFS:
                if ref in low:
                    raise PreflightError(
                        f"forbidden R2/R3 reference {ref!r} in {path.name}: {raw_line.strip()!r}"
                    )


# --------------------------------------------------------------------------
# Manifest checks
# --------------------------------------------------------------------------


def check_manifest() -> dict[str, Any]:
    m = load_manifest()
    if set(m.get("files", [])) != set(REQUIRED_FILES):
        raise PreflightError("manifest files list does not match required files")
    if tuple(m.get("contract_files", [])) != CONTRACT_FILES and set(
        m.get("contract_files", [])
    ) != set(CONTRACT_FILES):
        raise PreflightError("manifest contract_files does not match validator load list")
    if m.get("route_id") != "R1":
        raise PreflightError("manifest route_id must be R1")
    if m.get("package_status") != "preflight_only":
        raise PreflightError("manifest package_status must be preflight_only")
    if m.get("p1_execution_status") != "blocked":
        raise PreflightError("manifest p1_execution_status must be blocked")
    reuses = m.get("reuses", {})
    if str(reuses.get("r1_mock_package_hash")) != R1_MOCK_HASH:
        raise PreflightError("manifest reuses.r1_mock_package_hash mismatch")
    if reuses.get("measurement_source") != "pa_wu_p0":
        raise PreflightError("manifest reuses.measurement_source must be pa_wu_p0")
    if "pa_wu_r1_mock" not in str(reuses.get("r1_mock_package", "")):
        raise PreflightError("manifest reuses.r1_mock_package path invalid")
    invariants = m.get("invariants", {})
    if not isinstance(invariants, dict) or not all(
        v is True for v in invariants.values()
    ):
        raise PreflightError("manifest invariants must all be true")
    return m


# --------------------------------------------------------------------------
# Hashes
# --------------------------------------------------------------------------


def compute_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    payload = {name: contracts[name] for name in sorted(contracts)}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def compute_package_hash(contracts: dict[str, dict[str, Any]], manifest: dict[str, Any]) -> str:
    payload = {
        "manifest": manifest,
        "contracts": {name: contracts[name] for name in sorted(contracts)},
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
    check_no_secrets_no_clients_no_network()
    check_no_r2_r3_reads()
    check_required_gates_present(auth)

    # Actual R1 mock source verification (manifest cross-check + real validator).
    verified_hash = verify_r1_mock_source(route)
    validator_hash = run_r1_mock_validator()
    mock_ok = validator_hash == R1_MOCK_HASH
    source_ok = verified_hash == R1_MOCK_HASH and mock_ok

    gate_status = compute_gate_status(contracts, mock_ok, source_ok)

    # Declared required_gates must match computed values exactly.
    check_declared_matches_computed(auth, gate_status)

    # Authorization state machine (raises on illegal combinations).
    resolved_status = check_authorization_state_machine(auth, gate_status)

    resolved_gates = sorted(g for g, ok in gate_status.items() if ok)
    blocking_gates = sorted(g for g, ok in gate_status.items() if not ok)

    unresolved: list[str] = []
    if not gate_status["model_frozen"]:
        unresolved.append("model_selection_unresolved")
    if not gate_status["budget_approved"]:
        unresolved.append("budget_not_approved")
    if not gate_status["prompt_frozen"]:
        unresolved.append("prompt_not_frozen")
    if not gate_status["sampling_frozen"]:
        unresolved.append("sampling_not_frozen")
    if not gate_status["stop_conditions_frozen"]:
        unresolved.append("stop_thresholds_unresolved")
    if not gate_status["privacy_review_completed"]:
        unresolved.append("privacy_review_pending")
    if not gate_status["retry_policy_frozen"]:
        unresolved.append("retry_policy_not_frozen")
    if not gate_status["logging_contract_frozen"]:
        unresolved.append("logging_contract_not_frozen")

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
        "p1_execution_status": "authorized"
        if preflight_status == "authorized"
        else "blocked",
        "route_id": route.get("route_id"),
        "mock_package_hash": route.get("mock_package_hash"),
        "r1_mock_validator_hash": validator_hash,
    }


def main() -> None:  # pragma: no cover - convenience entry point
    report = build_preflight_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
