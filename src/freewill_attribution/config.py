"""Read-only configuration loading (FND-006).

This module only loads and validates declarative YAML configuration into the
schemas defined in :mod:`freewill_attribution.schemas`. It deliberately does
NOT: modify environment variables, read ``.env`` files, read API keys, create
directories, write a resolved config, merge command-line arguments, execute a
study, import the runner or CLI, or make provider calls.

Not implemented this round (out of scope): multi-layer config merge,
environment-variable substitution, CLI overrides, secret interpolation,
include/import, profile inheritance, remote URLs, and resolved-config writing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from .schemas import ModelConfig, PromptConfig, StudyConfig, ConfigBundle


class ConfigLoadError(RuntimeError):
    """Raised when a configuration file cannot be loaded or validated."""


def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    """Load a YAML file that must contain a top-level mapping.

    Empty YAML returns an empty dict. Malformed YAML is wrapped in
    :class:`ConfigLoadError`. Error messages include the file path but never the
    full file body. This function never returns ``None``.
    """
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise ConfigLoadError(f"Config file does not exist: {resolved}")
    if not resolved.is_file():
        raise ConfigLoadError(f"Config path is not a file: {resolved}")

    try:
        with resolved.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Malformed YAML in config file: {resolved}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Config file top-level must be a mapping, got "
            f"{type(data).__name__}: {resolved}"
        )
    return data


def _summarize_validation_error(exc: PydanticValidationError) -> str:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        parts.append(f"{loc or '<root>'}: {err.get('msg', 'invalid')}")
    return "; ".join(parts)


def load_study_config(path: str | Path) -> StudyConfig:
    resolved = Path(path).expanduser().resolve()
    data = load_yaml_mapping(resolved)
    try:
        return StudyConfig.model_validate(data)
    except PydanticValidationError as exc:
        raise ConfigLoadError(
            f"Invalid study config: {resolved} ({_summarize_validation_error(exc)})"
        ) from exc


def load_model_config(path: str | Path) -> ModelConfig:
    resolved = Path(path).expanduser().resolve()
    data = load_yaml_mapping(resolved)
    try:
        return ModelConfig.model_validate(data)
    except PydanticValidationError as exc:
        raise ConfigLoadError(
            f"Invalid model config: {resolved} ({_summarize_validation_error(exc)})"
        ) from exc


def load_prompt_config(path: str | Path) -> PromptConfig:
    resolved = Path(path).expanduser().resolve()
    data = load_yaml_mapping(resolved)
    try:
        return PromptConfig.model_validate(data)
    except PydanticValidationError as exc:
        raise ConfigLoadError(
            f"Invalid prompt config: {resolved} ({_summarize_validation_error(exc)})"
        ) from exc


def _resolve_config_ref(base_dir: Path, ref: str) -> Path:
    """Safely resolve a relative config reference inside ``base_dir``.

    The reference must be relative (absolute paths are rejected) and must not
    escape ``base_dir`` via ``..``. No file or directory is created.
    """
    ref_path = Path(ref)
    if ref_path.is_absolute() or ref_path.drive or ref_path.root:
        raise ConfigLoadError(
            f"Config reference must be a relative path, got: {ref}"
        )

    base = Path(base_dir).resolve()
    candidate = (base / ref_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise ConfigLoadError(
            f"Config reference escapes its base directory: {ref}"
        ) from None
    return candidate


def load_config_bundle(study_config_path: str | Path) -> ConfigBundle:
    """Load a study config plus its referenced model and prompt configs.

    References are resolved relative to the study config's own directory using
    :func:`_resolve_config_ref`. File paths are not written back into any model
    extra field.
    """
    study_path = Path(study_config_path).expanduser().resolve()
    study = load_study_config(study_path)

    base_dir = study_path.parent
    model_path = _resolve_config_ref(base_dir, study.model_config_ref)
    prompt_path = _resolve_config_ref(base_dir, study.prompt_config_ref)

    model = load_model_config(model_path)
    prompt = load_prompt_config(prompt_path)

    return ConfigBundle(study=study, model=model, prompt=prompt)


__all__ = [
    "ConfigLoadError",
    "load_yaml_mapping",
    "load_study_config",
    "load_model_config",
    "load_prompt_config",
    "load_config_bundle",
]
