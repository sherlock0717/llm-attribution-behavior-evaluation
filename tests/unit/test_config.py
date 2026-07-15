"""Unit tests for read-only configuration loading (FND-006)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from freewill_attribution.config import (
    ConfigLoadError,
    load_config_bundle,
    load_model_config,
    load_prompt_config,
    load_study_config,
    load_yaml_mapping,
)
from freewill_attribution.schemas import ModelConfig, PromptConfig, StudyConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS = REPO_ROOT / "configs"
STUDY_DEFAULT = CONFIGS / "study.default.yaml"


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


STUDY_TEMPLATE = """\
study_id: demo
design:
  process_conditions:
    - a
    - b
  identity_labels:
    - x
    - y
  n_per_cell: 5
  seed: 1
stimuli_version: v1
scales_version: v1
prompt_config_ref: {prompt_ref}
model_config_ref: {model_ref}
output_dir: null
budget:
  max_calls: 10
  max_cost_usd: null
"""

MODEL_YAML = """\
provider: mock
model: rule-based-v1
temperature: 1.0
max_tokens: 100
response_format: json_object
"""

PROMPT_YAML = """\
prompt_id: p1
version: v1
expose_construct_names: false
items_batching: all
system_template: s
user_template: u
"""


# 1-7 load_yaml_mapping --------------------------------------------------


def test_load_yaml_mapping_reads_mapping(tmp_path):
    path = _write(tmp_path / "m.yaml", "a: 1\nb: two\n")
    assert load_yaml_mapping(path) == {"a": 1, "b": "two"}


def test_empty_yaml_returns_empty_dict(tmp_path):
    path = _write(tmp_path / "empty.yaml", "")
    assert load_yaml_mapping(path) == {}


def test_top_level_list_is_rejected(tmp_path):
    path = _write(tmp_path / "list.yaml", "- 1\n- 2\n")
    with pytest.raises(ConfigLoadError):
        load_yaml_mapping(path)


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(ConfigLoadError):
        load_yaml_mapping(tmp_path / "nope.yaml")


def test_directory_path_is_rejected(tmp_path):
    with pytest.raises(ConfigLoadError):
        load_yaml_mapping(tmp_path)


def test_malformed_yaml_is_wrapped(tmp_path):
    path = _write(tmp_path / "bad.yaml", "a: [1, 2\nb: :\n")
    with pytest.raises(ConfigLoadError):
        load_yaml_mapping(path)


def test_error_contains_path_but_not_full_body(tmp_path):
    secret = "TOP_SECRET_BODY_LINE_SHOULD_NOT_LEAK"
    path = _write(tmp_path / "bad.yaml", f"a: [1, 2\n{secret}: :\n")
    with pytest.raises(ConfigLoadError) as excinfo:
        load_yaml_mapping(path)
    message = str(excinfo.value)
    assert "bad.yaml" in message
    assert secret not in message


# 8-10 typed loaders -----------------------------------------------------


def test_load_study_config_returns_study(tmp_path):
    _write(tmp_path / "model.mock.yaml", MODEL_YAML)
    _write(tmp_path / "prompt.v1.yaml", PROMPT_YAML)
    study_path = _write(
        tmp_path / "study.yaml",
        STUDY_TEMPLATE.format(prompt_ref="prompt.v1.yaml", model_ref="model.mock.yaml"),
    )
    study = load_study_config(study_path)
    assert isinstance(study, StudyConfig)
    assert study.design.n_per_cell == 5


def test_load_model_config_returns_model(tmp_path):
    path = _write(tmp_path / "model.yaml", MODEL_YAML)
    model = load_model_config(path)
    assert isinstance(model, ModelConfig)
    assert model.provider == "mock"


def test_load_prompt_config_returns_prompt(tmp_path):
    path = _write(tmp_path / "prompt.yaml", PROMPT_YAML)
    prompt = load_prompt_config(path)
    assert isinstance(prompt, PromptConfig)
    assert prompt.version == "v1"


# 11-15 bundle + repo configs -------------------------------------------


def test_load_config_bundle_from_repo_default():
    bundle = load_config_bundle(STUDY_DEFAULT)
    assert bundle.study.study_id == "freewill-attribution-v1"


def test_bundle_n_per_cell_is_twenty():
    bundle = load_config_bundle(STUDY_DEFAULT)
    assert bundle.study.design.n_per_cell == 20


def test_bundle_model_provider_is_mock():
    bundle = load_config_bundle(STUDY_DEFAULT)
    assert bundle.model.provider == "mock"


def test_bundle_prompt_expose_construct_names_is_true():
    bundle = load_config_bundle(STUDY_DEFAULT)
    assert bundle.prompt.expose_construct_names is True


def test_unknown_extra_field_preserved(tmp_path):
    text = MODEL_YAML + "future_field: keep-me\n"
    path = _write(tmp_path / "model.yaml", text)
    model = load_model_config(path)
    assert model.model_dump()["future_field"] == "keep-me"


# 16-18 reference safety -------------------------------------------------


def test_absolute_model_ref_is_rejected(tmp_path):
    _write(tmp_path / "prompt.v1.yaml", PROMPT_YAML)
    abs_ref = (tmp_path / "model.mock.yaml").resolve()
    _write(abs_ref, MODEL_YAML)
    study_path = _write(
        tmp_path / "study.yaml",
        STUDY_TEMPLATE.format(prompt_ref="prompt.v1.yaml", model_ref=str(abs_ref)),
    )
    with pytest.raises(ConfigLoadError):
        load_config_bundle(study_path)


def test_parent_escape_ref_is_rejected(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    _write(tmp_path / "outside.yaml", MODEL_YAML)
    _write(base / "prompt.v1.yaml", PROMPT_YAML)
    study_path = _write(
        base / "study.yaml",
        STUDY_TEMPLATE.format(prompt_ref="prompt.v1.yaml", model_ref="../outside.yaml"),
    )
    with pytest.raises(ConfigLoadError):
        load_config_bundle(study_path)


def test_missing_referenced_file_is_rejected(tmp_path):
    _write(tmp_path / "prompt.v1.yaml", PROMPT_YAML)
    study_path = _write(
        tmp_path / "study.yaml",
        STUDY_TEMPLATE.format(prompt_ref="prompt.v1.yaml", model_ref="model.missing.yaml"),
    )
    with pytest.raises(ConfigLoadError):
        load_config_bundle(study_path)


# 19-21 side effects / cwd / secrets ------------------------------------


def test_import_creates_no_files_or_dirs(tmp_path):
    work = tmp_path / "cwd"
    work.mkdir()
    result = subprocess.run(
        [sys.executable, "-c", "import freewill_attribution.config"],
        cwd=str(work),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(work.iterdir()) == []


def test_load_from_outside_cwd_with_absolute_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bundle = load_config_bundle(STUDY_DEFAULT.resolve())
    assert bundle.model.provider == "mock"


def test_loading_does_not_read_deepseek_api_key(monkeypatch):
    sentinel = "unused-sentinel-value"
    monkeypatch.setenv("DEEPSEEK_API_KEY", sentinel)
    bundle = load_config_bundle(STUDY_DEFAULT)
    # The value must never surface in the loaded configuration output.
    assert sentinel not in bundle.model.model_dump_json()
    assert sentinel not in bundle.study.model_dump_json()
