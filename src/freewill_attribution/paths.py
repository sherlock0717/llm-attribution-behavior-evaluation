"""Path helpers for the transitional package CLI (FND-005).

This module only resolves and validates the location of the legacy run script.
It performs no writes, creates no directories, does not change the working
directory, and never reads API keys.

Layout (source checkout / editable install):

    <PROJECT_ROOT>/
        src/                        # SOURCE_DIR
            freewill_attribution/   # PACKAGE_DIR
            run_simulated_study.py  # LEGACY_RUN_SCRIPT
"""

from __future__ import annotations

from pathlib import Path

# ``src/freewill_attribution/paths.py``
PACKAGE_DIR = Path(__file__).resolve().parent
# ``src``
SOURCE_DIR = PACKAGE_DIR.parent
# repository root
PROJECT_ROOT = SOURCE_DIR.parent

# The existing safe legacy generation entry point.
LEGACY_RUN_SCRIPT = SOURCE_DIR / "run_simulated_study.py"


def get_legacy_run_script() -> Path:
    """Return the absolute, resolved path to the legacy run script.

    Raises a clear ``RuntimeError`` if the script cannot be found (for example
    when the package is used outside of a source checkout). This function does
    not create directories, write files, change the working directory, or read
    any API credentials.
    """
    script = LEGACY_RUN_SCRIPT.resolve()
    if not script.is_file():
        raise RuntimeError(
            "Legacy run script not found at "
            f"{script}. The freewill_attribution CLI is currently a "
            "source-checkout transitional adapter and requires the repository "
            "layout (src/run_simulated_study.py) to be present."
        )
    return script


__all__ = [
    "PACKAGE_DIR",
    "SOURCE_DIR",
    "PROJECT_ROOT",
    "LEGACY_RUN_SCRIPT",
    "get_legacy_run_script",
]
