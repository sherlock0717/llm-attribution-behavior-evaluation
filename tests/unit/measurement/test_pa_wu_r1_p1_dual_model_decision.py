"""Static tests for the PA-Wu R1 P1 dual-model selection decision package.

NO real model, NO network, NO API key, NO model output, NO ranking, NO effect
evaluation. These tests exercise the offline validator: exact dual-model
selection, co-primary roles, official evidence domain legality, unresolved-field
discipline, parameter compatibility legality, migration-plan-only, deterministic
package hash, and non-interference with the existing preflight package.
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
PKG_DIR = MC_DIR / "pa_wu_r1_p1_decision_fill" / "dual_model_selection"
PREFLIGHT_DIR = MC_DIR / "pa_wu_p1_preflight"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PKG_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator():
    return _load_module("pa_wu_dual_model_validate", "validate_dual_model_decision.py")


@pytest.fixture(scope="module")
def report(validator):
    return validator.build_report()


def _load(name: str) -> dict:
    with (PKG_DIR / name).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _write(path, data) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _isolated_pkg(validator, tmp_path, monkeypatch):
    dst = tmp_path / "dual_model_selection"
    shutil.copytree(PKG_DIR, dst)
    monkeypatch.setattr(validator, "PACKAGE_DIR", dst)
    return dst


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
# Happy path
# ==========================================================================


def test_report_ok(report) -> None:
    assert report["selection_status"] == "human_selected"
    assert report["selected_models"] == ["deepseek-v4-pro", "gpt-5.6-terra"]
    assert report["role_policy"] == "co_primary"
    assert report["empirical_evaluation_status"] == "not_evaluated"
    assert report["migration_status"] == "proposed_not_implemented"
    assert report["operational_readiness"] == "incomplete"
    assert set(report["documented_fields_by_model"]) == {"deepseek-v4-pro", "gpt-5.6-terra"}
    assert set(report["unresolved_fields_by_model"]) == {"deepseek-v4-pro", "gpt-5.6-terra"}
    for mid in ("deepseek-v4-pro", "gpt-5.6-terra"):
        assert report["unresolved_fields_by_model"][mid]  # non-empty


# ==========================================================================
# Decision-level failures
# ==========================================================================


def test_missing_one_model_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"] = d["selected_models"][:1]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_extra_model_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"].append({"provider": "anthropic", "model_id": "claude-x", "role": "co_primary"})
    d["selection_scope"]["model_count"] = 3
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_wrong_model_id_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"][0]["model_id"] = "deepseek-v3"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_role_not_co_primary_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selected_models"][0]["role"] = "primary"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_selection_status_unresolved_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["selection_status"] = "unresolved"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_empirical_evaluated_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["empirical_evaluation"]["status"] = "evaluated"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_comparative_quality_true_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["empirical_evaluation"]["comparative_quality_evaluated"] = True
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_ranking_supported_true_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["empirical_evaluation"]["ranking_supported"] = True
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


def test_operational_readiness_ready_fails(validator) -> None:
    d = _load("dual_model_decision.yaml")
    d["operational_readiness"]["status"] = "ready"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_decision(d)


# ==========================================================================
# Package-wide hygiene (ranking vocabulary / placeholders)
# ==========================================================================


def test_winner_field_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    (dst / "comparability_boundaries.yaml").write_text(
        (dst / "comparability_boundaries.yaml").read_text(encoding="utf-8")
        + "\nwinner: gpt-5.6-terra\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_no_placeholders_no_ranking()


def test_effect_ranking_text_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    (dst / "comparability_boundaries.yaml").write_text(
        (dst / "comparability_boundaries.yaml").read_text(encoding="utf-8")
        + "\nnote2: gpt-5.6-terra outperforms deepseek-v4-pro on accuracy\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_no_placeholders_no_ranking()


def test_placeholder_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    (dst / "parameter_compatibility.yaml").write_text(
        (dst / "parameter_compatibility.yaml").read_text(encoding="utf-8")
        + "\nfoo: TBD\n",
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_no_placeholders_no_ranking()


# ==========================================================================
# Evidence-level failures
# ==========================================================================


def test_illegal_domain_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    ev["sources"][0]["canonical_url"] = "https://random-blog.example/deepseek"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_documented_without_source_id_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    ev["models"][0]["official_source_ids"] = []
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


def test_unresolved_field_not_declared_fails(validator) -> None:
    ev = _load("official_evidence.yaml")
    # remove a null field from unresolved_fields while it stays null
    m = ev["models"][0]
    m["unresolved_fields"] = [f for f in m["unresolved_fields"] if f != "context_window"]
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_evidence(ev)


# ==========================================================================
# Parameter compatibility / migration failures
# ==========================================================================


def test_illegal_semantic_status_fails(validator) -> None:
    compat = _load("parameter_compatibility.yaml")
    compat["mappings"][0]["semantic_equivalence_status"] = "identical"
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_parameter_compatibility(compat)


def test_migration_marked_implemented_fails(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    plan = dst / "preflight_schema_migration_plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8").replace(
            "migration_status: proposed_not_implemented",
            "migration_status: implemented",
        ),
        encoding="utf-8",
    )
    with pytest.raises(validator.DualModelDecisionError):
        validator.check_migration_plan()


# ==========================================================================
# Package hash determinism + sensitivity
# ==========================================================================


def test_package_hash_deterministic(validator) -> None:
    assert validator.compute_package_hash() == validator.compute_package_hash()


def test_package_hash_changes_on_evidence(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    h1 = validator.compute_package_hash()
    ev = dst / "official_evidence.yaml"
    ev.write_text(ev.read_text(encoding="utf-8") + "\n# tweak\n", encoding="utf-8")
    assert validator.compute_package_hash() != h1


def test_package_hash_changes_on_compat(validator, tmp_path, monkeypatch) -> None:
    dst = _isolated_pkg(validator, tmp_path, monkeypatch)
    h1 = validator.compute_package_hash()
    cp = dst / "parameter_compatibility.yaml"
    cp.write_text(cp.read_text(encoding="utf-8") + "\n# tweak\n", encoding="utf-8")
    assert validator.compute_package_hash() != h1


# ==========================================================================
# Isolation: preflight untouched + validator does not read authorization
# ==========================================================================


def _repo_status(paths) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    ).stdout


def test_preflight_dir_untouched(validator) -> None:
    rel = "tasks/attribution_behavior/measurement_candidates/pa_wu_p1_preflight"
    snap_before = _dir_snapshot(PREFLIGHT_DIR)
    status_before = _repo_status([rel])
    validator.build_report()
    assert _dir_snapshot(PREFLIGHT_DIR) == snap_before
    assert _repo_status([rel]) == status_before


def test_validator_does_not_read_authorization(validator) -> None:
    # The guard itself asserts no file access to the preflight authorization
    # gate in the validator source (no ".yaml" access, no preflight path).
    validator.check_no_authorization_access()
    src = (PKG_DIR / "validate_dual_model_decision.py").read_text(encoding="utf-8")
    auth_yaml = "authorization" + "_gate.yaml"
    assert auth_yaml not in src
    assert "pa_wu_p1_preflight" not in src


def test_no_legacy_selected_model_singular() -> None:
    text = (PKG_DIR / "dual_model_decision.yaml").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        assert not stripped.startswith("selected_model:")
