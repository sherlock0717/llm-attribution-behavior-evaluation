"""freewill_attribution: minimal package and transitional CLI (FND-005).

This package currently provides a thin, transitional command-line adapter over
the existing safe legacy entry point (``src/run_simulated_study.py``). It does
not yet re-implement the study/analysis logic; see ``runner.py`` for the
source-checkout adapter boundary.

Importing this package must have no filesystem side effects (no files, no
directories, no subprocesses).
"""

from __future__ import annotations

from importlib import metadata

_FALLBACK_VERSION = "0.2.0.dev0"

try:
    __version__ = metadata.version("llm-agent-free-will-attribution")
except metadata.PackageNotFoundError:  # pragma: no cover - depends on install state
    __version__ = _FALLBACK_VERSION

__all__ = ["__version__"]
