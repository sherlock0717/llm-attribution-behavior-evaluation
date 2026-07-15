"""Offline budget-controller / cost-accounting tests (REAL-SETUP-001).

All money is Decimal. When pricing is unverified, live pricing must be refused.
No network, no key.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from freewill_attribution import budget


def _verified_pricing():
    return budget.PricingSnapshot.from_config(
        {
            "status": "verified",
            "unit_tokens": 1_000_000,
            "input_cache_hit": "0.07",
            "input_cache_miss": "0.27",
            "output": "1.10",
            "checked_at": "2026-07-14",
            "source": "test-only-fixture",
        }
    )


def test_unverified_pricing_is_not_verified():
    p = budget.PricingSnapshot.from_config({"status": "requires_runtime_verification"})
    assert p.is_verified is False


def test_cost_of_usage_is_decimal_and_correct():
    p = _verified_pricing()
    usage = budget.UsageRecord(
        prompt_cache_hit_tokens=1_000_000,
        prompt_cache_miss_tokens=1_000_000,
        completion_tokens=1_000_000,
    )
    cost = budget.cost_of_usage(usage, p)
    assert isinstance(cost, Decimal)
    # 0.07 + 0.27 + 1.10 = 1.44 per 1M each
    assert cost == Decimal("1.44")


def test_cost_computation_refused_when_pricing_unverified():
    p = budget.PricingSnapshot.from_config({"status": "requires_runtime_verification"})
    usage = budget.UsageRecord(completion_tokens=100)
    with pytest.raises(budget.BudgetError):
        budget.cost_of_usage(usage, p)


def test_reserve_and_commit_updates_summary():
    p = _verified_pricing()
    ctrl = budget.BudgetController(hard_limit_usd="2.00", pricing=p, worst_case_tokens=1000)
    res = ctrl.reserve_worst_case_cost()
    assert ctrl.summary.reserved_usd > Decimal("0")
    actual = ctrl.commit_actual_usage(res, budget.UsageRecord(completion_tokens=500))
    assert isinstance(actual, Decimal)
    assert ctrl.summary.reserved_usd == Decimal("0")
    assert ctrl.summary.committed_usd == actual


def test_reserve_refused_when_pricing_unverified():
    p = budget.PricingSnapshot.from_config({"status": "requires_runtime_verification"})
    ctrl = budget.BudgetController(hard_limit_usd="2.00", pricing=p)
    with pytest.raises(budget.BudgetError):
        ctrl.reserve_worst_case_cost()


def test_hard_limit_enforced():
    p = _verified_pricing()
    # Tiny limit + large worst-case tokens -> reservation exceeds hard limit.
    ctrl = budget.BudgetController(hard_limit_usd="0.0000001", pricing=p, worst_case_tokens=1_000_000)
    with pytest.raises(budget.BudgetError):
        ctrl.reserve_worst_case_cost()


def test_release_returns_reserved_amount():
    p = _verified_pricing()
    ctrl = budget.BudgetController(hard_limit_usd="2.00", pricing=p, worst_case_tokens=1000)
    res = ctrl.reserve_worst_case_cost()
    reserved_before = ctrl.summary.reserved_usd
    assert reserved_before > Decimal("0")
    ctrl.release_reservation(res)
    assert ctrl.summary.reserved_usd == Decimal("0")
    assert ctrl.summary.released_usd == reserved_before


def test_dry_run_cost_estimate_unavailable_when_unverified():
    p = budget.PricingSnapshot.from_config({"status": "requires_runtime_verification"})
    est = budget.dry_run_cost_estimate(p)
    assert est["cost_estimate_status"] == "unavailable_until_pricing_verified"


def test_dry_run_cost_estimate_available_when_verified():
    est = budget.dry_run_cost_estimate(_verified_pricing())
    assert est["cost_estimate_status"] == "available"
