"""Integration tests for the mock benchmark vertical slice (FAST-001).

These tests run the full lifecycle (TaskSpec -> Stimulus -> Prompt -> Provider ->
Raw -> Parser -> Validation -> Repair -> Score -> Aggregate -> Manifest) against
the deterministic mock provider. They write only to tmp_path artifact roots and
never touch the historical outputs/ directory or call any API.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from freewill_attribution import runner
from freewill_attribution.benchmark import artifacts as artifact_io

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_OUTPUTS = REPO_ROOT / "outputs"


def _outputs_manifest():
    manifest = {}
    if not REPO_OUTPUTS.exists():
        return manifest
    for p in REPO_OUTPUTS.rglob("*"):
        if p.is_file():
            rel = p.relative_to(REPO_OUTPUTS).as_posix()
            data = p.read_bytes()
            manifest[rel] = (len(data), hashlib.sha256(data).hexdigest())
    return manifest


def test_smoke_run_12_records(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    m = result.manifest
    assert m.status.value == "completed"
    assert m.planned_records == 12
    assert m.completed_records == 12
    assert m.failed_records == 0
    raw = artifact_io.read_jsonl(result.run_dir / "raw_responses.jsonl")
    assert len(raw) == 12
    norm = artifact_io.read_jsonl(result.run_dir / "normalized_responses.jsonl")
    assert len(norm) == 12


def test_acceptance_run_24_records_cells_complete(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=2, artifact_root=tmp_path, fresh=True)
    m = result.manifest
    assert m.planned_records == 24
    assert m.completed_records == 24
    norm = artifact_io.read_jsonl(result.run_dir / "normalized_responses.jsonl")
    cells = {}
    for row in norm:
        cells.setdefault((row["condition"], row["identity"]), 0)
        cells[(row["condition"], row["identity"])] += 1
    assert len(cells) == 12
    assert set(cells.values()) == {2}


def test_manifest_hashes_present_and_artifacts_verify(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    m = result.manifest
    for hash_field in (
        m.resolved_config_hash,
        m.task_spec_hash,
        m.model_spec_hash,
        m.prompt_template_hash,
        m.prompt_snapshot_set_hash,
        m.stimulus_set_hash,
        m.scoring_spec_hash,
    ):
        assert isinstance(hash_field, str) and len(hash_field) == 64
    # Manifest artifacts re-verify against files on disk.
    assert artifact_io.verify_artifacts(m.artifacts, result.run_dir) == []


def test_same_seed_hash_stable_across_reruns(tmp_path):
    r1 = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path / "a", fresh=True)
    r2 = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path / "b", fresh=True)
    # Content hashes for deterministic artifacts must match.
    assert r1.manifest.stimulus_set_hash == r2.manifest.stimulus_set_hash
    assert r1.manifest.prompt_template_hash == r2.manifest.prompt_template_hash
    assert r1.manifest.prompt_snapshot_set_hash == r2.manifest.prompt_snapshot_set_hash

    def _sha(run_dir, name):
        return hashlib.sha256((run_dir / name).read_bytes()).hexdigest()

    for name in ("raw_responses.jsonl", "normalized_responses.jsonl", "scores.jsonl"):
        assert _sha(r1.run_dir, name) == _sha(r2.run_dir, name), name


def test_resume_does_not_duplicate_records(tmp_path):
    first = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    assert first.manifest.completed_records == 12
    second = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, resume=True)
    norm = artifact_io.read_jsonl(second.run_dir / "normalized_responses.jsonl")
    ids = [r["record_id"] for r in norm]
    assert len(ids) == len(set(ids)) == 12
    assert second.manifest.completed_records == 12


def test_repair_path_recovers_and_records_lineage(tmp_path):
    # Force a malformed first attempt for one record; repair (attempt 2) recovers.
    design = __import__(
        "freewill_attribution.tasks.freewill_attribution.stimuli",
        fromlist=["build_design"],
    ).build_design(1, 20260425)
    target = design[0]["record_id"]
    result = runner.run_benchmark(
        seed=20260425,
        n_per_cell=1,
        artifact_root=tmp_path,
        fresh=True,
        max_repair_attempts=1,
        fault_map={target: "malformed_json"},
    )
    m = result.manifest
    assert m.completed_records == 12  # repaired successfully
    assert m.status.value == "completed"
    oq = result.aggregate_report.output_quality
    assert oq["first_attempt_parse_success_rate"] < 1.0
    assert oq["final_parse_success_rate"] == 1.0
    assert oq["repair_trigger_rate"] > 0.0
    assert oq["repair_success_rate"] == 1.0
    # Repair attempt references its parent first attempt.
    raw = artifact_io.read_jsonl(result.run_dir / "raw_responses.jsonl")
    repaired = [r for r in raw if r["record_id"] == target and r["attempt"] == 2]
    assert repaired and repaired[0]["parent_attempt_id"] is not None


def test_repair_exhausted_is_recorded_as_failure(tmp_path):
    design = __import__(
        "freewill_attribution.tasks.freewill_attribution.stimuli",
        fromlist=["build_design"],
    ).build_design(1, 20260425)
    target = design[0]["record_id"]
    result = runner.run_benchmark(
        seed=20260425,
        n_per_cell=1,
        artifact_root=tmp_path,
        fresh=True,
        max_repair_attempts=0,  # no repair allowed -> failure recorded
        fault_map={target: "empty"},
    )
    m = result.manifest
    assert m.failed_records == 1
    assert m.status.value == "partial"
    failures = artifact_io.read_jsonl(result.run_dir / "failures.jsonl")
    assert any(f["record_id"] == target for f in failures)


def test_outputs_unchanged_by_benchmark_run(tmp_path):
    before = _outputs_manifest()
    runner.run_benchmark(seed=20260425, n_per_cell=2, artifact_root=tmp_path, fresh=True)
    assert _outputs_manifest() == before


# --- FAST-001.1: manifest provenance + portable paths ----------------------

def test_manifest_git_commit_is_populated(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    gc = result.manifest.git_commit
    assert gc, "git_commit must be populated (a SHA or 'unknown'), never null"
    assert gc == "unknown" or len(gc) == 40


def test_artifact_paths_are_relative(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    for ref in result.manifest.artifacts:
        p = Path(ref.path)
        assert not p.is_absolute(), ref.path
        assert not p.drive, ref.path
        assert ".." not in p.parts, ref.path
    # And they all re-resolve strictly within the run dir.
    assert artifact_io.verify_artifacts(result.manifest.artifacts, result.run_dir) == []


def test_artifact_ref_rejects_absolute_path(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    abs_path = (result.run_dir / "resolved_config.json").resolve()
    bad = result.manifest.artifacts[0].model_copy(update={"path": str(abs_path)})
    problems = artifact_io.verify_artifacts([bad], result.run_dir)
    assert problems and "absolute" in problems[0]


def test_artifact_ref_rejects_parent_escape(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    bad = result.manifest.artifacts[0].model_copy(update={"path": "../escape.json"})
    problems = artifact_io.verify_artifacts([bad], result.run_dir)
    assert problems and ".." in problems[0]


def test_manifest_contains_no_local_user_path(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    blob = json.dumps(result.manifest.model_dump(mode="json"))
    for banned in ("C:/Users", "C:\\\\Users", "/home/", "/Users/", str(tmp_path)):
        assert banned not in blob, banned


def test_manifest_self_hash_strategy_is_explicit(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    # manifest.json is excluded from its own artifact list.
    roles = {a.role for a in result.manifest.artifacts}
    assert "manifest" not in roles
    paths = {a.path for a in result.manifest.artifacts}
    assert "manifest.json" not in paths
    assert "excluded from its own artifact list" in result.manifest.integrity_note
    # A separate manifest.sha256 records its digest (no self-cycle).
    sha_file = result.run_dir / "manifest.sha256"
    assert sha_file.is_file()
    recorded = sha_file.read_text(encoding="utf-8").strip()
    actual = hashlib.sha256((result.run_dir / "manifest.json").read_bytes()).hexdigest()
    assert recorded == actual


# --- FAST-001.1: run lifecycle / overwrite ---------------------------------

def test_existing_run_requires_fresh_or_resume(tmp_path):
    runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    # Second run into the same run dir with NEITHER flag must refuse.
    with pytest.raises(runner.RunConfigError):
        runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path)


def test_fresh_removes_stale_artifacts(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    stale = result.run_dir / "figures" / "stale_leftover.txt"
    stale.write_text("stale", encoding="utf-8")
    stray = result.run_dir / "orphan.jsonl"
    stray.write_text("{}\n", encoding="utf-8")
    result2 = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    assert not stale.exists()
    assert not stray.exists()
    assert result2.manifest.completed_records == 12


def test_resume_preserves_all_attempt_records(tmp_path):
    design = __import__(
        "freewill_attribution.tasks.freewill_attribution.stimuli",
        fromlist=["build_design"],
    ).build_design(1, 20260425)
    target = design[0]["record_id"]
    first = runner.run_benchmark(
        seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True,
        max_repair_attempts=1, fault_map={target: "malformed_json"},
    )
    before = artifact_io.read_jsonl(first.run_dir / "response_records.jsonl")
    before_target = [r for r in before if r["record_id"] == target]
    assert len(before_target) == 2  # first attempt + repair preserved
    second = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, resume=True)
    after = artifact_io.read_jsonl(second.run_dir / "response_records.jsonl")
    after_target = [r for r in after if r["record_id"] == target]
    # Both attempts (incl. the failed first attempt lineage) are preserved.
    assert len(after_target) == 2
    assert {r["attempt"] for r in after_target} == {1, 2}
    assert any(r.get("parent_attempt_id") for r in after_target)


def test_noop_resume_preserves_metrics(tmp_path):
    first = runner.run_benchmark(seed=20260425, n_per_cell=2, artifact_root=tmp_path, fresh=True)
    second = runner.run_benchmark(seed=20260425, n_per_cell=2, artifact_root=tmp_path, resume=True)
    m1, m2 = first.manifest, second.manifest
    for field in ("completed_records", "failed_records", "retry_count",
                  "parse_failure_count", "schema_failure_count"):
        assert getattr(m1, field) == getattr(m2, field), field
    oq1 = first.aggregate_report.output_quality
    oq2 = second.aggregate_report.output_quality
    for key in ("first_attempt_parse_success_rate", "final_parse_success_rate",
                "first_attempt_schema_compliance_rate", "final_schema_compliance_rate",
                "repair_trigger_rate", "repair_success_rate"):
        assert oq1[key] == oq2[key], key


def test_provider_exception_writes_partial_manifest(tmp_path):
    design = __import__(
        "freewill_attribution.tasks.freewill_attribution.stimuli",
        fromlist=["build_design"],
    ).build_design(1, 20260425)
    target = design[0]["record_id"]
    result = runner.run_benchmark(
        seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True,
        fault_map={target: "provider_error"},
    )
    m = result.manifest
    assert m.status.value == "partial"
    assert m.failed_records == 1
    assert m.completed_records == 11
    failures = artifact_io.read_jsonl(result.run_dir / "failures.jsonl")
    assert any(f["record_id"] == target and f["stage"] == "provider" for f in failures)
    # a manifest DID get written despite the provider exception
    assert (result.run_dir / "manifest.json").is_file()


def test_no_api_key_in_manifest(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    dumped = result.manifest.model_dump(mode="json")
    # Artifact paths embed tmp dir names, so scan the manifest with artifact
    # path strings removed; check for credential-shaped keys and values.
    dumped_no_paths = dict(dumped)
    dumped_no_paths["artifacts"] = [
        {k: v for k, v in a.items() if k != "path"} for a in dumped.get("artifacts", [])
    ]
    blob = json.dumps(dumped_no_paths)
    for banned in ('"api_key"', '"authorization"', '"access_token"', "sk-", "DEEPSEEK_API_KEY"):
        assert banned not in blob
    # No manifest model field is credential-shaped.
    from freewill_attribution.benchmark.models import RunManifest

    for field in RunManifest.model_fields:
        assert field not in ("api_key", "authorization", "access_token")
