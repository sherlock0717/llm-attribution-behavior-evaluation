"""Prompt template and rendering for the freewill-attribution task (FAST-001).

Implements the v2 core prompt contract:
- **construct-label blinding**: items are presented by their neutral text and
  ``valid_range`` only; the construct/scale label (e.g. ``agency``) is NOT shown.
- **all_items** batching: every item in one request.
- factual-manipulation-check items use their 0-2 range; other items use 1-7.
- The model must return ONLY the core JSON ``{"items": [{"item_id","rating"}]}``;
  runner-owned metadata (condition, identity, participant_id, ...) is NOT
  requested from the model.
"""

from __future__ import annotations

import json
from typing import Any

from . import spec

PROMPT_TEMPLATE_ID = "freewill-attribution-v2-core"
PROMPT_TEMPLATE_VERSION = "2.0-mock"

SYSTEM_TEMPLATE = (
    "你正在阅读一段决策材料，并需要对材料中的决策者作出一系列评分。"
    "请只依据材料内容作答，允许中立、犹豫和个体差异。"
    "只输出 JSON，不要输出任何解释或额外文字。"
)

USER_INSTRUCTION = (
    "请阅读下面的【材料】，然后对每个评分条目给出一个整数评分。"
    "每个条目都标注了它的有效取值范围 valid_range，评分必须落在该范围内。"
    "只输出如下 JSON：{\"items\": [{\"item_id\": \"...\", \"rating\": <整数>}]}。"
    "items 必须覆盖全部条目，不要增加解释字段，不要复述材料。"
)


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
            "batching": "all_items",
            "construct_label_blinding": True,
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
        "output_contract": {"items": [{"item_id": "string", "rating": "integer in valid_range"}]},
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def repair_instruction(missing: list[str], out_of_range: list[str]) -> str:
    """A concise repair instruction appended for a repair attempt."""
    return json.dumps(
        {
            "repair": True,
            "note": "上一次输出无效，请只输出合法 JSON：{\"items\":[{\"item_id\",\"rating\"}]}。",
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
