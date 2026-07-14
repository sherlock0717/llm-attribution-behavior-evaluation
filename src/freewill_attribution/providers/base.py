"""Provider interface for benchmark runs (FAST-001).

This defines the abstract provider boundary and the response envelope. Only a
deterministic mock provider is implemented this round (see ``mock.py``). No real
network provider is implemented and no API key is read anywhere in this package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ProviderErrorCategory(str, Enum):
    """Stable categories for provider-side failures (offline-classified).

    These map onto FAILURE_TAXONOMY.md codes. This round they are only ever
    produced from FAKE exceptions in tests; no real HTTP error is created.
    """

    AUTH_FAILURE = "AUTH_FAILURE"
    BUDGET_OR_BALANCE_FAILURE = "BUDGET_OR_BALANCE_FAILURE"
    RATE_LIMITED = "RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TRANSPORT_ERROR = "TRANSPORT_ERROR"
    REQUEST_INVALID = "REQUEST_INVALID"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"


class ProviderError(RuntimeError):
    """Base class for provider errors carrying a stable category.

    The message MUST NOT contain any credential material; adapters are
    responsible for never placing an API key into the message or context.
    """

    category: ProviderErrorCategory = ProviderErrorCategory.PROVIDER_UNAVAILABLE

    def __init__(self, message: str, *, category: ProviderErrorCategory | None = None,
                 retryable: bool | None = None):
        super().__init__(message)
        if category is not None:
            self.category = category
        # Whether a retry is sensible for this category (offline heuristic).
        if retryable is None:
            retryable = self.category in (
                ProviderErrorCategory.RATE_LIMITED,
                ProviderErrorCategory.PROVIDER_UNAVAILABLE,
                ProviderErrorCategory.TRANSPORT_ERROR,
            )
        self.retryable = retryable


@dataclass(frozen=True)
class ProviderRequest:
    """Everything a provider needs to produce one response attempt.

    The request intentionally carries only task/design coordinates and the
    rendered prompt. It never carries credentials.
    """

    prompt: str
    task_id: str
    condition: str
    identity: str
    scenario_id: str
    seed: int
    request_index: int
    attempt: int = 1
    item_specs: tuple[dict[str, Any], ...] = ()
    structure_level: int = 0
    choice_valence: str = "mixed_choice"
    # Test-only knob: force a malformed / incomplete first attempt to exercise
    # the repair path. Never set by normal runs.
    fault: str | None = None


@dataclass(frozen=True)
class ProviderResponse:
    """A single provider response envelope. ``text`` is the raw model output."""

    text: str
    provider: str
    model_id: str
    latency_ms: float
    finish_reason: str
    usage: dict[str, Any] | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    """Minimal provider protocol."""

    provider_name: str
    model_id: str

    def generate(self, request: ProviderRequest) -> ProviderResponse:  # pragma: no cover - protocol
        ...


__all__ = [
    "ProviderRequest",
    "ProviderResponse",
    "Provider",
    "ProviderErrorCategory",
    "ProviderError",
]
