"""DeepSeek provider adapter — OFFLINE-validated only (REAL-SETUP-001).

Design guarantees enforced by this module:

- **No network at import or init.** Constructing :class:`DeepSeekProvider` does
  not connect anywhere. The HTTP client is DEPENDENCY-INJECTED via
  :class:`DeepSeekClientProtocol`; tests inject a ``FakeDeepSeekClient``.
- **No API key unless explicitly live.** ``os.environ["DEEPSEEK_API_KEY"]`` is
  read ONLY inside :meth:`DeepSeekProvider.load_api_key`, which is called only
  on the explicit live path after every gate has passed. Dry-run, unit tests
  and showcase builds never call it.
- **Live run is gated.** :func:`assert_live_run_allowed` refuses unless config
  ``enabled`` + ``live_api_allowed`` are true, ``base_url`` / ``model_id`` are
  non-empty, pricing is verified, and both ``--real-api`` and
  ``--confirm-paid-run`` were provided.
- **No key ever leaks.** The key is never placed into requests logged as
  artifacts, errors, or config snapshots.

This round performs NO real request. Only the fake client is exercised.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from ..budget import PricingSnapshot
from .base import ProviderError, ProviderErrorCategory

PROVIDER_NAME = "deepseek"
ENV_VAR = "DEEPSEEK_API_KEY"


# ---------------------------------------------------------------------------
# Request / response envelopes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeepSeekRequest:
    """A single provider request. Carries NO credential."""

    prompt: str
    model_id: str
    temperature: float = 0.0
    max_tokens: int = 2048
    response_format: str = "json_object"
    stream: bool = False
    request_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeepSeekUsage:
    prompt_cache_hit_tokens: int | None = None
    prompt_cache_miss_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class DeepSeekProviderResponse:
    """Full response envelope with reserved fields for a future real run.

    In this round every value is fake/synthetic/null (test-only) and must never
    be written into a public report as a real-run measurement.
    """

    text: str
    provider: str = PROVIDER_NAME
    model_id: str | None = None
    request_id: str | None = None
    system_fingerprint: str | None = None
    finish_reason: str | None = None
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    prompt_cache_hit_tokens: int | None = None
    prompt_cache_miss_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: str | None = None  # Decimal serialized as str, or None
    raw_metadata_ref: str | None = None


class DeepSeekError(ProviderError):
    """DeepSeek-specific provider error (carries a stable category)."""


# HTTP-status -> stable category mapping (used to classify fake exceptions).
STATUS_CATEGORY = {
    400: ProviderErrorCategory.REQUEST_INVALID,
    401: ProviderErrorCategory.AUTH_FAILURE,
    402: ProviderErrorCategory.BUDGET_OR_BALANCE_FAILURE,
    422: ProviderErrorCategory.REQUEST_INVALID,
    429: ProviderErrorCategory.RATE_LIMITED,
    500: ProviderErrorCategory.PROVIDER_UNAVAILABLE,
    503: ProviderErrorCategory.PROVIDER_UNAVAILABLE,
}


def classify_status(status_code: int) -> ProviderErrorCategory:
    """Map an HTTP status code to a stable error category (offline)."""
    if status_code in STATUS_CATEGORY:
        return STATUS_CATEGORY[status_code]
    if 500 <= status_code < 600:
        return ProviderErrorCategory.PROVIDER_UNAVAILABLE
    if 400 <= status_code < 500:
        return ProviderErrorCategory.REQUEST_INVALID
    return ProviderErrorCategory.TRANSPORT_ERROR


class DeepSeekClientProtocol(Protocol):
    """The minimal client interface the provider depends on.

    A real implementation would wrap an HTTP client; tests inject a fake. The
    provider itself never constructs a concrete networked client.
    """

    def complete(self, request: DeepSeekRequest, *, api_key: str,
                 base_url: str, timeout_seconds: int) -> DeepSeekProviderResponse:
        ...


# ---------------------------------------------------------------------------
# Live-run gate
# ---------------------------------------------------------------------------


def live_run_blockers(
    config: dict[str, Any],
    *,
    real_api: bool,
    confirm_paid_run: bool,
) -> list[str]:
    """Return the list of reasons a live run is not allowed (empty = allowed).

    This performs NO network and reads NO environment variable.
    """
    blockers: list[str] = []
    if not real_api:
        blockers.append("missing --real-api flag")
    if not confirm_paid_run:
        blockers.append("missing --confirm-paid-run flag")
    if not config.get("enabled", False):
        blockers.append("config.enabled is false")
    if not config.get("live_api_allowed", False):
        blockers.append("config.live_api_allowed is false")
    if not config.get("base_url"):
        blockers.append("base_url is not set (verify current official base_url)")
    if not config.get("model_id"):
        blockers.append("model_id is not set (verify current official model_id)")
    pricing = PricingSnapshot.from_config(config.get("pricing_snapshot"))
    if not pricing.is_verified:
        blockers.append("pricing_snapshot is not verified")
    return blockers


def assert_live_run_allowed(
    config: dict[str, Any],
    *,
    real_api: bool,
    confirm_paid_run: bool,
) -> None:
    """Raise :class:`DeepSeekError` if any live-run precondition is unmet."""
    blockers = live_run_blockers(config, real_api=real_api, confirm_paid_run=confirm_paid_run)
    if blockers:
        raise DeepSeekError(
            "live DeepSeek run refused; unmet preconditions: " + "; ".join(blockers),
            category=ProviderErrorCategory.REQUEST_INVALID,
            retryable=False,
        )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class DeepSeekProvider:
    """DeepSeek adapter. Never connects at import/init; client is injected."""

    provider_name = PROVIDER_NAME

    def __init__(self, client: DeepSeekClientProtocol, config: dict[str, Any]):
        # No network, no env read here.
        self.client = client
        self.config = dict(config)
        self.model_id = self.config.get("model_id")
        self.base_url = self.config.get("base_url")

    @staticmethod
    def load_api_key(env: dict[str, str] | None = None) -> str:
        """Read the API key from the environment (LIVE path only).

        This is the ONLY place the key is read. It is never called from
        dry-run, unit tests, or showcase builds. The value is never logged and
        never returned into any artifact.
        """
        source = env if env is not None else os.environ
        key = source.get(ENV_VAR, "")
        if not key:
            raise DeepSeekError(
                f"{ENV_VAR} is not set in the environment",
                category=ProviderErrorCategory.AUTH_FAILURE,
                retryable=False,
            )
        return key

    def generate(
        self,
        request: DeepSeekRequest,
        *,
        real_api: bool = False,
        confirm_paid_run: bool = False,
        api_key: str | None = None,
        max_attempts: int | None = None,
    ) -> DeepSeekProviderResponse:
        """Issue a request THROUGH THE INJECTED CLIENT (gated).

        In tests the injected client is a fake and no network occurs. The live
        gate is enforced before any client call. Retries apply only to
        retryable error categories.
        """
        assert_live_run_allowed(
            self.config, real_api=real_api, confirm_paid_run=confirm_paid_run
        )
        key = api_key if api_key is not None else self.load_api_key()
        attempts = max_attempts or int(self.config.get("provider_retry_attempts", 3))
        timeout = int(self.config.get("request_timeout_seconds", 180))
        last_error: DeepSeekError | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self.client.complete(
                    request, api_key=key, base_url=self.base_url, timeout_seconds=timeout
                )
            except DeepSeekError as exc:
                last_error = exc
                if not getattr(exc, "retryable", False) or attempt >= attempts:
                    raise
        assert last_error is not None  # pragma: no cover - loop always sets it
        raise last_error


__all__ = [
    "PROVIDER_NAME",
    "ENV_VAR",
    "DeepSeekRequest",
    "DeepSeekUsage",
    "DeepSeekProviderResponse",
    "DeepSeekError",
    "DeepSeekClientProtocol",
    "DeepSeekProvider",
    "STATUS_CATEGORY",
    "classify_status",
    "live_run_blockers",
    "assert_live_run_allowed",
]
