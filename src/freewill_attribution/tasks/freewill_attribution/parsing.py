"""Parsing and validation for the freewill-attribution core response (FAST-001).

Parsing is strict but tolerant of markdown code fences. Validation checks:
- all expected item_ids present (else MISSING_ITEM),
- no unknown item_ids (else UNKNOWN_ITEM),
- no duplicate item_ids (else DUPLICATE_ITEM),
- ratings are integers inside each item's valid range (else OUT_OF_RANGE),
- overall structural shape (else SCHEMA_FAILURE).

Failure codes here map to ``docs/benchmark/FAILURE_TAXONOMY.md``.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ...benchmark.models import AttemptParseStatus, AttemptValidationStatus
from . import spec

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_response(text: str) -> tuple[dict[str, Any] | None, AttemptParseStatus, str]:
    """Parse raw response text into a dict.

    Returns ``(payload, parse_status, message)``. ``payload`` is None on failure.
    """
    if text is None or text.strip() == "":
        return None, AttemptParseStatus.EMPTY, "empty response"
    stripped = _FENCE.sub("", text.strip()).strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if match:
            try:
                payload = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None, AttemptParseStatus.MALFORMED_JSON, "malformed json"
        else:
            return None, AttemptParseStatus.MALFORMED_JSON, "malformed json"
    if not isinstance(payload, dict):
        return None, AttemptParseStatus.PARSE_FAILURE, "top-level not an object"
    return payload, AttemptParseStatus.OK, "ok"


def validate_core(
    payload: dict[str, Any],
) -> tuple[dict[str, int], AttemptValidationStatus, dict[str, list[str]], str]:
    """Validate a parsed core payload.

    Returns ``(ratings, validation_status, detail, message)`` where ``ratings``
    contains only in-range integer ratings for known items, and ``detail`` lists
    missing / unknown / duplicate / out_of_range item_ids.
    """
    detail: dict[str, list[str]] = {
        "missing": [],
        "unknown": [],
        "duplicate": [],
        "out_of_range": [],
    }
    items = payload.get("items")
    if not isinstance(items, list):
        return {}, AttemptValidationStatus.SCHEMA_FAILURE, detail, "items missing or not a list"

    seen: set[str] = set()
    ratings: dict[str, int] = {}
    expected = set(spec.ITEM_IDS)

    for entry in items:
        if not isinstance(entry, dict) or "item_id" not in entry or "rating" not in entry:
            return {}, AttemptValidationStatus.SCHEMA_FAILURE, detail, "malformed item entry"
        item_id = str(entry["item_id"])
        if item_id in seen:
            detail["duplicate"].append(item_id)
            continue
        seen.add(item_id)
        if item_id not in expected:
            detail["unknown"].append(item_id)
            continue
        rating = entry["rating"]
        if isinstance(rating, bool) or not isinstance(rating, int):
            detail["out_of_range"].append(item_id)
            continue
        low, high = spec.ITEM_RANGE[item_id]
        if rating < low or rating > high:
            detail["out_of_range"].append(item_id)
            continue
        ratings[item_id] = rating

    detail["missing"] = [i for i in spec.ITEM_IDS if i not in ratings and i not in detail["out_of_range"]]

    # Priority ordering of validation failure reasons.
    if detail["duplicate"]:
        return ratings, AttemptValidationStatus.DUPLICATE_ITEM, detail, "duplicate item_id(s)"
    if detail["unknown"]:
        return ratings, AttemptValidationStatus.UNKNOWN_ITEM, detail, "unknown item_id(s)"
    if detail["out_of_range"]:
        return ratings, AttemptValidationStatus.OUT_OF_RANGE, detail, "rating(s) out of range"
    if detail["missing"]:
        return ratings, AttemptValidationStatus.MISSING_ITEM, detail, "missing item(s)"
    return ratings, AttemptValidationStatus.OK, detail, "ok"


__all__ = ["parse_response", "validate_core"]
