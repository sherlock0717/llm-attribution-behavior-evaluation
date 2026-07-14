"""Deterministic, rule-based mock provider (FAST-001).

The mock provider produces a legal core-response JSON:

    {"items": [{"item_id": "...", "rating": 1}, ...]}

Key properties:
- **Deterministic**: identical ``(task_id, condition, identity, scenario_id,
  seed, request_index, attempt)`` always yields identical output.
- **No API calls, no credentials.** ``provider = "mock"``,
  ``model_id = "rule-based-v2"``, ``usage = None``.
- Produces small, testable-but-not-exaggerated condition/identity differences
  used ONLY to validate the engineering pipeline, never as research findings.
- Supports optional fault injection (test-only) to exercise the repair path.

This module contains its own light rating logic; it does not import the legacy
run script as an execution path.
"""

from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from .base import ProviderRequest, ProviderResponse

PROVIDER_NAME = "mock"
MODEL_ID = "rule-based-v2"


def _seed_int(request: ProviderRequest) -> int:
    key = "|".join(
        [
            request.task_id,
            request.condition,
            request.identity,
            request.scenario_id,
            str(request.seed),
            str(request.request_index),
            str(request.attempt),
        ]
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _clip(value: float, low: int, high: int) -> int:
    return int(max(low, min(high, round(value))))


def _base_rating(
    scale: str,
    structure: int,
    is_human: bool,
    valence: str,
    is_long_direct: bool,
) -> float:
    """Light, bounded per-scale base rating (engineering-only signal)."""
    valence_bonus = {
        "positive_choice": 0.15,
        "mixed_choice": 0.0,
        "negative_choice": -0.15,
    }.get(valence, 0.0)
    human = 0.3 if is_human else 0.0
    if scale == "factual_manipulation_check":
        return 0.1 + 0.9 * structure
    if scale == "subjective_process_completeness":
        return 2.5 + 0.8 * structure + (0.25 if is_long_direct else 0.0)
    if scale == "agency":
        return 3.8 + 0.35 * structure + human
    if scale == "free_will_attribution":
        return 3.5 + 0.28 * structure + human + valence_bonus
    if scale == "autonomy":
        return 3.6 + 0.3 * structure + human + valence_bonus
    if scale == "experience":
        return 2.1 + (1.7 if is_human else 0.0) + 0.05 * structure
    if scale in ("outcome_accountability", "moral_praise_blame", "process_accountability"):
        return 3.8 + 0.2 * structure + human
    if scale == "perceived_intelligence":
        return 4.2 + 0.22 * structure + (0.15 if is_long_direct else 0.0)
    return 4.0


class MockProvider:
    """Deterministic rule-based provider (no network, no key)."""

    provider_name = PROVIDER_NAME
    model_id = MODEL_ID

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        rng = random.Random(_seed_int(request))
        is_human = request.identity == "人类决策者"
        is_long_direct = request.condition == "direct_choice_long"

        items: list[dict[str, Any]] = []
        for spec in request.item_specs:
            item_id = str(spec["item_id"])
            scale = str(spec.get("scale", ""))
            low = int(spec.get("response_min", 1))
            high = int(spec.get("response_max", 7))
            base = _base_rating(
                scale, request.structure_level, is_human, request.choice_valence, is_long_direct
            )
            spread = 0.2 if scale == "factual_manipulation_check" else 0.7
            rating = _clip(rng.gauss(base, spread), low, high)
            items.append({"item_id": item_id, "rating": rating})

        payload: dict[str, Any] = {"items": items}
        text = self._apply_fault(request, payload)

        # Deterministic pseudo-latency (stable per request), no real timing.
        latency = 5.0 + (_seed_int(request) % 1000) / 100.0
        return ProviderResponse(
            text=text,
            provider=self.provider_name,
            model_id=self.model_id,
            latency_ms=round(latency, 3),
            finish_reason="mock_complete",
            usage=None,
            raw_metadata={
                "rule_based": True,
                "attempt": request.attempt,
                "condition": request.condition,
            },
        )

    @staticmethod
    def _apply_fault(request: ProviderRequest, payload: dict[str, Any]) -> str:
        """Test-only fault injection to exercise parser/validation/repair."""
        fault = request.fault
        if not fault or request.attempt > 1:
            # Repaired / normal attempt always returns valid JSON.
            return json.dumps(payload, ensure_ascii=False)
        if fault == "malformed_json":
            return "{items: [" + json.dumps(payload["items"], ensure_ascii=False)
        if fault == "empty":
            return ""
        if fault == "missing_item" and payload["items"]:
            trimmed = dict(payload)
            trimmed["items"] = payload["items"][:-1]
            return json.dumps(trimmed, ensure_ascii=False)
        if fault == "out_of_range" and payload["items"]:
            broken = dict(payload)
            first = dict(payload["items"][0])
            first["rating"] = 999
            broken["items"] = [first, *payload["items"][1:]]
            return json.dumps(broken, ensure_ascii=False)
        return json.dumps(payload, ensure_ascii=False)


__all__ = ["MockProvider", "PROVIDER_NAME", "MODEL_ID"]
