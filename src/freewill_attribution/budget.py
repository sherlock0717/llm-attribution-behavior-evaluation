"""Budget control and cost accounting for provider runs (REAL-SETUP-001).

Everything here is OFFLINE and deterministic:
- It performs no network I/O and reads no API key.
- All money is handled with :class:`decimal.Decimal` (never float) to avoid
  rounding drift in cost accounting.
- When the pricing snapshot is not ``verified`` (or any price field is null),
  cost cannot be computed and a live run MUST be refused; dry-run reports the
  cost estimate as ``unavailable_until_pricing_verified``.

This module is used both by the (deferred) live path and by the dry-run planner.
No cost value produced here is a real run result unless a real run happens.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from .providers.base import ProviderError, ProviderErrorCategory

# Prices are quoted per this many tokens (DeepSeek quotes per 1M tokens).
DEFAULT_UNIT_TOKENS = 1_000_000


class PricingStatus(str, Enum):
    REQUIRES_RUNTIME_VERIFICATION = "requires_runtime_verification"
    VERIFIED = "verified"


class BudgetError(ProviderError):
    """Raised when a run would exceed budget or cannot be priced."""

    category = ProviderErrorCategory.BUDGET_EXCEEDED


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


@dataclass(frozen=True)
class PricingSnapshot:
    """A per-unit-token price snapshot. Only usable when ``status`` is verified.

    ``input_cache_hit`` / ``input_cache_miss`` / ``output`` are prices per
    ``unit_tokens`` tokens, expressed as Decimal. They are None until verified.
    """

    status: PricingStatus = PricingStatus.REQUIRES_RUNTIME_VERIFICATION
    currency: str = "USD"
    unit_tokens: int = DEFAULT_UNIT_TOKENS
    input_cache_hit: Decimal | None = None
    input_cache_miss: Decimal | None = None
    output: Decimal | None = None
    checked_at: str | None = None
    source: str | None = None

    @classmethod
    def from_config(cls, data: dict[str, Any] | None) -> "PricingSnapshot":
        data = data or {}
        status_raw = str(data.get("status", PricingStatus.REQUIRES_RUNTIME_VERIFICATION.value))
        try:
            status = PricingStatus(status_raw)
        except ValueError:
            status = PricingStatus.REQUIRES_RUNTIME_VERIFICATION
        return cls(
            status=status,
            currency=str(data.get("currency", "USD")),
            unit_tokens=int(data.get("unit_tokens", DEFAULT_UNIT_TOKENS)),
            input_cache_hit=_to_decimal(data.get("input_cache_hit")),
            input_cache_miss=_to_decimal(data.get("input_cache_miss")),
            output=_to_decimal(data.get("output")),
            checked_at=data.get("checked_at"),
            source=data.get("source"),
        )

    @property
    def is_verified(self) -> bool:
        return (
            self.status == PricingStatus.VERIFIED
            and self.input_cache_hit is not None
            and self.input_cache_miss is not None
            and self.output is not None
        )


@dataclass(frozen=True)
class UsageRecord:
    """Token usage for a single response. Fields are ints (or 0)."""

    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    completion_tokens: int = 0

    @property
    def prompt_tokens(self) -> int:
        return self.prompt_cache_hit_tokens + self.prompt_cache_miss_tokens

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class BudgetReservation:
    """A worst-case cost reservation held before a request is issued."""

    reservation_id: str
    amount_usd: Decimal
    committed: bool = False
    released: bool = False


@dataclass
class CostSummary:
    reserved_usd: Decimal = Decimal("0")
    committed_usd: Decimal = Decimal("0")
    released_usd: Decimal = Decimal("0")

    def as_dict(self) -> dict[str, str]:
        return {
            "reserved_usd": str(self.reserved_usd),
            "committed_usd": str(self.committed_usd),
            "released_usd": str(self.released_usd),
        }


def cost_of_usage(usage: UsageRecord, pricing: PricingSnapshot) -> Decimal:
    """Compute the Decimal cost of a usage record under a verified pricing.

    Raises :class:`BudgetError` when pricing is not verified (never guesses).
    """
    if not pricing.is_verified:
        raise BudgetError(
            "cost cannot be computed: pricing snapshot is not verified",
        )
    unit = Decimal(pricing.unit_tokens)
    cost = (
        Decimal(usage.prompt_cache_hit_tokens) / unit * pricing.input_cache_hit
        + Decimal(usage.prompt_cache_miss_tokens) / unit * pricing.input_cache_miss
        + Decimal(usage.completion_tokens) / unit * pricing.output
    )
    return cost


class BudgetController:
    """Reserve worst-case cost, commit actual usage, enforce a hard limit.

    All accounting is in Decimal. When pricing is unverified, every reservation
    attempt raises :class:`BudgetError` so a live run cannot proceed. The hard
    limit is checked on both reservation and commit.
    """

    def __init__(self, hard_limit_usd: Any, pricing: PricingSnapshot,
                 worst_case_tokens: int = 4096):
        self.hard_limit_usd = Decimal(str(hard_limit_usd))
        self.pricing = pricing
        self.worst_case_tokens = int(worst_case_tokens)
        self.summary = CostSummary()
        self._reservations: dict[str, BudgetReservation] = {}
        self._counter = 0

    # -- helpers ----------------------------------------------------------
    @property
    def outstanding_usd(self) -> Decimal:
        return self.summary.reserved_usd + self.summary.committed_usd - self.summary.released_usd

    def check_hard_limit(self, prospective_usd: Decimal) -> None:
        if self.outstanding_usd + prospective_usd > self.hard_limit_usd:
            raise BudgetError(
                "hard budget limit would be exceeded",
                category=ProviderErrorCategory.BUDGET_EXCEEDED,
            )

    def _worst_case_cost(self) -> Decimal:
        usage = UsageRecord(prompt_cache_miss_tokens=self.worst_case_tokens,
                            completion_tokens=self.worst_case_tokens)
        return cost_of_usage(usage, self.pricing)

    # -- lifecycle --------------------------------------------------------
    def reserve_worst_case_cost(self) -> BudgetReservation:
        # Raises BudgetError if pricing is unverified (cannot price a live run).
        amount = self._worst_case_cost()
        self.check_hard_limit(amount)
        self._counter += 1
        res = BudgetReservation(reservation_id=f"res-{self._counter}", amount_usd=amount)
        self._reservations[res.reservation_id] = res
        self.summary.reserved_usd += amount
        return res

    def commit_actual_usage(self, reservation: BudgetReservation, usage: UsageRecord) -> Decimal:
        if reservation.committed or reservation.released:
            raise BudgetError("reservation already finalized")
        actual = cost_of_usage(usage, self.pricing)
        # Release the reservation, then commit the actual cost.
        self.summary.reserved_usd -= reservation.amount_usd
        self.check_hard_limit(actual)
        self.summary.committed_usd += actual
        reservation.committed = True
        return actual

    def release_reservation(self, reservation: BudgetReservation) -> None:
        if reservation.committed or reservation.released:
            return
        self.summary.reserved_usd -= reservation.amount_usd
        self.summary.released_usd += reservation.amount_usd
        reservation.released = True


def dry_run_cost_estimate(pricing: PricingSnapshot) -> dict[str, Any]:
    """Return an offline cost-estimate status block for dry-run planning.

    Never fabricates a number when pricing is unverified.
    """
    if pricing.is_verified:
        return {"cost_estimate_status": "available", "currency": pricing.currency}
    return {"cost_estimate_status": "unavailable_until_pricing_verified"}


__all__ = [
    "DEFAULT_UNIT_TOKENS",
    "PricingStatus",
    "BudgetError",
    "PricingSnapshot",
    "UsageRecord",
    "BudgetReservation",
    "CostSummary",
    "BudgetController",
    "cost_of_usage",
    "dry_run_cost_estimate",
]
