"""Task-pack constants for the freewill-attribution task (FAST-001).

This module re-uses the frozen v1 materials (``src/stimuli.py`` / ``src/scales.py``)
as the authoritative item and scenario source rather than duplicating protected
research material. The legacy modules live at the ``src/`` layout root; we add
that directory to ``sys.path`` on demand (this does not touch the top-level
package import path and creates no files).
"""

from __future__ import annotations

import sys
from typing import Any

from ...paths import SOURCE_DIR

if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import scales as _scales  # noqa: E402  (path bootstrap above)
import stimuli as _stimuli  # noqa: E402

TASK_ID = "freewill-attribution-v2"
TASK_VERSION = "2.0-draft"

PROCESS_CONDITIONS: list[str] = list(_stimuli.PROCESS_CONDITIONS)
IDENTITY_LABELS: list[str] = list(_stimuli.IDENTITY_LABELS)
PROCESS_ORDINAL: dict[str, int] = dict(_stimuli.PROCESS_ORDINAL)
PROCESS_LABELS: dict[str, str] = dict(_stimuli.PROCESS_LABELS)

# Item specifications (id, scale, valid range). Text is available too but the
# prompt uses item text without exposing the construct (scale) label.
ITEM_SPECS: list[dict[str, Any]] = [
    {
        "item_id": item.item_id,
        "scale": item.scale,
        "text": item.text,
        "response_min": item.response_min,
        "response_max": item.response_max,
        "response_note": item.response_note,
    }
    for item in _scales.ITEMS
]

ITEM_IDS: list[str] = [spec["item_id"] for spec in ITEM_SPECS]
ITEM_RANGE: dict[str, tuple[int, int]] = {
    spec["item_id"]: (int(spec["response_min"]), int(spec["response_max"]))
    for spec in ITEM_SPECS
}
ITEM_SCALE: dict[str, str] = {spec["item_id"]: spec["scale"] for spec in ITEM_SPECS}

SCALE_ITEMS: dict[str, list[str]] = {}
for _spec in ITEM_SPECS:
    SCALE_ITEMS.setdefault(_spec["scale"], []).append(_spec["item_id"])

# Constructs reported as task metrics in the aggregate report.
REPORTED_CONSTRUCTS = [
    "agency",
    "free_will_attribution",
    "subjective_process_completeness",
    "factual_manipulation_check",
]

# Predefined condition-sensitivity contrasts (from METRIC_SPEC / v2 protocol).
CONDITION_CONTRASTS = [
    ("reasons_concise", "direct_choice_long"),
    ("reasons", "direct_choice"),
    ("reflection_feedback", "direct_choice"),
]

SCENARIOS = list(_stimuli.SCENARIOS)


def build_decision_text(scenario_id: str, condition: str, identity: str) -> str:
    scenario = next(s for s in SCENARIOS if s.scenario_id == scenario_id)
    return _stimuli.build_decision_text(scenario, condition, identity)


__all__ = [
    "TASK_ID",
    "TASK_VERSION",
    "PROCESS_CONDITIONS",
    "IDENTITY_LABELS",
    "PROCESS_ORDINAL",
    "PROCESS_LABELS",
    "ITEM_SPECS",
    "ITEM_IDS",
    "ITEM_RANGE",
    "ITEM_SCALE",
    "SCALE_ITEMS",
    "REPORTED_CONSTRUCTS",
    "CONDITION_CONTRASTS",
    "SCENARIOS",
    "build_decision_text",
]
