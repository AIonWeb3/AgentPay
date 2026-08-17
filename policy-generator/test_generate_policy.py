import pytest
from datetime import datetime, timedelta, timezone

from generate_policy import score_transactions

def test_score_transactions_outlier():
    base_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # 20 steady volume transactions
    tx_log = []
    for i in range(20):
        tx_log.append({
            "contract_id": "C_STEADY_VENDOR",
            "method": "buy",
            "amount": 10,
            "timestamp": (base_time + timedelta(minutes=i)).isoformat()
        })
        
    # 1 outlier spike
    tx_log.append({
        "contract_id": "C_STEADY_VENDOR",
        "method": "buy",
        "amount": 1000,
        "timestamp": (base_time + timedelta(minutes=20)).isoformat()
    })
    
    policy = score_transactions(tx_log)
    
    assert len(policy.allowed_contracts) == 1
    contract_policy = policy.allowed_contracts[0]
    
    assert contract_policy.contract_id == "C_STEADY_VENDOR"
    
    # The p95 of [10]*20 + [1000] should be 10.
    # With a safety margin of 1.5, the cap should be 15.
    assert contract_policy.max_spend_per_period >= 10
    assert contract_policy.max_spend_per_period < 1000
    assert contract_policy.max_spend_per_period == 15
    
    # Rate limit check:
    # 21 calls in 20 minutes (1200 seconds).
    # span_ledgers = 1200 / 5 = 240
    # period_ledgers for 1200 seconds is 1200/5 * 1.2 = 288. max(720, 288) = 720
    # rate_multiplier = 720 / 240 = 3
    # base_calls = 21, max_calls = 21 * 3 * 1.5 = 94
    assert contract_policy.max_calls_per_period >= 21
