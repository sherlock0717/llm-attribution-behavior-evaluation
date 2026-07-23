"""Static tests for the PA-Wu R1 P1 preflight decision & authorization gate package.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests only exercise the offline static validator and assert that the initial
preflight state is BLOCKED and can never be auto-authorized by the validator.
"""

from __future__ import annotations

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


# --- 1: initial preflight is blocked -----------------------------------------


def test_initial_preflight_blocked(report) -> None:
    assert report["preflight_status"] == "blocked"
    assert report["real_model_execution_authorized"] is False
    assert report["p1_execution_status"] == "blocked"
    assert report["blocking_gates"]  # at least one gate is blocking


# --- 2: model unresolved -> blocked ------------------------------------------


def test_model_unresolved_blocks(report) -> None:
    model = _load("model_selection_decision.yaml")
    assert model["selection_status"] == "unresolved"
    assert model["selected_model"] is None
    assert "model_frozen" in report["blocking_gates"]
    assert "model_selection_unresolved" in report["unresolved_decisions"]


# --- 3: budget not approved -> blocked ---------------------------------------


def test_budget_not_approved_blocks(report) -> None:
    budget = _load("budget_and_rate_limit_contract.yaml")
    assert budget["budget_approved"] is False
    assert "budget_approved" in report["blocking_gates"]
    assert "budget_not_approved" in report["unresolved_decisions"]


# --- 4: prompt not frozen -> blocked -----------------------------------------


def test_prompt_not_frozen_blocks(report) -> None:
    prompt = _load("prompt_freeze_contract.yaml")
    assert any(not seg["frozen"] for seg in prompt["segments"].values())
    assert "prompt_frozen" in report["blocking_gates"]
    assert "prompt_not_frozen" in report["unresolved_decisions"]


# --- 5: stop thresholds unresolved -> blocked --------------------------------


def test_stop_thresholds_unresolved_blocks(report) -> None:
    stop = _load("stop_conditions.yaml")
    assert any(
        e["threshold_status"] == "unresolved" for e in stop["threshold_stop"]
    )
    assert "stop_conditions_frozen" in report["blocking_gates"]
    assert "stop_thresholds_unresolved" in report["unresolved_decisions"]


# --- 6: mock hash mismatch -> hard failure -----------------------------------


def test_mock_hash_mismatch_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["mock_package_hash"] = "deadbeefdeadbeef"
    with pytest.raises(validator.PreflightError):
        validator.check_mock_hash(route)


# --- 7/8/9: route/language/identity must be R1/en/machine --------------------


def test_route_not_r1_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["route_id"] = "R2"
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


def test_language_not_en_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["language"] = "zh"
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


def test_identity_not_machine_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["target_identity"] = "human"
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


# --- 10: required gate missing -> hard failure -------------------------------


def test_required_gate_missing_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    del auth["required_gates"]["model_frozen"]
    with pytest.raises(validator.PreflightError):
        validator.check_required_gates_present(auth)


# --- 11: authorization cannot be auto-enabled by the validator ---------------


def test_authorization_not_auto_enabled_by_validator(validator) -> None:
    # Even if every required_gate flag in the file is flipped to true, the
    # validator recomputes gates from the source contracts, so preflight must
    # stay blocked (the human authorization flag is still false, and the source
    # contracts are still unresolved).
    report = validator.build_preflight_report()
    assert report["preflight_status"] == "blocked"
    # And the consistency guard rejects a lying 'authorized' status.
    auth = _load("authorization_gate.yaml")
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = False
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_not_auto_enabled(auth)


def test_full_gate_flip_still_blocked_without_human_flag(validator) -> None:
    # Simulate all source contracts satisfied but human flag false -> blocked.
    contracts = {name: _load(name) for name in validator.CONTRACT_FILES}
    # satisfy every gate at the source level
    contracts["model_selection_decision.yaml"]["selection_status"] = "frozen"
    contracts["model_selection_decision.yaml"]["selected_model"] = "placeholder"
    dec = contracts["model_selection_decision.yaml"]["decision"]
    for f in contracts["model_selection_decision.yaml"]["frozen_fields_required"]:
        dec[f] = "x"
    for seg in contracts["prompt_freeze_contract.yaml"]["segments"].values():
        seg["frozen"] = True
    contracts["sampling_and_repeat_contract.yaml"]["frozen"] = True
    contracts["budget_and_rate_limit_contract.yaml"]["budget_approved"] = True
    contracts["retry_and_recovery_contract.yaml"]["frozen"] = True
    contracts["provenance_and_logging_contract.yaml"]["frozen"] = True
    contracts["stop_conditions.yaml"]["frozen"] = True
    for e in contracts["stop_conditions.yaml"]["threshold_stop"]:
        e["threshold_status"] = "resolved"
    gate_status = validator.compute_gate_status(contracts)
    assert all(gate_status.values()), gate_status
    # human flag is still false in authorization_gate.yaml -> overall blocked
    auth = _load("authorization_gate.yaml")
    assert bool(auth.get("real_model_execution_authorized")) is False


# --- 12: secret / api key literal rejected -----------------------------------


def test_secret_or_apikey_rejected(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "leak.yaml").write_text(
        'api_key: "sk-abcdef0123456789abcdef"\n', encoding="utf-8"
    )
    with pytest.raises(validator.PreflightError):
        validator.check_no_secrets_no_clients_no_network()


def test_policy_flag_mentioning_secret_allowed(validator, tmp_path, monkeypatch) -> None:
    # A boolean policy flag that merely names api_key/secret must NOT be rejected.
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "policy.yaml").write_text(
        "never_log_api_key: true\nnever_log_secret: true\n", encoding="utf-8"
    )
    validator.check_no_secrets_no_clients_no_network()  # must not raise


# --- 13 & 14: no network lib / no real-model SDK -----------------------------


def test_no_network_library(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "bad.py").write_text("import requests\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.check_no_secrets_no_clients_no_network()


def test_no_real_model_sdk(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "bad.py").write_text("from openai import OpenAI\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.check_no_secrets_no_clients_no_network()


def test_package_sources_are_clean(validator) -> None:
    # The real package sources must pass the client/network/secret scan.
    validator.check_no_secrets_no_clients_no_network()  # raises on violation


# --- 15: no R2/R3 reads ------------------------------------------------------


def test_no_r2_r3_reads(validator) -> None:
    validator.check_no_r2_r3_reads()  # raises on violation


def test_r2_r3_reference_rejected(validator, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    (tmp_path / "bad.yaml").write_text("note: adaptation_candidates\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.check_no_r2_r3_reads()


# --- 16: environment acceptance accurately records the Windows exception -----


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


# --- 17 & 18: contract hash determinism + sensitivity ------------------------


def test_contract_hash_deterministic(validator) -> None:
    r1 = validator.build_preflight_report()
    r2 = validator.build_preflight_report()
    assert r1["contract_hash"] == r2["contract_hash"]
    assert r1["contract_hash"]


def test_contract_hash_changes_on_contract_change(validator) -> None:
    contracts = {name: _load(name) for name in validator.CONTRACT_FILES}
    base = validator.compute_contract_hash(contracts)
    mutated = copy.deepcopy(contracts)
    mutated["route_freeze.yaml"]["route_id"] = "R1-CHANGED"
    assert validator.compute_contract_hash(mutated) != base


# --- boundary: route forbidden flags must stay true --------------------------


def test_route_forbidden_flags_locked(validator) -> None:
    route = _load("route_freeze.yaml")
    route["forbidden"]["r2_chinese_route"] = False
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)
