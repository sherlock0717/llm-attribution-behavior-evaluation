"""Tests for the shared output-path safety module (FND-004).

These tests pin the safety contract for resolve_output_dir()/resolve_input_dir():
explicit paths only, protected repository directories rejected, and no
directory creation at import time.
"""

from __future__ import annotations

import pytest

import path_safety
from path_safety import (
    LEGACY_OUTPUT_DIR,
    PROJECT_ROOT,
    InputPathError,
    UnsafeOutputPathError,
    resolve_input_dir,
    resolve_output_dir,
)


def test_safe_temp_directory_is_accepted_and_created(tmp_path):
    target = tmp_path / "run"
    resolved = resolve_output_dir(target)
    assert resolved == target.resolve()
    assert resolved.is_dir()


def test_missing_output_path_is_rejected():
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(None)
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir("   ")


def test_repository_root_is_rejected():
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(PROJECT_ROOT)


def test_historical_outputs_directory_is_rejected():
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(LEGACY_OUTPUT_DIR)


def test_outputs_subdirectory_is_rejected():
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(LEGACY_OUTPUT_DIR / "plots")


@pytest.mark.parametrize("name", ["src", "docs", "tests", ".git", ".venv"])
def test_repository_internal_directories_are_rejected(name):
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(PROJECT_ROOT / name)
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(PROJECT_ROOT / name / "nested_run")


def test_rejected_output_path_is_not_created(tmp_path, monkeypatch):
    # A path inside a forbidden dir must never be created, even accidentally.
    forbidden = LEGACY_OUTPUT_DIR / "should_not_exist_run"
    with pytest.raises(UnsafeOutputPathError):
        resolve_output_dir(forbidden)
    assert not forbidden.exists()


def test_create_false_does_not_create_directory(tmp_path):
    target = tmp_path / "not_created"
    resolved = resolve_output_dir(target, create=False)
    assert resolved == target.resolve()
    assert not target.exists()


def test_input_directory_must_exist(tmp_path):
    with pytest.raises(InputPathError):
        resolve_input_dir(tmp_path / "does_not_exist")


def test_missing_input_path_is_rejected():
    with pytest.raises(InputPathError):
        resolve_input_dir(None)
    with pytest.raises(InputPathError):
        resolve_input_dir("")


def test_input_path_must_be_directory(tmp_path):
    file_path = tmp_path / "a_file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(InputPathError):
        resolve_input_dir(file_path)


def test_existing_input_directory_resolves(tmp_path):
    resolved = resolve_input_dir(tmp_path)
    assert resolved == tmp_path.resolve()


def test_readonly_input_may_point_at_historical_outputs():
    # Read-only inputs are allowed to reference the protected outputs/ dir.
    resolved = resolve_input_dir(LEGACY_OUTPUT_DIR)
    assert resolved == LEGACY_OUTPUT_DIR.resolve()


def test_importing_module_creates_no_directories():
    # Importing the module must not have created any directory. The module only
    # references PROJECT_ROOT/LEGACY_OUTPUT_DIR (which already exist in the repo)
    # and must not create a spurious directory of its own.
    assert path_safety.PROJECT_ROOT.is_dir()
    spurious = PROJECT_ROOT / "path_safety"
    assert not spurious.exists()
