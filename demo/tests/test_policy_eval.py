from policy_eval import evaluate_call


def test_evaluate_under_cap():
    d = evaluate_call(
        allowlisted=True, amount=50, spent=0, max_spend=1000, calls=0, max_calls=10
    )
    assert d.ok
    assert d.remaining == 950


def test_evaluate_not_allowlisted():
    d = evaluate_call(
        allowlisted=False, amount=50, spent=0, max_spend=1000, calls=0, max_calls=10
    )
    assert not d.ok
    assert d.error == "PolicyDenied"
