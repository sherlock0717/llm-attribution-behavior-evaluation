"""Static tests for the PA-Wu R1 P1 preflight decision & authorization gates.

NO real model, NO network, NO API key, NO model output, NO P1 execution. These
tests exercise the offline validator: item_block P0 source-bundle composite hash,
fully tmp-isolated end-to-end synthetic authorized run, manifest recursive asset
management + package hash coverage, finite/date validation, formal AST security
scan (no bypass), and cross-contract consistency.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import shutil
import subprocess

import pytest
import yaml

from freewill_attribution.paths import PROJECT_ROOT

MC_DIR = PROJECT_ROOT / "tasks" / "attribution_behavior" / "measurement_candidates"
PKG_DIR = MC_DIR / "pa_wu_p1_preflight"
P0_DIR = MC_DIR / "pa_wu_p0"
R1_DIR = MC_DIR / "pa_wu_r1_mock"


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


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ==========================================================================
# Initial state
# ==========================================================================


def test_initial_preflight_blocked(report) -> None:
    assert report["preflight_status"] == "blocked"
    assert report["authorization_status"] == "blocked"
    assert report["p1_execution_status"] == "blocked"
    assert "environment_review_completed" in report["blocking_gates"]


def test_p1_status_only_derived(validator) -> None:
    for name in ("route_freeze.yaml", "authorization_gate.yaml", "preflight_manifest.yaml"):
        assert "p1_execution_status" not in _load(name)
    assert "p1_execution_status" in validator.build_preflight_report()


# ==========================================================================
# 一、item_block P0 source bundle + composite hash
# ==========================================================================


def test_item_block_bundle_declared() -> None:
    prompt = _load("prompt_freeze_contract.yaml")
    seg = prompt["segments"]["item_block"]
    assert seg["source_bundle"] == [
        "pa_wu_p0/items_pa_2024.yaml",
        "pa_wu_p0/items_wu_shen_2026.yaml",
        "pa_wu_p0/forms.yaml",
    ]


def _bundle_seg(validator, bundle=None) -> dict:
    bundle = bundle if bundle is not None else list(validator.ITEM_BLOCK_P0_BUNDLE)
    return {
        "content": None,
        "template_reference": None,
        "source_bundle": bundle,
        "sha256": validator.source_bundle_hash(bundle),
        "frozen": True,
        "owner": "researcher",
        "change_requires_new_run_version": True,
    }


def test_item_block_bundle_ok(validator) -> None:
    assert validator._segment_ok("item_block", _bundle_seg(validator)) is True


def test_item_block_bundle_missing_entry_fails(validator) -> None:
    bad = _bundle_seg(validator, ["pa_wu_p0/items_pa_2024.yaml", "pa_wu_p0/forms.yaml"])
    assert validator._segment_ok("item_block", bad) is False


def test_item_block_bundle_reorder_fails(validator) -> None:
    reordered = [
        "pa_wu_p0/forms.yaml",
        "pa_wu_p0/items_pa_2024.yaml",
        "pa_wu_p0/items_wu_shen_2026.yaml",
    ]
    seg = _bundle_seg(validator, reordered)  # hash computed on reordered
    # sha matches reordered content but bundle != fixed order -> fails
    assert validator._segment_ok("item_block", seg) is False


def test_item_block_bundle_extra_or_wrong_file_fails(validator) -> None:
    bad = _bundle_seg(
        validator,
        [
            "pa_wu_p0/items_pa_2024.yaml",
            "pa_wu_p0/items_wu_shen_2026.yaml",
            "pa_wu_p0/README.md",
        ],
    )
    assert validator._segment_ok("item_block", bad) is False


def test_item_block_reference_manifest_fails(validator) -> None:
    # Referencing other P0 files (README/manifest) instead of the fixed bundle
    # fails the gate: the bundle list differs from the fixed order.
    seg = {
        "content": None,
        "template_reference": None,
        "source_bundle": ["pa_wu_p0/manifest.yaml", "pa_wu_p0/README.md"],
        "sha256": "0" * 64,
        "frozen": True,
        "owner": "r",
        "change_requires_new_run_version": True,
    }
    assert validator._segment_ok("item_block", seg) is False
    # A reference outside the whitelist raises in the resolver.
    with pytest.raises(validator.PreflightError):
        validator.source_bundle_hash(["pa_wu_r1_mock/mock_manifest.yaml"])


def test_item_block_hash_changes_when_pa_or_wu_or_forms_change(validator, tmp_path, monkeypatch) -> None:
    # Build an isolated MC with copied P0, mutate each file, hash must change.
    mc = tmp_path / "measurement_candidates"
    (mc / "pa_wu_p1_preflight").mkdir(parents=True)
    shutil.copytree(P0_DIR, mc / "pa_wu_p0")
    monkeypatch.setattr(validator, "PACKAGE_DIR", mc / "pa_wu_p1_preflight")
    base = validator.source_bundle_hash(list(validator.ITEM_BLOCK_P0_BUNDLE))

    pa = mc / "pa_wu_p0" / "items_pa_2024.yaml"
    pa.write_text(pa.read_text(encoding="utf-8") + "\n# x\n", encoding="utf-8")
    assert validator.source_bundle_hash(list(validator.ITEM_BLOCK_P0_BUNDLE)) != base

    shutil.rmtree(mc / "pa_wu_p0")
    shutil.copytree(P0_DIR, mc / "pa_wu_p0")
    wu = mc / "pa_wu_p0" / "items_wu_shen_2026.yaml"
    wu.write_text(wu.read_text(encoding="utf-8") + "\n# y\n", encoding="utf-8")
    assert validator.source_bundle_hash(list(validator.ITEM_BLOCK_P0_BUNDLE)) != base

    shutil.rmtree(mc / "pa_wu_p0")
    shutil.copytree(P0_DIR, mc / "pa_wu_p0")
    forms = mc / "pa_wu_p0" / "forms.yaml"
    forms.write_text(forms.read_text(encoding="utf-8") + "\n# z\n", encoding="utf-8")
    assert validator.source_bundle_hash(list(validator.ITEM_BLOCK_P0_BUNDLE)) != base


# ==========================================================================
# R1 mock + manifest chain
# ==========================================================================


def test_r1_mock_actually_validated(report, validator) -> None:
    assert report["r1_mock_validator_hash"] == validator.R1_MOCK_HASH


def test_manifest_in_chain(validator) -> None:
    m = validator.check_manifest()
    assert set(m["files"]) == set(validator.REQUIRED_FILES)
    assert m["template_files"] == []


def test_manifest_nested_undeclared_template_rejected(validator, tmp_path, monkeypatch) -> None:
    # copy the package, add an undeclared nested template, expect rejection
    dst = tmp_path / "pkg"
    shutil.copytree(PKG_DIR, dst)
    (dst / "templates").mkdir(exist_ok=True)
    (dst / "templates" / "extra.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    with pytest.raises(validator.PreflightError):
        validator.check_manifest()


# ==========================================================================
# 二、fully tmp-isolated synthetic authorized + repo cleanliness
# ==========================================================================


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
            "decided_at": "2026-07-02",
            "source_references": ["https://acme.example/docs"],
        },
    }


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


def _full_budget() -> dict:
    return {
        "budget_approved": True,
        "currency": "USD",
        "maximum_total_budget": 1000.0,
        "warning_budget_threshold": 800.0,
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


def _write(path, data) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _repo_status(paths) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    ).stdout


def test_end_to_end_synthetic_authorized_fully_isolated(validator, tmp_path, monkeypatch) -> None:
    """Build a COMPLETE measurement_candidates structure in tmp; write frozen
    contracts + controlled templates ONLY in tmp; drive build_preflight_report().
    The real repository must remain untouched."""
    real_templates_rel = "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight/templates"
    status_before = _repo_status([
        "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight",
        real_templates_rel,
    ])

    mc = tmp_path / "measurement_candidates"
    dst = mc / "pa_wu_p1_preflight"
    shutil.copytree(PKG_DIR, dst)
    shutil.copytree(P0_DIR, mc / "pa_wu_p0")
    shutil.copytree(R1_DIR, mc / "pa_wu_r1_mock")

    # controlled template ONLY in tmp
    tmpl_dir = dst / "templates"
    tmpl_dir.mkdir(exist_ok=True)
    (tmpl_dir / "seg.txt").write_text("frozen segment content", encoding="utf-8")

    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)

    seg_hash = _sha_text((tmpl_dir / "seg.txt").read_text(encoding="utf-8"))
    bundle = list(validator.ITEM_BLOCK_P0_BUNDLE)
    bundle_hash = validator.source_bundle_hash(bundle)

    model = _frozen_model(validator)
    _write(dst / "model_selection_decision.yaml", model)

    prompt = _load("prompt_freeze_contract.yaml")
    for name, seg in prompt["segments"].items():
        seg["frozen"] = True
        seg["owner"] = "researcher"
        seg["change_requires_new_run_version"] = True
        seg["content"] = None
        if name == "item_block":
            seg["template_reference"] = None
            seg["source_bundle"] = bundle
            seg["sha256"] = bundle_hash
        else:
            seg["template_reference"] = "pa_wu_p1_preflight/templates/seg.txt"
            seg["sha256"] = seg_hash
    _write(dst / "prompt_freeze_contract.yaml", prompt)

    _write(dst / "sampling_and_repeat_contract.yaml", _full_sampling())
    _write(dst / "budget_and_rate_limit_contract.yaml", _full_budget())
    retry = _load("retry_and_recovery_contract.yaml")
    retry["frozen"] = True
    _write(dst / "retry_and_recovery_contract.yaml", retry)
    logging_c = _load("provenance_and_logging_contract.yaml")
    logging_c["frozen"] = True
    logging_c["privacy_review"] = {"status": "completed", "reviewed_by": "dpo", "reviewed_at": "2026-07-02T12:00"}
    _write(dst / "provenance_and_logging_contract.yaml", logging_c)
    _write(dst / "stop_conditions.yaml", _full_stop())

    env = _load("environment_acceptance.yaml")
    env["preflight_branch_ci"] = {"run_number": 99, "status": "success"}
    _write(dst / "environment_acceptance.yaml", env)

    manifest = _load("preflight_manifest.yaml")
    manifest["template_files"] = ["templates/seg.txt"]
    _write(dst / "preflight_manifest.yaml", manifest)

    auth = _load("authorization_gate.yaml")
    auth["required_gates"] = dict.fromkeys(validator.REQUIRED_GATES, True)
    auth["authorization_status"] = "authorized"
    auth["real_model_execution_authorized"] = True
    auth["authorized_by"] = "pi"
    auth["authorized_at"] = "2026-07-02T13:00"
    _write(dst / "authorization_gate.yaml", auth)

    report = validator.build_preflight_report()
    assert report["preflight_status"] == "authorized"
    assert report["p1_execution_status"] == "authorized"
    assert report["blocking_gates"] == []

    # real repo must be untouched (no templates created/modified in real tree)
    assert not (PKG_DIR / "templates").exists()
    status_after = _repo_status([
        "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight",
        real_templates_rel,
    ])
    assert status_after == status_before


def test_real_templates_sentinel_untouched(validator, tmp_path, monkeypatch) -> None:
    """Even if a real templates dir with a sentinel pre-exists, running an
    isolated e2e must not modify or delete it. We simulate by ensuring the
    validator's file operations only touch tmp (PACKAGE_DIR monkeypatched)."""
    # create a sentinel in tmp-only package; the real tree is never written.
    mc = tmp_path / "measurement_candidates"
    dst = mc / "pa_wu_p1_preflight"
    shutil.copytree(PKG_DIR, dst)
    shutil.copytree(P0_DIR, mc / "pa_wu_p0")
    (dst / "templates").mkdir()
    sentinel = dst / "templates" / "sentinel.txt"
    sentinel.write_text("KEEP", encoding="utf-8")
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    # resolver reads only; sentinel remains
    validator.template_content_hash("pa_wu_p1_preflight/templates/sentinel.txt")
    assert sentinel.read_text(encoding="utf-8") == "KEEP"


def test_package_hash_changes_with_template(validator, tmp_path, monkeypatch) -> None:
    mc = tmp_path / "measurement_candidates"
    dst = mc / "pa_wu_p1_preflight"
    shutil.copytree(PKG_DIR, dst)
    (dst / "templates").mkdir()
    (dst / "templates" / "t.txt").write_text("A", encoding="utf-8")
    m = _load("preflight_manifest.yaml")
    m["template_files"] = ["templates/t.txt"]
    _write(dst / "preflight_manifest.yaml", m)
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    contracts = {n: yaml.safe_load((dst / n).read_text(encoding="utf-8")) for n in validator.CONTRACT_FILES}
    manifest = yaml.safe_load((dst / "preflight_manifest.yaml").read_text(encoding="utf-8"))
    h1 = validator.compute_package_hash(contracts, manifest)
    (dst / "templates" / "t.txt").write_text("B", encoding="utf-8")
    h2 = validator.compute_package_hash(contracts, manifest)
    assert h1 != h2


# ==========================================================================
# 三、environment gate blocked until branch CI success
# ==========================================================================


def test_environment_review_blocked_when_branch_ci_pending() -> None:
    env = _load("environment_acceptance.yaml")
    assert env["preflight_branch_ci"]["status"] == "pending"


def test_environment_review_records_all_failures() -> None:
    env = _load("environment_acceptance.yaml")
    assert env["r1_baseline_ci"]["run_number"] == 71
    win = env["windows_local"]
    assert win["bash_wrapper_failures"] == 5
    assert win["scipy_dll_failures"] == 2
    assert win["scipy_collection_errors"] == 1
    qual = env["windows_failure_qualification"]
    assert qual["is_preflight_code_regression"] is False
    assert qual["is_fixed"] is False


def test_env_reviewed_true_only_with_branch_success(validator) -> None:
    env = _load("environment_acceptance.yaml")
    assert validator._env_reviewed(env) is False
    env2 = copy.deepcopy(env)
    env2["preflight_branch_ci"] = {"run_number": 88, "status": "success"}
    assert validator._env_reviewed(env2) is True


# ==========================================================================
# 四、finite / date / security scan / cross-contract
# ==========================================================================


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, "x"])
def test_finite_rejects_nan_inf_bool(validator, bad) -> None:
    assert validator._finite_number(bad) is False


def test_finite_accepts_real(validator) -> None:
    assert validator._finite_number(0.0) is True
    assert validator._finite_number(3) is True


@pytest.mark.parametrize("good", ["2026-07-02", "2026-07-02T13:00", "2026-07-02T13:00:00"])
def test_date_accepts_iso(validator, good) -> None:
    assert validator._is_date(good) is True


@pytest.mark.parametrize("bad", ["later", "2026/07/02", "", "not-a-date", "07-02-2026"])
def test_date_rejects_non_iso(validator, bad) -> None:
    assert validator._is_date(bad) is False


def test_sampling_nan_temperature_blocks(validator) -> None:
    s = _full_sampling()
    s["temperature"] = float("nan")
    assert validator._sampling_frozen(s) is False


def test_budget_bad_date_blocks(validator) -> None:
    b = _full_budget()
    b["approval_timestamp"] = "sometime"
    assert validator._budget_approved(b, _full_sampling()) is False


# ---- formal AST security scan (production function) ----


def test_scan_rejects_import_requests(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import requests\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_importlib_alias(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import importlib as il\nil.import_module('requests')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_from_importlib_alias(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("from importlib import import_module as im\nim('socket')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_subprocess_list_curl(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("import subprocess\nsubprocess.run(['curl', 'http://x'])\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


@pytest.mark.parametrize("cli", ["wget", "powershell", "pwsh"])
def test_scan_rejects_subprocess_tuple_clis(validator, tmp_path, cli) -> None:
    p = tmp_path / "m.py"
    p.write_text(f"import subprocess\nsubprocess.Popen(({cli!r}, '-x'))\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_scan_rejects_r2_r3_open(validator, tmp_path) -> None:
    p = tmp_path / "m.py"
    p.write_text("open('adaptation_candidates/x.yaml')\n", encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_python_source(p)


def test_secret_scan_not_bypassed_by_marker(validator, tmp_path) -> None:
    p = tmp_path / "m.yaml"
    p.write_text('api_key: "abcdef0123456789"  # preflight-detection-pattern\n', encoding="utf-8")
    with pytest.raises(validator.PreflightError):
        validator.scan_text_secrets(p)


def test_validator_self_scan_clean(validator) -> None:
    validator.check_validator_self_ast()
    validator.check_no_secrets_no_clients_no_network()


# ---- cross-contract consistency ----


def _consistent_contracts(validator) -> dict:
    c = _all_contracts(validator)
    c["model_selection_decision.yaml"] = _frozen_model(validator)
    c["sampling_and_repeat_contract.yaml"] = _full_sampling()
    c["budget_and_rate_limit_contract.yaml"] = _full_budget()
    return c


def test_cross_contract_consistent_ok(validator) -> None:
    assert validator._cross_contract_consistent(_consistent_contracts(validator)) is True


def test_cross_contract_seed_support_mismatch(validator) -> None:
    c = _consistent_contracts(validator)
    c["model_selection_decision.yaml"]["decision"]["deterministic_seed_support"] = True
    # sampling.seed_supported is False -> mismatch
    assert validator._cross_contract_consistent(c) is False


def test_cross_contract_pricing_mismatch(validator) -> None:
    c = _consistent_contracts(validator)
    c["budget_and_rate_limit_contract.yaml"]["pricing"]["snapshot_date"] = "2099-01-01"
    assert validator._cross_contract_consistent(c) is False


def test_cross_contract_structured_output_required(validator) -> None:
    c = _consistent_contracts(validator)
    c["model_selection_decision.yaml"]["decision"]["structured_output_support"] = False
    assert validator._cross_contract_consistent(c) is False


def test_source_reference_placeholder_rejected(validator) -> None:
    model = _frozen_model(validator)
    model["decision"]["source_references"] = ["placeholder"]
    assert validator._model_frozen(model) is False
