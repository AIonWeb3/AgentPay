"""Engine decisions must match the smart-account unit-test cases."""

import pytest

from policy_eval import evaluate_call


@pytest.mark.parametrize(
    "kwargs,ok,error",
    [
        (
            dict(
                allowlisted=True,
                amount=5_000_000,
                spent=0,
                max_spend=10_000_000,
                calls=0,
                max_calls=100,
            ),
            True,
            None,
        ),
        (
            dict(
                allowlisted=True,
                amount=15_000_000,
                spent=0,
                max_spend=10_000_000,
                calls=0,
                max_calls=100,
            ),
            False,
            "InsufficientBudget",
        ),
        (
            dict(
                allowlisted=True,
                amount=50,
                spent=0,
                max_spend=10_000_000,
                calls=100,
                max_calls=100,
            ),
            False,
            "PolicyDenied",
        ),
        (
            dict(
                allowlisted=False,
                amount=50,
                spent=0,
                max_spend=10_000_000,
                calls=0,
                max_calls=100,
            ),
            False,
            "PolicyDenied",
        ),
        (
            dict(
                allowlisted=True,
                amount=1,
                spent=9_999_999,
                max_spend=10_000_000,
                calls=1,
                max_calls=100,
            ),
            True,
            None,
        ),
    ],
)
def test_evaluate_call_matches_contract_cases(kwargs, ok, error):
    decision = evaluate_call(**kwargs)
    assert decision.ok is ok
    assert decision.error == error
    if ok:
        assert decision.remaining == kwargs["max_spend"] - kwargs["spent"] - kwargs["amount"]
    else:
        assert decision.remaining == kwargs["max_spend"] - kwargs["spent"]
