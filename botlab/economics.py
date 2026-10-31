"""Verified-revenue gate. Decision logic only; no payment processing or cloud shutdown."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

@dataclass(frozen=True)
class RevenueEvent:
    amount_inr: float
    verified: bool
    refunded: bool = False
    source: str = ""

@dataclass(frozen=True)
class BusinessPolicy:
    grace_days: int = 30
    evaluation_days: int = 30
    minimum_net_revenue_inr: float = 999.0
    max_spend_inr: float = 0.0
    shutdown_on_policy_violation: bool = True

@dataclass(frozen=True)
class BusinessDecision:
    status: str
    reason: str
    verified_net_revenue_inr: float
    spending_allowed: bool
    new_jobs_allowed: bool
    external_actions_allowed: bool

def verified_net_revenue(events: Iterable[RevenueEvent]) -> float:
    return round(sum(e.amount_inr for e in events if e.verified and not e.refunded and e.amount_inr > 0), 2)

def evaluate_business(*, started_at, now, events: Iterable[RevenueEvent], policy: BusinessPolicy,
                      policy_violation: bool = False, manual_pause: bool = False) -> BusinessDecision:
    if started_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("started_at and now must be timezone-aware")
    revenue = verified_net_revenue(events)
    age_days = max(0, (now - started_at).total_seconds() / 86400)
    if manual_pause:
        return BusinessDecision("PAUSED", "Manual pause requested", revenue, False, False, False)
    if policy_violation and policy.shutdown_on_policy_violation:
        return BusinessDecision("SHUTDOWN", "Policy/security violation", revenue, False, False, False)
    deadline = policy.grace_days + policy.evaluation_days
    if age_days >= deadline and revenue < policy.minimum_net_revenue_inr:
        return BusinessDecision("SHUTDOWN",
            f"Revenue gate failed: verified net revenue ₹{revenue:.2f} below ₹{policy.minimum_net_revenue_inr:.2f} after {deadline} days",
            revenue, False, False, False)
    return BusinessDecision("ACTIVE", "Within evaluation window or verified revenue target met",
                            revenue, policy.max_spend_inr > 0, True, False)

def decision_as_dict(decision: BusinessDecision) -> dict:
    return asdict(decision)
