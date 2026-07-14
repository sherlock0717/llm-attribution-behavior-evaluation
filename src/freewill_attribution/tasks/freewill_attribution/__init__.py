"""Freewill-attribution v2 task pack (FAST-001).

Provides deterministic design generation, prompt rendering (with construct-label
blinding), parsing/validation, and scoring/aggregation for the mock vertical
slice. No network calls and no API keys.
"""

from __future__ import annotations

from . import parsing, prompting, scoring, spec, stimuli

__all__ = ["spec", "stimuli", "prompting", "parsing", "scoring"]
