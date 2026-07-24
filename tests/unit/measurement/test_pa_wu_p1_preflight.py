"""Static tests for the PA-Wu R1 P1 preflight decision & authorization gates.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the offline validator: per-gate real satisfaction, the single
source authorization state machine (derived p1_execution_status), the manifest
chain, actual R1 mock source verification, the AST-based self security scan, the
controlled template resolver, and an end-to-end synthetic authorized run through
build_preflight_report().
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import shutil

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

MC_DIR = (
    PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates"
)
PKG_DIR = MC_DIR / "pa_wu_p1_preflight"
P0_ITEMS = MC_DIR / "pa_wu_p0" / "items_pa_2024.yaml"


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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ==========================================================================
# Initial state + single source
# ==========================================================================


def test_initial_preflight_blocked(report) -> None:
    assert report["preflight_status"] == "blocked"
    assert report["authorization_status"] == "blocked"
    assert report["real_model_execution_authorized"] is False
    assert report["p1_execution_status"] == "blocked"
    assert report["blocking_gates"]


def test_p1_status_only_derived_not_persisted(validator) -> None:
    # no contract or manifest persists p1_execution_status
    auth = _load("authorization_gate.yaml")
    assert "p1_execution_status" not in auth
    manifest = _load("preflight_manifest.yaml")
    assert "p1_execution_status" not in manifest
    route = _load("route_freeze.yaml")
    assert "p1_execution_status" not in route
    # but the report derives it
    assert "p1_execution_status" in validator.build_preflight_report()


def test_authorization_single_source(validator) -> None:
    route = _load("route_freeze.yaml")
    assert "real_model_execution_authorized" not in route
    auth = _load("authorization_gate.yaml")
    for key in ("real_model_execution_authorized", "authorization_status",
                "authorized_by", "authorized_at", "required_gates"):
        assert key in auth


def test_manifest_rejects_persisted_p1_status(validator, tmp_path, monkeypatch) -> None:
    m = _load("preflight_manifest.yaml")
    m["p1_execution_status"] = "blocked"
    for name in validator.REQUIRED_FILES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    (tmp_path / "preflight_manifest.yaml").write_text(
        yaml.safe_dump(m, allow_unicode=True), encoding="utf-8"
    )
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    with pytest.raises(validator.PreflightError):
        validator.check_manifest()


# ==========================================================================
# R1 mock actual verification + manifest chain
# ==========================================================================


def test_r1_mock_actually_validated(report, validator) -> None:
    assert report["r1_mock_validator_hash"] == validator.R1_MOCK_HASH


def test_r1_mock_hash_mismatch_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["mock_package_hash"] = "deadbeefdeadbeef"
    with pytest.raises(validator.PreflightError):
        validator.verify_r1_mock_source(route)


def test_manifest_in_chain(validator) -> None:
    m = validator.check_manifest()
    assert set(m["files"]) == set(validator.REQUIRED_FILES)


def test_manifest_stray_asset_rejected(validator, tmp_path, monkeypatch) -> None:
    for name in validator.REQUIRED_FILES:
        (tmp_path / name).write_text("x", encoding="utf-8")
    m = _load("preflight_manifest.yaml")
    (tmp_path / "preflight_manifest.yaml").write_text(
        yaml.safe_dump(m, allow_unicode=True), encoding="utf-8"
    )
    # add a stray undeclared yaml asset
    (tmp_path / "stray_contract.yaml").write_text("a: 1\n", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", tmp_path)
    with pytest.raises(validator.PreflightError):
        validator.check_manifest()


def test_hashes_present_and_distinct(report) -> None:
    assert report["contract_hash"] and report["package_hash"]
    assert report["contract_hash"] != report["package_hash"]


def test_contract_hash_deterministic(validator) -> None:
    a = validator.build_preflight_report()
    b = validator.build_preflight_report()
    assert a["contract_hash"] == b["contract_hash"]
    assert a["package_hash"] == b["package_hash"]


def test_hash_changes_on_change(validator) -> None:
    contracts = _all_contracts(validator)
    base = validator.compute_contract_hash(contracts)
    mutated = copy.deepcopy(contracts)
    mutated["route_freeze.yaml"]["route_id"] = "R1-X"
    assert validator.compute_contract_hash(mutated) != base


# ==========================================================================
# Route boundary
# ==========================================================================


@pytest.mark.parametrize(
    "key,value",
    [("route_id", "R2"), ("language", "zh"), ("target_identity", "human")],
)
def test_route_boundary_violations(validator, key, value) -> None:
    route = _load("route_freeze.yaml")
    route[key] = value
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


def test_route_carrying_auth_state_fails(validator) -> None:
    route = _load("route_freeze.yaml")
    route["p1_execution_status"] = "blocked"
    with pytest.raises(validator.PreflightError):
        validator.check_route_boundary(route)


# ==========================================================================
# Template resolver
# ==========================================================================


def test_template_resolver_reads_p0(validator) -> None:
    h = validator.template_content_hash("pa_wu_p0/items_pa_2024.yaml")
    assert h == _sha256_text(P0_ITEMS.read_text(encoding="utf-8"))


def test_template_resolver_rejects_escape(validator) -> None:
    with pytest.raises(validator.PreflightError):
        validator.resolve_template("../../../etc/passwd")
    with pytest.raises(validator.PreflightError):
        validator.resolve_template("pa_wu_r1_mock/mock_manifest.yaml")  # not whitelisted


def test_template_resolver_missing_file(validator) -> None:
    with pytest.raises(validator.PreflightError):
        validator.resolve_template("pa_wu_p0/does_not_exist.yaml")


# ==========================================================================
# Model gate: complete field coverage
# ==========================================================================


def test_model_frozen_fields_set_must_match(validator) -> None:
    model = _load("model_selection_decision.yaml")
    model["frozen_fields_required"] = model["frozen_fields_required"][:-1]
    with pytest.raises(validator.PreflightError):
        validator.check_model_frozen_fields_set(model)


def _frozen_model(validator) -> dict:
    return {
        "selection_status": "frozen",
        "selected_model": "acme-lm-1",
        "frozen_fields_required": list(validator.MODEL_FROZEN_FIELDS),
        "decision": {
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
        },
    }


@pytest.mark.parametrize(
    "field",
    [
        "provider",
        "model_id",
        "exact_model_version_or_snapshot",
        "endpoint_type",
        "access_method",
        "context_window_requirement",
        "pricing_snapshot_date",
        "pricing_source_recorded",
        "decided_by",
        "decided_at",
    ],
)
def test_model_field_empty_blocks(validator, field) -> None:
    model = _frozen_model(validator)
    model["decision"][field] = None
    assert validator._model_frozen(model) is False


@pytest.mark.parametrize(
    "field", ["provider_retention_policy_reviewed", "regional_availability_reviewed",
              "terms_of_use_reviewed"],
)
def test_model_review_flag_false_blocks(validator, field) -> None:
    model = _frozen_model(validator)
    model["decision"][field] = False
    assert validator._model_frozen(model) is False


def test_model_placeholder_blocks(validator) -> None:
    model = _frozen_model(validator)
    model["decision"]["provider"] = "placeholder"
    assert validator._model_frozen(model) is False


def test_model_source_references_empty_blocks(validator) -> None:
    model = _frozen_model(validator)
    model["decision"]["source_references"] = []
    assert validator._model_frozen(model) is False


# ==========================================================================
# Sampling / budget / stop boundaries
# ==========================================================================


def _full_sampling() -> dict:
    return {
        "temperature": 0.0,
        "top_p": 1.0,
        "max_output_tokens": 512,
        "seed": None,
        "seed_supported": False,
        "seed_is_determinism_guarantee": False,
        "linked_to_budget_contract": True,
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


def test_sampling_frozen_ok(validator) -> None:
    assert validator._sampling_frozen(_full_sampling()) is True


@pytest.mark.parametrize(
    "mutate",
    [
        {"temperature": -0.1},
        {"top_p": 0.0},
        {"top_p": 1.5},
        {"seed_supported": True, "seed": None},   # seed inconsistent
        {"seed_supported": False, "seed": 5},     # seed inconsistent
        {"concurrency": 1000},                    # concurrency > total
        {"linked_to_budget_contract": False},
        {"total_planned_requests": 25},           # != 8*3
    ],
)
def test_sampling_boundary_blocks(validator, mutate) -> None:
    s = _full_sampling()
    s.update(mutate)
    assert validator._sampling_frozen(s) is False


def _full_budget() -> dict:
    return {
        "budget_approved": True,
        "currency": "USD",
        "maximum_total_budget": 100.0,
        "warning_budget_threshold": 80.0,
        "maximum_cost_per_case": 5.0,
        "estimated_input_tokens": 1000,
        "estimated_output_tokens": 500,
        "total_planned_requests": 24,
        "concurrency_limit": 4,
        "requests_per_minute_limit": 60,
        "tokens_per_minute_limit": 90000,
        "budget_owner": "pi",
        "approval_timestamp": "2026-07-02",
        "pricing": {
            "source": "https://acme.example/pricing",
            "snapshot_date": "2026-07-01",
            "verified": True,
        },
    }


def test_budget_ok(validator) -> None:
    assert validator._budget_approved(_full_budget(), _full_sampling()) is True


@pytest.mark.parametrize(
    "mutate",
    [
        {"warning_budget_threshold": 200.0},   # > hard limit
        {"maximum_cost_per_case": 200.0},      # > hard limit
        {"total_planned_requests": 30},        # inconsistent with sampling
        {"concurrency_limit": 1},              # < sampling concurrency
        {"approval_timestamp": "later"},       # bad date format
    ],
)
def test_budget_incompatible_blocks(validator, mutate) -> None:
    b = _full_budget()
    b.update(mutate)
    assert validator._budget_approved(b, _full_sampling()) is False


def test_budget_cost_times_cases_exceeds_hardlimit_blocks(validator) -> None:
    b = _full_budget()
    b["maximum_cost_per_case"] = 20.0  # 20 * 8 = 160 > 100
    assert validator._budget_approved(b, _full_sampling()) is False


def _full_stop() -> dict:
    base = _load("stop_conditions.yaml")
    base["frozen"] = True
    for e in base["immediate_stop"]:
        e["owner"] = "ops"
    for e in base["threshold_stop"]:
        e["threshold_status"] = "resolved"
        e["threshold"] = 0.05
        e["owner"] = "ops"
    return base


def test_stop_ok(validator) -> None:
    assert validator._stop_conditions_frozen(_full_stop()) is True


def test_stop_missing_immediate_threshold_blocks(validator) -> None:
    stop = _full_stop()
    stop["immediate_stop"][0]["threshold"] = None
    assert validator._stop_conditions_frozen(stop) is False


def test_stop_missing_action_or_resume_blocks(validator) -> None:
    stop = _full_stop()
    stop["threshold_stop"][0]["action"] = None
    assert validator._stop_conditions_frozen(stop) is False
    stop2 = _full_stop()
    stop2["threshold_stop"][0]["resume_requires"] = None
    assert validator._stop_conditions_frozen(stop2) is False


def test_stop_rate_above_one_blocks(validator) -> None:
    stop = _full_stop()
    stop["threshold_stop"][0]["threshold"] = 1.5
    assert validator._stop_conditions_frozen(stop) is False


def test_stop_illegal_action_blocks(validator) -> None:
    stop = _full_stop()
    stop["threshold_stop"][0]["action"] = "explode"
    assert validator._stop_conditions_frozen(stop) is False


# ==========================================================================
# Privacy + retry
# ==========================================================================


def test_privacy_initial_pending() -> None:
    logging_c = _load("provenance_and_logging_contract.yaml")
    assert logging_c["privacy_review"]["status"] == "pending"


def test_privacy_pending_blocks(validator) -> None:
    logging_c = _load("provenance_and_logging_contract.yaml")
    logging_c["frozen"] = True
    logging_c["privacy_review"] = {"status": "pending", "reviewed_by": None, "reviewed_at": None}
    assert validator._privacy_review_completed(logging_c) is False


def test_retry_manual_must_equal_non_auto(validator) -> None:
    retry = _load("retry_and_recovery_contract.yaml")
    retry["frozen"] = True
    retry["manual_review_required_codes"] = ["timeout"]
    assert validator._retry_frozen(retry) is False


# ==========================================================================
# Authorization state machine
# ==========================================================================


def test_required_gates_must_equal_exact(validator) -> None:
    auth = _load("authorization_gate.yaml")
    del auth["required_gates"]["model_frozen"]
    with pytest.raises(validator.PreflightError):
        validator.check_required_gates_exact(auth)
    auth2 = _load("authorization_gate.yaml")
    auth2["required_gates"]["extra_gate"] = True
    with pytest.raises(validator.PreflightError):
        validator.check_required_gates_exact(auth2)


def test_declared_vs_computed_mismatch_fails(validator) -> None:
    auth = _load("authorization_gate.yaml")
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, False)
    with pytest.raises(validator.PreflightError):
        validator.check_declared_matches_computed(auth, gate_status)


@pytest.mark.parametrize(
    "status,flag,by,at,all_ok",
    [
        ("authorized", False, "pi", "t", True),   # flag false
        ("authorized", True, "pi", "t", False),   # a gate false
        ("authorized", True, None, "t", True),     # missing by
        ("authorized", True, "pi", None, True),    # missing at
        ("blocked", True, None, None, False),      # blocked + flag true
        ("maybe", False, None, None, False),       # illegal enum
    ],
)
def test_auth_state_machine_hard_fails(validator, status, flag, by, at, all_ok) -> None:
    auth = {
        "authorization_status": status,
        "real_model_execution_authorized": flag,
        "authorized_by": by,
        "authorized_at": at,
    }
    gate_status = dict.fromkeys(validator.REQUIRED_GATES, all_ok)
    with pytest.raises(validator.PreflightError):
        validator.check_authorization_state_machine(auth, gate_status)


# ==========================================================================
# End-to-end synthetic authorized via build_preflight_report
# ==========================================================================


def _write(path, data) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_end_to_end_synthetic_authorized(validator, tmp_path, monkeypatch) -> None:
    """Copy the whole package to tmp, write fully-frozen legal contracts, set
    authorization=authorized, and drive the entire build_preflight_report()."""
    dst = tmp_path / "pa_wu_p1_preflight"
    shutil.copytree(PKG_DIR, dst)

    # We reference the REAL P0 items file for item_block and a real local
    # template for other segments. Create a controlled template under the
    # package templates dir root used by the resolver whitelist.
    real_templates = PKG_DIR / "templates"
    real_templates.mkdir(exist_ok=True)
    seg_template = real_templates / "seg_e2e.txt"
    seg_template.write_text("frozen segment content", encoding="utf-8")
    seg_hash = _sha256_text(seg_template.read_text(encoding="utf-8"))
    item_ref = "pa_wu_p0/items_pa_2024.yaml"
    item_hash = validator.template_content_hash(item_ref)

    try:
        # route unchanged (already R1)
        # model
        model = _frozen_model(validator)
        _write(dst / "model_selection_decision.yaml", model)

        # prompt: all segments frozen via template_reference
        prompt = _load("prompt_freeze_contract.yaml")
        for name, seg in prompt["segments"].items():
            seg["frozen"] = True
            seg["owner"] = "researcher"
            seg["change_requires_new_run_version"] = True
            seg["content"] = None
            if name == "item_block":
                seg["template_reference"] = item_ref
                seg["sha256"] = item_hash
            else:
                seg["template_reference"] = "pa_wu_p1_preflight/templates/seg_e2e.txt"
                seg["sha256"] = seg_hash
        _write(dst / "prompt_freeze_contract.yaml", prompt)

        # sampling / budget / retry / logging / stop
        _write(dst / "sampling_and_repeat_contract.yaml", _full_sampling())
        _write(dst / "budget_and_rate_limit_contract.yaml", _full_budget())
        retry = _load("retry_and_recovery_contract.yaml")
        retry["frozen"] = True
        _write(dst / "retry_and_recovery_contract.yaml", retry)
        logging_c = _load("provenance_and_logging_contract.yaml")
        logging_c["frozen"] = True
        logging_c["privacy_review"] = {
            "status": "completed",
            "reviewed_by": "dpo",
            "reviewed_at": "2026-07-02T12:00",
        }
        _write(dst / "provenance_and_logging_contract.yaml", logging_c)
        _write(dst / "stop_conditions.yaml", _full_stop())

        # authorization: authorized with all required_gates true
        auth = _load("authorization_gate.yaml")
        auth["required_gates"] = dict.fromkeys(validator.REQUIRED_GATES, True)
        auth["authorization_status"] = "authorized"
        auth["real_model_execution_authorized"] = True
        auth["authorized_by"] = "pi"
        auth["authorized_at"] = "2026-07-02T13:00"
        _write(dst / "authorization_gate.yaml", auth)

        monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
        report = validator.build_preflight_report()
        assert report["preflight_status"] == "authorized"
        assert report["p1_execution_status"] == "authorized"
        assert report["blocking_gates"] == []
        assert report["authorization_status"] == "authorized"
    finally:
        shutil.rmtree(real_templates, ignore_errors=True)


# ==========================================================================
# Security scan via formal production path
# ==========================================================================


def test_validator_self_ast_clean(validator) -> None:
    validator.check_validator_self_ast()


def test_scan_rejects_import_requests(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import requests\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_dynamic_import(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import importlib\nimportlib.import_module('requests')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_dunder_import(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("__import__('socket')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_subprocess_network_cli(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import subprocess\nsubprocess.run('curl http://x')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_r2_r3_path_open(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("open('adaptation_candidates/x.yaml')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_secret_scan_not_bypassed_by_marker(validator, tmp_path) -> None:
    p = tmp_path / "m.yaml"
    p.write_text(
        'api_key: "abcdef0123456789"  # preflight-detection-pattern\n', encoding="utf-8"
    )
    with pytest.raises(validator.PreflightError):
        validator.scan_text_secrets(p)


def test_secret_literal_rejected(validator, tmp_path) -> None:
    p = tmp_path / "m.yaml"
    p.write_text('token: "sk-abcdef0123456789abcdef"\n', encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_text_secrets(p)


def test_full_package_security_scan_passes(validator) -> None:
    validator.check_no_secrets_no_clients_no_network()  # raises on violation


# ==========================================================================
# Environment acceptance
# ==========================================================================


def test_environment_acceptance_records_windows_exception() -> None:
    env = _load("environment_acceptance.yaml")
    assert env["linux_ci"]["run_number"] == 71
    assert env["linux_ci"]["status"] == "success"
    win = env["windows_local"]
    assert win["full_pytest_status"] == "environment_specific_failures"
    assert win["failed_count"] == 5
    qual = env["windows_failure_qualification"]
    assert qual["in_pr_10_diff"] is False
    assert qual["is_r1_mock_regression"] is False
    assert qual["is_fixed"] is False
