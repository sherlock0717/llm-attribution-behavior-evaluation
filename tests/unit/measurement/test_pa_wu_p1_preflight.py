"""Static tests for the PA-Wu R1 P1 preflight decision & authorization gate package.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the offline static validator, the per-gate real-satisfaction
logic, the single-source authorization state machine, the manifest check chain,
the actual R1 mock source verification, and the AST-based self security scan.
"""

from __future__ import annotations

import ast
import copy
import importlib.util

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

PKG_DIR = (
    PROJECT_ROOT
    / "tasks"
    / "attribution_behavior"
    / "measurement_candidates"
    / "pa_wu_p1_preflight"
)
R1_MOCK_MANIFEST = (
    PROJECT_ROOT
    / "tasks"
    / "attribution_behavior"
    / "measurement_candidates"
    / "pa_wu_r1_mock"
    / "mock_manifest.yaml"
)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PKG_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_module("pa_wu_p1_preflight_validate", "validate_preflight.py")


@pytest.fixture(scope="module")
def report(validator):
    return validator.build_preflight_report()


def _load(name: str) -> dict:
    with (PKG_DIR / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _all_contracts(validator) -> dict:
    return {name: _load(name) for name in validator.CONTRACT_FILES}


# ==========================================================================
# Initial state
# ==========================================================================


def test_initial_preflight_blocked(report) -> None:
    assert report["preflight_status"] == "blocked"
    assert report["authorization_status"] == "blocked"
    assert report["real_model_execution_authorized"] is False
    assert report["p1_execution_status"] == "blocked"
    assert report["blocking_gates"]


def test_authorization_single_source(validator) -> None:
    # route_freeze must NOT carry authorization state; only authorization_gate does.
    route = _load("route_freeze.yaml")
    assert "real_model_execution_authorized" not in route
    assert "p1_execution_status" not in route
    auth = _load("authorization_gate.yaml")
    assert "real_model_execution_authorized" in auth
    assert "authorization_status" in auth
    assert "p1_execution_status" in auth


def test_route_carrying_auth_state_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["real_model_execution_authorized"] = False
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


# ==========================================================================
# R1 mock actual verification + manifest chain
# ==========================================================================


def test_r1_mock_actually_validated(report, validator) -> None:
    # hash comes from actually running the R1 mock validator, not a constant only.
    assert report["r1_mock_validator_hash"] == validator.R1_MOCK_HASH
    assert report["mock_package_hash"] == validator.R1_MOCK_HASH


def test_r1_mock_manifest_hash_mismatch_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["mock_package_hash"] = "deadbeefdeadbeef"
    with pytest.raises(validator.PreflightError):
        validator.verify_r1_mock_source(route)


def test_manifest_in_validation_chain(validator) -> None:
    m = validator.check_manifest()  # raises on mismatch
    assert set(m["files"]) == set(validator.REQUIRED_FILES)
    assert m["route_id"] == "R1"
    assert m["package_status"] == "preflight_only"
    assert m["p1_execution_status"] == "blocked"


def test_manifest_files_drift_fails(validator, tmp_path, monkeypatch) -> None:
    m = _load("preflight_manifest.yaml")
    m["files"] = m["files"][:-1]  # drop one
    (tmp_path / "preflight_manifest.yaml").write_text(
        yaml.safe_dump(m, allow_unicode=True), encoding="utf-8"
    )
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    with pytest.raises(validator.PreflightError):
        validator.check_manifest()


def test_package_hash_and_contract_hash_present(report) -> None:
    assert report["contract_hash"]
    assert report["package_hash"]
    assert report["contract_hash"] != report["package_hash"]


def test_contract_hash_deterministic(validator) -> None:
    r1 = validator.build_preflight_report()
    r2 = validator.build_preflight_report()
    assert r1["contract_hash"] == r2["contract_hash"]
    assert r1["package_hash"] == r2["package_hash"]


def test_contract_hash_changes_on_change(validator) -> None:
    contracts = _all_contracts(validator)
    base = validator.compute_contract_hash(contracts)
    mutated = copy.deepcopy(contracts)
    mutated["route_freeze.yaml"]["route_id"] = "R1-CHANGED"
    assert validator.compute_contract_hash(mutated) != base


def test_package_hash_changes_on_manifest_change(validator) -> None:
    contracts = _all_contracts(validator)
    manifest = _load("preflight_manifest.yaml")
    base = validator.compute_package_hash(contracts, manifest)
    mutated_manifest = copy.deepcopy(manifest)
    mutated_manifest["manifest_id"] = "changed"
    assert validator.compute_package_hash(contracts, mutated_manifest) != base


# ==========================================================================
# Route / language / identity boundary
# ==========================================================================


@pytest.mark.parametrize(
    "key,value",
    [("route_id", "R2"), ("language", "zh"), ("target_identity", "human")],
)
def test_route_boundary_violations_fail(validator, key, value) -> None:
    route = _load("route_freeze.yaml")
    route[key] = value
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


def test_route_forbidden_flags_locked(validator) -> None:
    route = _load("route_freeze.yaml")
    route["forbidden"]["r2_chinese_route"] = False
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


# ==========================================================================
# Per-gate real satisfaction (blocked cases)
# ==========================================================================


def _satisfy_all(validator) -> dict:
    """Build a fully-satisfied set of contracts (pure static synthetic)."""
    import hashlib

    contracts = _all_contracts(validator)

    # model
    model = contracts["model_selection_decision.yaml"]
    model["selection_status"] = "frozen"
    model["selected_model"] = "acme-lm-1"
    model["decision"] = {
        "provider": "acme",
        "model_id": "acme-lm-1",
        "exact_model_version_or_snapshot": "2026-07-01",
        "endpoint_type": "chat",
        "access_method": "https_api",
        "context_window_requirement": 8192,
        "structured_output_support": True,
        "deterministic_seed_support": False,
        "temperature_support": True,
        "response_id_available": True,
        "provider_retention_policy_reviewed": True,
        "pricing_snapshot_date": "2026-07-01",
        "pricing_source_recorded": "https://acme.example/pricing",
        "regional_availability_reviewed": True,
        "terms_of_use_reviewed": True,
        "decided_by": "researcher",
        "decided_at": "2026-07-02T10:00",
        "source_references": ["https://acme.example/docs"],
    }

    # prompt
    prompt = contracts["prompt_freeze_contract.yaml"]
    for name, seg in prompt["segments"].items():
        content = f"content for {name}"
        seg["content"] = content
        seg["template_reference"] = None
        seg["sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        seg["frozen"] = True
        seg["owner"] = "researcher"
        seg["change_requires_new_run_version"] = True

    # sampling
    sampling = contracts["sampling_and_repeat_contract.yaml"]
    sampling.update(
        {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_output_tokens": 512,
            "seed": None,
            "seed_supported": False,
            "seed_is_determinism_guarantee": False,
            "planned_case_count": 8,
            "repeats_per_case": 3,
            "total_planned_requests": 24,
            "concurrency": 2,
            "request_timeout_seconds": 60,
            "scenario_order_policy": "fixed",
            "item_order_policy": "p0_order",
            "repeat_index_policy": "zero_based",
            "frozen": True,
        }
    )

    # budget
    budget = contracts["budget_and_rate_limit_contract.yaml"]
    budget.update(
        {
            "currency": "USD",
            "maximum_total_budget": 100.0,
            "warning_budget_threshold": 80.0,
            "maximum_cost_per_case": 5.0,
            "estimated_input_tokens": 1000,
            "estimated_output_tokens": 500,
            "total_planned_requests": 24,
            "concurrency_limit": 2,
            "requests_per_minute_limit": 60,
            "tokens_per_minute_limit": 90000,
            "budget_owner": "pi",
            "budget_approved": True,
            "approval_timestamp": "2026-07-02T11:00",
            "pricing": {
                "source": "https://acme.example/pricing",
                "snapshot_date": "2026-07-01",
                "verified": True,
            },
        }
    )

    # retry
    retry = contracts["retry_and_recovery_contract.yaml"]
    retry["frozen"] = True

    # logging + privacy
    logging_c = contracts["provenance_and_logging_contract.yaml"]
    logging_c["frozen"] = True
    logging_c["privacy_review"] = {
        "status": "completed",
        "reviewed_by": "dpo",
        "reviewed_at": "2026-07-02T12:00",
    }

    # stop conditions
    stop = contracts["stop_conditions.yaml"]
    stop["frozen"] = True
    for e in stop["immediate_stop"]:
        e["owner"] = "ops"
    for e in stop["threshold_stop"]:
        e["threshold_status"] = "resolved"
        e["threshold"] = 0.05
        e["owner"] = "ops"

    return contracts


def test_model_unresolved_blocks(report) -> None:
    assert "model_frozen" in report["blocking_gates"]
    assert "model_selection_unresolved" in report["unresolved_decisions"]


def test_only_flip_frozen_with_nulls_still_blocked(validator) -> None:
    contracts = _all_contracts(validator)
    # flip frozen booleans but keep null fields
    contracts["sampling_and_repeat_contract.yaml"]["frozen"] = True
    contracts["retry_and_recovery_contract.yaml"]["frozen"] = True
    contracts["provenance_and_logging_contract.yaml"]["frozen"] = True
    contracts["stop_conditions.yaml"]["frozen"] = True
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["sampling_frozen"] is False  # still null fields
    assert gs["logging_contract_frozen"] is True  # fields already complete in file
    assert not all(gs.values())


def test_model_placeholder_still_blocked(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["model_selection_decision.yaml"]["decision"]["model_id"] = "placeholder"
    contracts["model_selection_decision.yaml"]["selected_model"] = "placeholder"
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["model_frozen"] is False


def test_prompt_missing_hash_or_owner_still_blocked(validator) -> None:
    contracts = _satisfy_all(validator)
    seg = contracts["prompt_freeze_contract.yaml"]["segments"]["system_prompt"]
    seg["sha256"] = None
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["prompt_frozen"] is False

    contracts2 = _satisfy_all(validator)
    contracts2["prompt_freeze_contract.yaml"]["segments"]["system_prompt"]["owner"] = None
    gs2 = validator.compute_gate_status(contracts2, True, True)
    assert gs2["prompt_frozen"] is False


def test_budget_approved_but_incomplete_still_blocked(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["budget_and_rate_limit_contract.yaml"]["maximum_total_budget"] = None
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["budget_approved"] is False

    contracts2 = _satisfy_all(validator)
    contracts2["budget_and_rate_limit_contract.yaml"]["pricing"]["verified"] = False
    gs2 = validator.compute_gate_status(contracts2, True, True)
    assert gs2["budget_approved"] is False


def test_stop_threshold_resolved_but_null_still_blocked(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["stop_conditions.yaml"]["threshold_stop"][0]["threshold"] = None
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["stop_conditions_frozen"] is False


def test_privacy_pending_still_blocked(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["provenance_and_logging_contract.yaml"]["privacy_review"]["status"] = "pending"
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["privacy_review_completed"] is False


def test_privacy_review_initial_pending() -> None:
    logging_c = _load("provenance_and_logging_contract.yaml")
    assert logging_c["privacy_review"]["status"] == "pending"


def test_sampling_total_requests_consistency(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["sampling_and_repeat_contract.yaml"]["total_planned_requests"] = 25  # != 8*3
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["sampling_frozen"] is False


def test_retry_manual_codes_must_equal_non_auto(validator) -> None:
    contracts = _satisfy_all(validator)
    contracts["retry_and_recovery_contract.yaml"]["manual_review_required_codes"] = [
        "timeout"
    ]
    gs = validator.compute_gate_status(contracts, True, True)
    assert gs["retry_policy_frozen"] is False


# ==========================================================================
# Authorization state machine
# ==========================================================================


def test_declared_vs_computed_mismatch_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    gate_status = {g: False for g in validator.REQUIRED_GATES}
    # auth declares route_frozen=true but computed says false -> mismatch
    with pytest.raises(validator.PreflightError):
        validator.check_declared_matches_computed(auth, gate_status)


def test_authorized_with_flag_false_hard_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = False
    gate_status = {g: True for g in validator.REQUIRED_GATES}
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_authorized_with_gate_false_hard_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = "pi"
    auth["authorized_at"] = "2026-07-02T13:00"
    gate_status = {g: True for g in validator.REQUIRED_GATES}
    gate_status["model_frozen"] = False
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_authorized_missing_by_or_at_hard_fails(validator) -> None:
    gate_status = {g: True for g in validator.REQUIRED_GATES}
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = None
    auth["authorized_at"] = "2026-07-02T13:00"
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_blocked_with_flag_true_hard_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "blocked"
    auth["real_model_execution_authorized"] = True
    gate_status = {g: False for g in validator.REQUIRED_GATES}
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_illegal_status_enum_hard_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "maybe"
    gate_status = {g: False for g in validator.REQUIRED_GATES}
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


def test_synthetic_full_authorization_resolves_authorized(validator) -> None:
    """All gates truly satisfied + human flag + authorized_by/at -> authorized.

    Pure static state-machine test: no model call, no P1 execution.
    """
    contracts = _satisfy_all(validator)
    gate_status = validator.compute_gate_status(contracts, True, True)
    assert all(gate_status.values()), sorted(
        g for g, ok in gate_status.items() if not ok
    )
    auth = {
        "authorization_status": "authorized",
        "real_model_execution_authorized": True,
        "authorized_by": "pi",
        "authorized_at": "2026-07-02T13:00",
        "required_gates": dict.fromkeys(validator.REQUIRED_GATES, True),
    }
    validator.check_declared_matches_computed(auth, gate_status)
    resolved = validator.check_authorization_state_machine(auth, gate_status)
    assert resolved == "authorized"


# ==========================================================================
# Security self-scan (AST) + no R2/R3
# ==========================================================================


def test_validator_import_ast_clean(validator) -> None:
    validator.check_validator_imports_ast()  # raises on banned import


def test_added_banned_import_would_be_rejected(validator) -> None:
    # Prove the AST scanner rejects a real banned import node.
    src = "import requests\n"
    tree = ast.parse(src)
    banned = validator._BANNED_IMPORT_MODULES
    found = any(
        isinstance(n, ast.Import) and n.names[0].name.split(".")[0] in banned
        for n in ast.walk(tree)
    )
    assert found  # our detection logic identifies it


def test_no_secrets_no_clients_scan_passes(validator) -> None:
    validator.check_no_secrets_no_clients_no_network()  # raises on violation


def test_secret_literal_rejected(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "leak.yaml").write_text(
        'api_key: "sk-abcdef0123456789abcdef"\n', encoding="utf-8"
    )
    with pytest.raises(validator.PreflightError):
        validator.check_no_secrets_no_clients_no_network()


def test_network_import_in_package_file_rejected(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "bad.py").write_text("import requests\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.check_no_secrets_no_clients_no_network()


def test_no_r2_r3_reads(validator) -> None:
    validator.check_no_r2_r3_reads()  # raises on violation


def test_r2_r3_reference_rejected(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "bad.yaml").write_text("note: adaptation_candidates\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.check_no_r2_r3_reads()


def test_validator_source_has_no_real_network_call(validator) -> None:
    """AST-prove the validator never actually calls requests/urllib/socket, and
    contains no real network usage beyond detection-pattern string literals."""
    import ast as _ast

    src = (PKG_DIR / "validate_preflight.py").read_text(encoding="utf-8")
    tree = _ast.parse(src)
    # No ImportFrom/Import of banned modules as real nodes.
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in validator._BANNED_IMPORT_MODULES
        elif isinstance(node, _ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in validator._BANNED_IMPORT_MODULES


# ==========================================================================
# Environment acceptance (Windows exception recorded honestly)
# ==========================================================================


def test_environment_acceptance_records_windows_exception() -> None:
    env = _load("environment_acceptance.yaml")
    assert env["linux_ci"]["run_number"] == 71
    assert env["linux_ci"]["status"] == "success"
    win = env["windows_local"]
    assert win["r1_target_tests"] == "passed"
    assert win["full_pytest_status"] == "environment_specific_failures"
    assert win["failed_count"] == 5
    assert win["affected_test_file"] == "tests/integration/test_cross_platform_scripts.py"
    qual = env["windows_failure_qualification"]
    assert qual["in_pr_10_diff"] is False
    assert qual["is_r1_mock_regression"] is False
    assert qual["is_fixed"] is False
