"""Shared, explicit, testable output-path safety helpers for the legacy scripts.

This module ONLY handles filesystem path resolution and validation. It performs
no research logic, no data generation, and no writing on import. In particular,
importing this module must never create directories or files.

Design goals (FND-004):
- Every generation / analysis write must go to an explicitly provided path.
- Missing output path => fail fast.
- Never default to (or allow writing inside) the protected historical
  ``outputs/`` directory or other repository-internal source directories.
"""

from __future__ import annotations

from pathlib import Path

# ``src/path_safety.py`` -> ``parents[1]`` is the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# The protected historical results directory. Read-only inputs may point here,
# but nothing is ever allowed to write here.
LEGACY_OUTPUT_DIR = (PROJECT_ROOT / "outputs").resolve()

# Directories that must never be used as, or contain, a write target.
_FORBIDDEN_OUTPUT_DIRS = (
    LEGACY_OUTPUT_DIR,
    (PROJECT_ROOT / ".git").resolve(),
    (PROJECT_ROOT / ".venv").resolve(),
    (PROJECT_ROOT / "src").resolve(),
    (PROJECT_ROOT / "docs").resolve(),
    (PROJECT_ROOT / "tests").resolve(),
)


class UnsafeOutputPathError(ValueError):
    """Raised when a requested output directory is missing or unsafe."""


class InputPathError(ValueError):
    """Raised when a requested input directory is missing or invalid."""


def _is_within(path: Path, other: Path) -> bool:
    """Return True if ``path`` is equal to or located inside ``other``."""
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def resolve_output_dir(raw_path: object, *, create: bool = True) -> Path:
    """Resolve and validate an explicit output directory.

    Rules:
    - Must be explicitly provided (non-empty).
    - Normalized via ``expanduser().resolve()``.
    - Must not equal the repository root.
    - Must not equal or live inside ``outputs/``, ``.git/``, ``.venv/``,
      ``src/``, ``docs/`` or ``tests/``.
    - Only after passing validation is ``mkdir(parents=True, exist_ok=True)``
      performed (when ``create`` is True).

    Errors always include the explicit path and the rejection reason.
    """
    if raw_path is None or str(raw_path).strip() == "":
        raise UnsafeOutputPathError(
            "An explicit output directory is required, but none was provided. "
            "Pass an explicit --out directory (e.g. a temporary directory or "
            "the repository's future artifacts/ directory)."
        )

    candidate = Path(str(raw_path)).expanduser().resolve()

    if candidate == PROJECT_ROOT:
        raise UnsafeOutputPathError(
            f"Refusing to use the repository root as an output directory: {candidate}. "
            "Choose a dedicated run directory outside of source/results folders."
        )

    for forbidden in _FORBIDDEN_OUTPUT_DIRS:
        if candidate == forbidden or _is_within(candidate, forbidden):
            raise UnsafeOutputPathError(
                f"Refusing to write to a protected repository directory: {candidate}. "
                f"It is equal to or located inside {forbidden}. Historical outputs/, "
                ".git/, .venv/, src/, docs/ and tests/ are never valid write targets."
            )

    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def resolve_input_dir(raw_path: object) -> Path:
    """Resolve and validate an explicit, read-only input directory.

    Rules:
    - Must be explicitly provided (non-empty).
    - Normalized via ``expanduser().resolve()``.
    - Must exist and be a directory.
    - Read-only inputs may point at the historical ``outputs/`` directory.
    - Never creates directories and never modifies the input directory.

    Errors always include the explicit path and the rejection reason.
    """
    if raw_path is None or str(raw_path).strip() == "":
        raise InputPathError(
            "An explicit input directory is required, but none was provided. "
            "Pass an explicit --input directory."
        )

    candidate = Path(str(raw_path)).expanduser().resolve()

    if not candidate.exists():
        raise InputPathError(
            f"Input directory does not exist: {candidate}."
        )
    if not candidate.is_dir():
        raise InputPathError(
            f"Input path is not a directory: {candidate}."
        )
    return candidate
