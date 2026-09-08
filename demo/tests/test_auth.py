from auth import OPERATOR_ENV
from httputil import asgi_request
from server import app


def test_reset_rejected_without_key():
    assert asgi_request(app, "POST", "/api/reset").status_code == 401


def test_pay_rejected_without_key():
    res = asgi_request(app, "POST", "/api/pay", json={"resource_id": "weather-oracle"})
    assert res.status_code == 401


def test_reset_ok_with_key(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "op-key")
    res = asgi_request(app, "POST", "/api/reset", headers={"X-Api-Key": "op-key"})
    assert res.status_code == 200


def test_state_and_index_remain_public():
    assert asgi_request(app, "GET", "/api/state").status_code == 200
    assert asgi_request(app, "GET", "/").status_code == 200
