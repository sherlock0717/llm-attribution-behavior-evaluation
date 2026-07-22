"""Task-pack constants for the attribution-behavior task.

The authoritative scenario / condition / item source is the neutral, version-
free task contract under ``tasks/attribution_behavior/`` (loaded via
``contracts.task_loader``). This module is a thin adapter that exposes the
contract to the runner in the shapes it already expects; it keeps NO second
full copy of the scenario or item text (the contract is the single source of
truth). Decision-process rendering is delegated to the contract as well.
"""

from __future__ import annotations

from typing import Any

from ...contracts import load_task_contract

TASK_ID = "attribution-behavior"
# Unified single source of truth for the task version string. This must equal
# configs/tasks/attribution_behavior.yaml:task_version.
TASK_VERSION = "1.0-mock"
FROZEN_MAX_REPAIR_ATTEMPTS = 1

# The single neutral material task contract drives the mock benchmark task pack.
_CONTRACT = load_task_contract()

# The Prompt contract (single source for prompt wording / ids / batching).
PROMPT = _CONTRACT.prompt

# Core batching comes from the Prompt contract, not a hard-coded literal.
CORE_BATCHING = PROMPT.batching

# Scenario objects (contract ScenarioModel instances) expose .scenario_id,
# .domain, .choice_valence, .context, .option_a, .option_b, .fixed_choice.
SCENARIOS = list(_CONTRACT.scenarios)

PROCESS_CONDITIONS: list[str] = list(_CONTRACT.condition_ids)
IDENTITY_LABELS: list[str] = list(_CONTRACT.identity_labels)
PROCESS_ORDINAL: dict[str, int] = {c.condition_id: c.structure_level for c in _CONTRACT.conditions}
PROCESS_LABELS: dict[str, str] = {c.condition_id: c.label for c in _CONTRACT.conditions}

# Item specifications (id, scale, valid range). Text is available too but the
# prompt uses item text without exposing the construct (scale) label. The
# ``scale`` key is kept for backward compatibility with the scoring/prompting
# adapters (it equals the contract's ``construct``).
ITEM_SPECS: list[dict[str, Any]] = [
    {
        "item_id": item.item_id,
        "scale": item.construct,
        "text": item.text,
        "response_min": item.min_score,
        "response_max": item.max_score,
        "response_note": item.response_note,
    }
    for item in _CONTRACT.items
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

# Constructs reported as task metrics in the aggregate report (from contract).
REPORTED_CONSTRUCTS = list(_CONTRACT.reported_constructs)

# Predefined condition-sensitivity contrasts on agency (high vs low structure),
# read from the task contract rather than hard-coded here.
CONDITION_CONTRASTS = [tuple(pair) for pair in _CONTRACT.condition_contrasts]

def build_decision_text(scenario_id: str, condition: str, identity: str) -> str:
    return _CONTRACT.build_decision_text(scenario_id, condition, identity)


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
    "PROMPT",
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
