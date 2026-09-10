from auth import OPERATOR_ENV
from httputil import asgi_request
from server import app


def test_apply_policy_reinstalls_rules(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "op")
    headers = {"X-Api-Key": "op"}
    spec = asgi_request(app, "POST", "/api/generate-policy", headers=headers).json()
    res = asgi_request(app, "POST", "/api/apply-policy", json={"spec": spec}, headers=headers)
    assert res.status_code == 200
    assert res.json()["rule_count"] >= 1
