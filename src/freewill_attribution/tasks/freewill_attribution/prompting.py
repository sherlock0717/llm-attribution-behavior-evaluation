"""Prompt rendering for the attribution-behavior task.

All prompt WORDING (template id/version, system, user instruction, output
contract, repair note, batching, construct-label blinding) comes from the
Prompt contract in ``tasks/attribution_behavior/prompt.yaml`` (exposed via
``spec.PROMPT``). This module owns only the serialization / assembly code; it
keeps no second copy of the prompt text.

Contract properties still in effect:
- **construct-label blinding**: items are presented by their neutral text and
  ``valid_range`` only; the construct/scale label (e.g. ``agency``) is NOT shown.
- **all_items** batching: every item in one request.
- factual-manipulation-check items use their 0-2 range; other items use 1-7.
- The model must return ONLY the core JSON described by the output contract;
  runner-owned metadata (condition, identity, participant_id, ...) is NOT
  requested from the model.
"""

from __future__ import annotations

import json
from typing import Any

from . import spec

# All values below are sourced from the Prompt contract (single source of
# truth); the names are kept for backward compatibility with existing callers.
PROMPT_TEMPLATE_ID = spec.PROMPT.prompt_template_id
PROMPT_TEMPLATE_VERSION = spec.PROMPT.prompt_template_version
SYSTEM_TEMPLATE = spec.PROMPT.system
USER_INSTRUCTION = spec.PROMPT.user_instruction


def _blinded_items() -> list[dict[str, Any]]:
    """Items for the prompt WITHOUT construct/scale labels (label blinding)."""
    blinded: list[dict[str, Any]] = []
    for item in spec.ITEM_SPECS:
        blinded.append(
            {
                "item_id": item["item_id"],
                "text": item["text"],
                "valid_range": f"{item['response_min']}-{item['response_max']}",
                "coding": item["response_note"],
            }
        )
    return blinded


def prompt_template_text() -> str:
    """A stable textual representation of the template (for hashing / snapshot)."""
    return json.dumps(
        {
            "prompt_template_id": PROMPT_TEMPLATE_ID,
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "batching": spec.PROMPT.batching,
            "construct_label_blinding": spec.PROMPT.construct_label_blinding,
            "system": SYSTEM_TEMPLATE,
            "user_instruction": USER_INSTRUCTION,
            "items": _blinded_items(),
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )


def render_prompt(design_row: dict[str, Any]) -> str:
    """Render the concrete prompt for one design row (construct labels hidden)."""
    payload = {
        "system": SYSTEM_TEMPLATE,
        "instruction": USER_INSTRUCTION,
        "material": design_row["material"],
        "items": _blinded_items(),
        "output_contract": spec.PROMPT.output_contract,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def repair_instruction(missing: list[str], out_of_range: list[str]) -> str:
    """A concise repair instruction appended for a repair attempt."""
    return json.dumps(
        {
            "repair": True,
            "note": spec.PROMPT.repair_note,
            "must_include_missing": missing,
            "fix_out_of_range": out_of_range,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


__all__ = [
    "PROMPT_TEMPLATE_ID",
    "PROMPT_TEMPLATE_VERSION",
    "SYSTEM_TEMPLATE",
    "USER_INSTRUCTION",
    "prompt_template_text",
    "render_prompt",
    "repair_instruction",
]
