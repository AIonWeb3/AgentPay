#!/usr/bin/env python3
"""
simulate_agent.py — Generate a Synthetic Transaction Log

Creates a realistic transaction log for demoing the policy generator
without needing a live agent. The log simulates an AI agent that:
- Calls a weather oracle frequently (low cost)
- Checks crypto prices regularly (medium cost)
- Runs AI inference occasionally (high cost)
- Has a mix of normal and outlier transactions

Usage:
    python scripts/simulate_agent.py
    python scripts/simulate_agent.py > transaction_log.json
    python scripts/simulate_agent.py | python policy-generator/generate_policy.py
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Resource definitions (matching registry/resources.json)
# ---------------------------------------------------------------------------

RESOURCES = [
    {
        "contract_id": "CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC",
        "method": "get_weather",
        "base_price": 50,
        "frequency": 0.5,   # 50% of transactions
        "variance": 0.1,    # Low price variance
    },
    {
        "contract_id": "CBQHNAXSI55GX2GN6D67GK7BHVPSLJUGZQEU7WJ5LKR5PNUCGLIMAO4K",
        "method": "get_price",
        "base_price": 100,
        "frequency": 0.35,  # 35% of transactions
        "variance": 0.2,    # Medium price variance
    },
    {
        "contract_id": "CA7QYNF7SOVZ3SS4KVQNHOACI3BSZAHH7KX4IXOFCPXBZW32PCBHFCLJ",
        "method": "run_inference",
        "base_price": 500,
        "frequency": 0.15,  # 15% of transactions
        "variance": 0.5,    # High price variance (different prompt sizes)
    },
]


def generate_transaction_log(
    num_transactions: int = 75,
    start_time: datetime | None = None,
    span_hours: int = 24,
    seed: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic transaction log.

    Args:
        num_transactions: Number of transactions to generate.
        start_time: Start timestamp (defaults to 24h ago).
        span_hours: Time span of the log in hours.
        seed: Random seed for reproducibility.

    Returns:
        List of transaction entries sorted by timestamp.
    """
    if seed is not None:
        random.seed(seed)

    if start_time is None:
        start_time = datetime.utcnow() - timedelta(hours=span_hours)

    transactions: List[Dict[str, Any]] = []

    for i in range(num_transactions):
        # Pick a resource based on frequency weights
        roll = random.random()
        cumulative = 0.0
        resource = RESOURCES[-1]  # Default to last
        for r in RESOURCES:
            cumulative += r["frequency"]
            if roll <= cumulative:
                resource = r
                break

        # Calculate amount with variance
        base = resource["base_price"]
        variance = resource["variance"]
        amount = max(1, int(base * (1.0 + random.uniform(-variance, variance))))

        # Add occasional outliers (5% chance, 3-5x normal)
        if random.random() < 0.05:
            amount = int(amount * random.uniform(3.0, 5.0))

        # Generate timestamp within the span
        offset_seconds = random.uniform(0, span_hours * 3600)
        timestamp = start_time + timedelta(seconds=offset_seconds)

        transactions.append({
            "contract_id": resource["contract_id"],
            "method": resource["method"],
            "amount": amount,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    # Sort by timestamp
    transactions.sort(key=lambda tx: tx["timestamp"])

    return transactions


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate and print a synthetic transaction log."""
    tx_log = generate_transaction_log(
        num_transactions=75,
        span_hours=24,
        seed=42,  # Reproducible for demos
    )

    print(json.dumps(tx_log, indent=2))

    # Print summary to stderr so it doesn't interfere with piping
    import sys
    print(f"\n# Generated {len(tx_log)} transactions", file=sys.stderr)

    contract_counts: Dict[str, int] = {}
    for tx in tx_log:
        cid = tx["contract_id"][:8] + "..."
        contract_counts[cid] = contract_counts.get(cid, 0) + 1

    for cid, count in sorted(contract_counts.items()):
        print(f"#   {cid}: {count} txs", file=sys.stderr)


if __name__ == "__main__":
    main()
