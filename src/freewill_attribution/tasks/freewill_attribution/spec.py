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
# FAST-001.1: unified single source of truth for the v2 version string. This
# must equal configs/tasks/freewill_attribution.v2.yaml:task_version and the
# protocol_version in docs/protocols/freewill_attribution_v2.md.
TASK_VERSION = "2.0-mock"
CORE_BATCHING = "all_items"
FROZEN_MAX_REPAIR_ATTEMPTS = 1

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


def taskspec_consistency_problems(task_spec: Any) -> list[str]:
    """Check that a declarative TaskSpec matches this Python task pack.

    Returns a list of human-readable problems (empty when consistent). This
    prevents the YAML contract and the Python implementation from drifting into
    two unverified sources of truth (FAST-001.1 §2.10).
    """
    td = task_spec.model_dump() if hasattr(task_spec, "model_dump") else dict(task_spec)
    problems: list[str] = []
    if td.get("task_id") != TASK_ID:
        problems.append(f"task_id mismatch: config={td.get('task_id')!r} impl={TASK_ID!r}")
    if td.get("task_version") != TASK_VERSION:
        problems.append(
            f"task_version mismatch: config={td.get('task_version')!r} impl={TASK_VERSION!r}"
        )
    conds = list((td.get("condition_schema") or {}).get("conditions") or [])
    if set(conds) != set(PROCESS_CONDITIONS):
        problems.append(
            f"condition_schema mismatch: config={sorted(conds)} impl={sorted(PROCESS_CONDITIONS)}"
        )
    idents = list((td.get("identity_schema") or {}).get("identities") or [])
    if set(idents) != set(IDENTITY_LABELS):
        problems.append(
            f"identity_schema mismatch: config={sorted(idents)} impl={sorted(IDENTITY_LABELS)}"
        )
    batching = (td.get("prompt_config") or {}).get("batching") or {}
    core = batching.get("core") or batching.get("recommended_core_default")
    if core != CORE_BATCHING:
        problems.append(f"core batching must be {CORE_BATCHING!r}, got {core!r}")
    return problems


__all__ = [
    "TASK_ID",
    "TASK_VERSION",
    "CORE_BATCHING",
    "FROZEN_MAX_REPAIR_ATTEMPTS",
    "taskspec_consistency_problems",
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
