"""Minimal legacy-entry-point adapter (FND-005).

This module builds and runs a subprocess command that invokes the existing safe
legacy run script. It deliberately does NOT re-implement any research logic
(make_design / mock_response / normalize_record are not copied here). It does
not build a manifest, does not retry, does not change the working directory,
and does not mask the legacy exit code.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .paths import get_legacy_run_script


def build_legacy_run_command(
    *,
    output_dir: str | Path,
    n_per_cell: int = 20,
    seed: int = 20260425,
    temperature: float = 1.0,
    mock: bool = False,
    fresh: bool = False,
) -> list[str]:
    """Build the argument list for invoking the legacy run script.

    Uses ``sys.executable`` and the absolute legacy script path. Returns a plain
    argument list (never a shell string). Boolean flags are only appended when
    True.
    """
    script = get_legacy_run_script()
    command = [
        sys.executable,
        str(script),
        "--out",
        str(output_dir),
        "--n-per-cell",
        str(n_per_cell),
        "--seed",
        str(seed),
        "--temperature",
        str(temperature),
    ]
    if mock:
        command.append("--mock")
    if fresh:
        command.append("--fresh")
    return command


def run_legacy_study(
    *,
    output_dir: str | Path,
    n_per_cell: int = 20,
    seed: int = 20260425,
    temperature: float = 1.0,
    mock: bool = False,
    fresh: bool = False,
) -> int:
    """Run the legacy study script as a subprocess and return its exit code.

    The legacy process inherits stdout/stderr (output is not captured or
    swallowed). Real API calls only happen if the caller does not set
    ``mock=True`` (the legacy script decides that). The legacy return code is
    returned unchanged; errors are never disguised as success and no retry is
    performed.
    """
    command = build_legacy_run_command(
        output_dir=output_dir,
        n_per_cell=n_per_cell,
        seed=seed,
        temperature=temperature,
        mock=mock,
        fresh=fresh,
    )
    result = subprocess.run(command)  # noqa: S603 - list args, no shell
    return result.returncode


__all__ = ["build_legacy_run_command", "run_legacy_study"]
