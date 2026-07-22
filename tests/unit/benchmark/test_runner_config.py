"""Contract-driven runner tests (FAST-001.1 §2).

Verify that the task/model config YAMLs really drive the run: they are loaded,
validated against the implemented task pack, and become the recorded
task_spec.json / model_spec.json and their hashes. No silent fallback.
"""

from __future__ import annotations

import json

import pytest
import yaml

from freewill_attribution import cli, runner
from freewill_attribution.benchmark import registry
from freewill_attribution.benchmark.hashing import hash_object
from freewill_attribution.tasks.freewill_attribution import spec


def _default_task_dict():
    return yaml.safe_load(registry.TASK_DEFAULT_YAML.read_text(encoding="utf-8"))


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def test_cli_passes_task_and_model_config(tmp_path):
    rc = cli.main(
        ["benchmark-run", "--mock", "--artifact-root", str(tmp_path),
         "--n-per-cell", "1", "--seed", "20260425", "--fresh"]
    )
    assert rc == 0
    run_dir = tmp_path / "runs" / "attribution-behavior-n1-seed20260425"
    resolved = json.loads((run_dir / "resolved_config.json").read_text(encoding="utf-8"))
    assert resolved["task_config_ref"].endswith("attribution_behavior.yaml")
    assert resolved["model_config_ref"].endswith("model.mock.yaml")
    assert resolved["provider"] == "mock"
    assert resolved["model_id"] == "rule-based-v2"
    assert resolved["task_id"] == "attribution-behavior"


def test_cli_task_config_flag_is_accepted(tmp_path):
    rc = cli.main(
        ["benchmark-run", "--mock", "--artifact-root", str(tmp_path),
         "--task-config", str(registry.TASK_DEFAULT_YAML),
         "--n-per-cell", "1", "--seed", "20260425", "--fresh"]
    )
    assert rc == 0


def test_cli_task_alias_is_rejected(tmp_path):
    # The misleading --task alias was removed; argparse must reject it.
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["benchmark-run", "--mock", "--artifact-root", str(tmp_path),
             "--task", str(registry.TASK_DEFAULT_YAML)]
        )


def test_cli_help_distinguishes_run_taskspec_from_material_contract(capsys):
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["benchmark-run", "--help"])
    out = capsys.readouterr().out
    assert "--task-config" in out
    # help text must not advertise the removed alias
    assert "--task " not in out
    assert "material task contract" in out


def test_runner_uses_taskspec_yaml(tmp_path):
    result = runner.run_benchmark(seed=20260425, n_per_cell=1, artifact_root=tmp_path, fresh=True)
    # task_spec_hash must be the hash of the ACTUAL validated TaskSpec dump,
    # not a throwaway _task_spec_payload() object.
    expected = hash_object(registry.load_default_task_spec().model_dump(mode="json"))
    assert result.manifest.task_spec_hash == expected
    on_disk = json.loads((result.run_dir / "task_spec.json").read_text(encoding="utf-8"))
    assert on_disk["task_id"] == "attribution-behavior"
    assert on_disk["task_version"] == "1.0-mock"
    # model_spec.json / model_spec_hash come from the actual model config.
    model_expected = hash_object(registry.load_model_spec().model_dump(mode="json"))
    assert result.manifest.model_spec_hash == model_expected


def test_runner_rejects_non_executable_task(tmp_path):
    data = _default_task_dict()
    data["executable"] = False
    cfg = _write_yaml(tmp_path / "task_nonexec.yaml", data)
    with pytest.raises(runner.RunConfigError):
        runner.run_benchmark(
            seed=20260425, n_per_cell=1, artifact_root=tmp_path / "run",
            task_config=cfg, fresh=True,
        )


def test_runner_rejects_unsupported_provider(tmp_path):
    class _FakeProvider:
        provider_name = "openai"
        model_id = "gpt"

        def generate(self, request):  # pragma: no cover - must never be called
            raise AssertionError("provider must be rejected before generate()")

    with pytest.raises(runner.RunConfigError):
        runner.run_benchmark(
            seed=20260425, n_per_cell=1, artifact_root=tmp_path,
            provider=_FakeProvider(), fresh=True,
        )


def test_taskspec_hash_changes_when_config_changes(tmp_path):
    base = runner.run_benchmark(
        seed=20260425, n_per_cell=1, artifact_root=tmp_path / "base", fresh=True
    )
    data = _default_task_dict()
    # Change a NON-validated field so the spec still passes consistency checks
    # but its canonical serialization (and hash) differs.
    data["evidence_boundary"] = data["evidence_boundary"] + " [variant marker]"
    cfg = _write_yaml(tmp_path / "task_variant.yaml", data)
    variant = runner.run_benchmark(
        seed=20260425, n_per_cell=1, artifact_root=tmp_path / "variant",
        task_config=cfg, fresh=True,
    )
    assert base.manifest.task_spec_hash != variant.manifest.task_spec_hash


def test_python_task_pack_matches_taskspec():
    # The neutral default TaskSpec must agree with the Python task pack.
    problems = spec.taskspec_consistency_problems(registry.load_default_task_spec())
    assert problems == [], problems
