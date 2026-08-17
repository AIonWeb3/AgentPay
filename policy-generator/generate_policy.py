"""
Policy Generator — Rule-Based Heuristic

Reads a JSON transaction log and produces a minimal least-privilege
PolicySpec (allowed contract/method pairs + per-period spend caps).

The heuristic:
1. Extract unique (contract_id, method) pairs from the log.
2. For each contract, compute the p95 of observed amounts × 1.5 safety
   margin as the spend cap.
3. Estimate the period from the timestamp range of the log.

# TODO: Swap heuristic for LLM summarizer
# The generate_policy() function has a clear seam: replace the body with
# an LLM call that takes the transaction log and returns a PolicySpec.
# The schema and CLI interface remain unchanged.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from schema import AllowedContract, AllowedMethod, PolicySpec


# ---------------------------------------------------------------------------
# Transaction log types
# ---------------------------------------------------------------------------

# Expected input format (list of):
# {
#   "contract_id": "C...",
#   "method": "transfer",
#   "amount": 1000,
#   "timestamp": "2025-01-15T10:30:00Z"
# }


def percentile(data: List[float], p: float) -> float:
    """Compute the p-th percentile of a list of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


def estimate_period_ledgers(timestamps: List[str]) -> int:
    """
    Estimate the period in ledgers from the timestamp range.

    Assumes ~5 seconds per ledger on Stellar.
    Default: 17280 ledgers ≈ 1 day.
    """
    if len(timestamps) < 2:
        return 17280  # Default: 1 day

    dts = sorted(datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps)
    span_seconds = (dts[-1] - dts[0]).total_seconds()

    # Convert to ledgers (5 seconds per ledger), add 20% buffer
    ledgers = int((span_seconds / 5.0) * 1.2)

    # Clamp to reasonable range: minimum 1 hour, maximum 7 days
    return max(720, min(ledgers, 120960))


def score_transactions(
    tx_log: List[Dict[str, Any]],
    safety_margin: float = 1.5,
    percentile_threshold: float = 95.0,
) -> PolicySpec:
    """
    Generate a minimal least-privilege PolicySpec from a transaction log.

    # TODO: replace with model
    # Interface: takes tx_log, returns PolicySpec. The schema stays the same.

    Args:
        tx_log: List of transaction entries with contract_id, method,
                amount, and timestamp fields.
        safety_margin: Multiplier applied to the percentile-based cap.
        percentile_threshold: Which percentile to use for cap calculation.

    Returns:
        A PolicySpec with the minimal allowlist and spend caps.
    """
    # Group transactions by contract_id
    by_contract: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"methods": set(), "amounts": []}
    )

    timestamps = []

    for tx in tx_log:
        contract_id = tx["contract_id"]
        method = tx["method"]
        amount = tx.get("amount", 0)
        timestamp = tx.get("timestamp", "")

        by_contract[contract_id]["methods"].add(method)
        by_contract[contract_id]["amounts"].append(float(amount))
        if timestamp:
            timestamps.append(timestamp)

    # Estimate the period from timestamp range
    period_ledgers = estimate_period_ledgers(timestamps)

    # Determine rate limit scaling factor
    dts = sorted(datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps) if timestamps else []
    span_seconds = (dts[-1] - dts[0]).total_seconds() if len(dts) >= 2 else 0
    span_ledgers = max(1, int(span_seconds / 5.0))
    rate_multiplier = (period_ledgers / span_ledgers) if span_ledgers > 0 else 1.0

    # Build the allowed contracts list
    allowed_contracts: List[AllowedContract] = []

    for contract_id, data in by_contract.items():
        # Compute the spend cap: p95 of observed amounts × safety margin
        p95 = percentile(data["amounts"], percentile_threshold)
        cap = int(p95 * safety_margin)

        # Ensure minimum cap of 1 stroop
        cap = max(cap, 1)

        # Compute max calls per period: observed calls × rate_multiplier × safety_margin
        base_calls = len(data["amounts"])
        max_calls = max(1, int(base_calls * rate_multiplier * safety_margin))

        allowed_contracts.append(
            AllowedContract(
                contract_id=contract_id,
                allowed_methods=[
                    AllowedMethod(name=m) for m in sorted(data["methods"])
                ],
                max_spend_per_period=cap,
                max_calls_per_period=max_calls,
            )
        )

    # Sort by contract_id for deterministic output
    allowed_contracts.sort(key=lambda c: c.contract_id)

    return PolicySpec(
        allowed_contracts=allowed_contracts,
        period_ledgers=period_ledgers,
        source_tx_count=len(tx_log),
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI: reads a JSON transaction log from stdin or a file argument,
    outputs a PolicySpec JSON to stdout.

    Usage:
        python generate_policy.py < transaction_log.json
        python generate_policy.py transaction_log.json
        python generate_policy.py transaction_log.json > policy.json
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            tx_log = json.load(f)
    else:
        tx_log = json.load(sys.stdin)

    policy = score_transactions(tx_log)
    print(policy.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
