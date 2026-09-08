"""Pure policy decision helper shared by the demo engine and tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    ok: bool
    error: str | None
    reason: str
    remaining: int


def evaluate_call(
    *,
    allowlisted: bool,
    amount: int,
    spent: int,
    max_spend: int,
    calls: int,
    max_calls: int,
) -> PolicyDecision:
    remaining = max_spend - spent
    if not allowlisted:
        return PolicyDecision(False, "PolicyDenied", "not_allowlisted", remaining)
    if calls + 1 > max_calls:
        return PolicyDecision(
            False,
            "PolicyDenied",
            f"rate limited: {calls}/{max_calls} calls this period",
            remaining,
        )
    if spent + amount > max_spend:
        return PolicyDecision(
            False,
            "InsufficientBudget",
            f"required {amount} stroops, remaining {remaining} stroops",
            remaining,
        )
    return PolicyDecision(True, None, "under_cap", remaining - amount)
