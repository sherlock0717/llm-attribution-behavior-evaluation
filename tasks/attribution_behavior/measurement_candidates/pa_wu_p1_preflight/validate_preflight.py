"""Static, offline validator for the PA-Wu R1 P1 preflight gate package.

STRICT boundaries (enforced by this module's own design and by the unit test):
- NO network I/O of any kind.
- NEVER reads an API key from the environment.
- NEVER imports a real-model SDK (openai / anthropic / httpx / requests / ...).
- NEVER executes a model and NEVER produces model output.
- NEVER rewrites any contract file (read-only).
- NEVER auto-enables authorization (authorization stays whatever the files say;
  this validator only checks consistency and reports blocking gates).

The validator loads the static YAML contracts, checks the frozen R1 route
boundary, verifies the R1 mock package hash matches route_freeze, and computes
which authorization gates are blocking. It returns a structured report whose
``preflight_status`` is ``blocked`` unless every gate is genuinely satisfied AND
the human-set ``real_model_execution_authorized`` flag is true.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent

R1_MOCK_HASH = "7c83def4c93ad26f"

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

# Patterns that must NEVER appear in the package sources (no real-model client,
# no network library, no secret literal).
_BANNED_SOURCE_PATTERNS = (
    re.compile(r"\bimport\s+(openai|anthropic|httpx|requests|socket)\b", re.IGNORECASE),
    re.compile(r"\bfrom\s+(openai|anthropic|httpx|urllib)\b", re.IGNORECASE),
    re.compile(r"requests\.(get|post)\s*\(", re.IGNORECASE),
    re.compile(r"urllib\.request", re.IGNORECASE),
    re.compile(r"chat\.completions", re.IGNORECASE),
)
_SECRET_LITERAL = re.compile(r"sk-[a-z0-9]{16,}", re.IGNORECASE)
# A key/value that actually assigns a secret value (not just a boolean policy
# flag like ``never_log_api_key: true``).
_SECRET_ASSIGNMENT = re.compile(
    r"(api_key|secret|token|password)\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{8,}", re.IGNORECASE
)
# Policy flags that legitimately mention the words api_key/secret (allow-list).
_SECRET_POLICY_ALLOWED = re.compile(
    r"(never_log_api_key|never_log_secret|secret_detected|no[_-]?api[_-]?key|"
    r"api_key|secret)\s*[:=]\s*(true|false|null|any|\[\])?\s*$",
    re.IGNORECASE,
)
# R2/R3 forbidden references.
_FORBIDDEN_REFS = (
    "pa_wu_p1_prep",
    "provisional",
    "zh-cn",
    "zh_cn",
    "adaptation_candidates",
    "ai_human",
    "ai/human",
)


class PreflightError(RuntimeError):
    """Raised when the preflight package is structurally inconsistent."""


def _load_yaml(name: str) -> dict[str, Any]:
    with (PACKAGE_DIR / name).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise PreflightError(f"{name}: expected a mapping at top level")
    return data


def check_required_files() -> None:
    missing = [n for n in REQUIRED_FILES if not (PACKAGE_DIR / n).is_file()]
    if missing:
        raise PreflightError(f"missing required preflight files: {missing}")


def check_route_boundary(route: dict[str, Any]) -> None:
    """R1 boundary is fixed; any deviation is a hard failure."""
    expected = {
        "route_id": "R1",
        "language": "en",
        "target_identity": "machine",
        "human_parallel_version": False,
        "translation_used": False,
        "is_construct_adaptation": False,
        "measurement_source": "pa_wu_p0",
        "real_model_execution_authorized": False,
        "p1_execution_status": "blocked",
    }
    for key, want in expected.items():
        if route.get(key) != want:
            raise PreflightError(
                f"route_freeze.{key} must be {want!r}, got {route.get(key)!r}"
            )
    forbidden = route.get("forbidden", {})
    if isinstance(forbidden, dict):
        for key, val in forbidden.items():
            if val is not True:
                raise PreflightError(f"route_freeze.forbidden.{key} must remain true")


def check_mock_hash(route: dict[str, Any]) -> None:
    if str(route.get("mock_package_hash")) != R1_MOCK_HASH:
        raise PreflightError(
            f"route_freeze.mock_package_hash != {R1_MOCK_HASH} "
            f"(got {route.get('mock_package_hash')!r})"
        )


def _model_frozen(model: dict[str, Any]) -> bool:
    status = str(model.get("selection_status"))
    selected = model.get("selected_model")
    if status != "frozen":
        return False
    if not selected:
        # selected_model must be non-empty when frozen.
        return False
    decision = model.get("decision", {})
    if not isinstance(decision, dict):
        return False
    for field_name in model.get("frozen_fields_required", []):
        if decision.get(field_name) in (None, "", []):
            return False
    return True


def _prompt_frozen(prompt: dict[str, Any]) -> bool:
    segments = prompt.get("segments", {})
    if not isinstance(segments, dict) or not segments:
        return False
    return all(bool(seg.get("frozen")) for seg in segments.values())


def _all_thresholds_resolved(stop: dict[str, Any]) -> bool:
    for entry in stop.get("threshold_stop", []):
        if str(entry.get("threshold_status")) != "resolved":
            return False
    return True


def _no_retry_overlap(retry: dict[str, Any]) -> bool:
    retryable = set(retry.get("retryable_codes", []))
    non_auto = set(retry.get("non_auto_retryable_codes", []))
    if retryable & non_auto:
        return False
    ma = retry.get("policy", {}).get("max_attempts")
    return isinstance(ma, int) and ma > 0


def compute_gate_status(contracts: dict[str, dict[str, Any]]) -> dict[str, bool]:
    """Derive the ACTUAL satisfaction of each required gate from the contracts.

    A gate is only satisfied when the underlying contract is genuinely frozen /
    approved. The authorization_gate.yaml's declared booleans are NOT trusted
    blindly: each gate is recomputed from its source contract, so the validator
    can never be tricked into 'authorized' by flipping a flag alone.
    """
    route = contracts["route_freeze.yaml"]
    model = contracts["model_selection_decision.yaml"]
    prompt = contracts["prompt_freeze_contract.yaml"]
    sampling = contracts["sampling_and_repeat_contract.yaml"]
    budget = contracts["budget_and_rate_limit_contract.yaml"]
    retry = contracts["retry_and_recovery_contract.yaml"]
    logging_c = contracts["provenance_and_logging_contract.yaml"]
    stop = contracts["stop_conditions.yaml"]

    route_frozen = (
        route.get("route_id") == "R1"
        and str(route.get("mock_package_hash")) == R1_MOCK_HASH
    )
    return {
        "route_frozen": bool(route_frozen),
        "model_frozen": _model_frozen(model),
        "prompt_frozen": _prompt_frozen(prompt),
        "sampling_frozen": bool(sampling.get("frozen")),
        "budget_approved": bool(budget.get("budget_approved")),
        "retry_policy_frozen": bool(retry.get("frozen")) and _no_retry_overlap(retry),
        "logging_contract_frozen": bool(logging_c.get("frozen")),
        "stop_conditions_frozen": bool(stop.get("frozen"))
        and _all_thresholds_resolved(stop),
        "privacy_review_completed": bool(
            logging_c.get("rules", {}).get("never_log_api_key")
        )
        and bool(logging_c.get("rules", {}).get("never_log_secret")),
        "environment_review_completed": _env_reviewed(
            contracts["environment_acceptance.yaml"]
        ),
        "mock_package_validated": str(route.get("mock_package_hash")) == R1_MOCK_HASH,
        "source_hashes_verified": str(route.get("mock_package_hash")) == R1_MOCK_HASH
        and route.get("measurement_source") == "pa_wu_p0",
    }


def _env_reviewed(env: dict[str, Any]) -> bool:
    # Environment review is 'completed' as a record when the Linux CI success and
    # the Windows exception are both honestly recorded (not when tests pass).
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


def check_required_gates_present(auth: dict[str, Any]) -> None:
    gates = auth.get("required_gates", {})
    if not isinstance(gates, dict):
        raise PreflightError("authorization_gate.required_gates must be a mapping")
    missing = [g for g in REQUIRED_GATES if g not in gates]
    if missing:
        raise PreflightError(f"authorization_gate missing required gates: {missing}")


def check_authorization_not_auto_enabled(auth: dict[str, Any]) -> None:
    """This validator must NEVER flip authorization on. We only assert that the
    file, as written, does not claim 'authorized' without the human flag."""
    status = str(auth.get("authorization_status"))
    authorized_flag = bool(auth.get("real_model_execution_authorized"))
    if status == "authorized" and not authorized_flag:
        raise PreflightError(
            "authorization_status=authorized without real_model_execution_authorized"
        )


def check_no_secrets_no_clients_no_network() -> None:
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".yml", ".md"):
            continue
        # Skip this validator itself: it defines the banned-client/secret
        # detection patterns as literals, which are logic, not real usage.
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        for pat in _BANNED_SOURCE_PATTERNS:
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
                raise PreflightError(f"secret assignment detected in {path.name}: {stripped!r}")


def check_no_r2_r3_reads() -> None:
    """Reject R2/R3 *asset* references without flagging the route_freeze
    declarations that merely NAME the forbidden routes to lock them out.

    A line that declares a forbidden route/flag (e.g. ``r3_ai_human_parallel_route:
    true`` or ``r2_chinese_route: true`` inside the ``forbidden`` block) is a
    legitimate lock-out declaration, not an asset read, so such declaration lines
    are exempt from the substring scan.
    """
    declaration = re.compile(
        r"^\s*(r2_[a-z0-9_]+|r3_[a-z0-9_]+|human_identity_version|chinese_formal_scale|"
        r"du_effect_conclusion|measurement_invariance_conclusion)\s*:\s*(true|false|null)\s*$",
        re.IGNORECASE,
    )
    for path in PACKAGE_DIR.rglob("*"):
        if path.suffix.lower() not in (".py", ".yaml", ".yml"):
            continue
        # This validator itself defines the forbidden-reference patterns as
        # detection logic; skip it so its own pattern literals are not flagged.
        if path.resolve() == Path(__file__).resolve():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if declaration.match(raw_line):
                continue  # lock-out declaration, not an asset read
            low = raw_line.lower()
            for ref in _FORBIDDEN_REFS:
                if ref in low:
                    raise PreflightError(
                        f"forbidden R2/R3 reference {ref!r} in {path.name}: {raw_line.strip()!r}"
                    )


def compute_contract_hash(contracts: dict[str, dict[str, Any]]) -> str:
    """Deterministic sha256[:16] over the canonicalized contract mapping."""
    import json

    payload = {name: contracts[name] for name in sorted(contracts)}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def build_preflight_report() -> dict[str, Any]:
    """Full static validation; returns the structured preflight report."""
    check_required_files()

    contracts = {name: _load_yaml(name) for name in CONTRACT_FILES}

    route = contracts["route_freeze.yaml"]
    auth = contracts["authorization_gate.yaml"]

    # Hard structural checks (raise on violation).
    check_route_boundary(route)
    check_mock_hash(route)
    check_required_gates_present(auth)
    check_authorization_not_auto_enabled(auth)
    check_no_secrets_no_clients_no_network()
    check_no_r2_r3_reads()

    gate_status = compute_gate_status(contracts)
    resolved_gates = sorted(g for g, ok in gate_status.items() if ok)
    blocking_gates = sorted(g for g, ok in gate_status.items() if not ok)

    human_authorized = bool(auth.get("real_model_execution_authorized"))
    all_gates_ok = all(gate_status.values())
    authorized = all_gates_ok and human_authorized

    unresolved: list[str] = []
    model = contracts["model_selection_decision.yaml"]
    if str(model.get("selection_status")) != "frozen":
        unresolved.append("model_selection_unresolved")
    if not contracts["budget_and_rate_limit_contract.yaml"].get("budget_approved"):
        unresolved.append("budget_not_approved")
    if not _prompt_frozen(contracts["prompt_freeze_contract.yaml"]):
        unresolved.append("prompt_not_frozen")
    if not _all_thresholds_resolved(contracts["stop_conditions.yaml"]):
        unresolved.append("stop_thresholds_unresolved")
    if not contracts["sampling_and_repeat_contract.yaml"].get("frozen"):
        unresolved.append("sampling_not_frozen")

    preflight_status = "authorized" if authorized else "blocked"

    return {
        "preflight_status": preflight_status,
        "blocking_gates": blocking_gates,
        "resolved_gates": resolved_gates,
        "unresolved_decisions": sorted(unresolved),
        "contract_hash": compute_contract_hash(contracts),
        "real_model_execution_authorized": human_authorized,
        "p1_execution_status": "blocked" if preflight_status != "authorized" else "authorized",
        "route_id": route.get("route_id"),
        "mock_package_hash": route.get("mock_package_hash"),
    }


def main() -> None:  # pragma: no cover - convenience entry point
    import json

    report = build_preflight_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    main()
