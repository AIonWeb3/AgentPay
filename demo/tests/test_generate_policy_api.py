from auth import OPERATOR_ENV
from httputil import asgi_request
from server import app


def test_generate_policy_endpoint(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "op")
    res = asgi_request(app, "POST", "/api/generate-policy", headers={"X-Api-Key": "op"})
    assert res.status_code == 200
    body = res.json()
    assert body["allowed_contracts"]
    assert body["source_tx_count"] > 0
