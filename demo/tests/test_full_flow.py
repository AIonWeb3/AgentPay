from auth import OPERATOR_ENV
from httputil import asgi_request
from server import app


def test_full_discover_budget_pay_deny_scope_flow(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "op")
    headers = {"X-Api-Key": "op"}
    assert asgi_request(app, "POST", "/api/reset", headers=headers).status_code == 200

    found = asgi_request(
        app, "POST", "/api/discover", json={"query": "weather"}, headers=headers
    ).json()["results"]
    assert any(r["id"] == "weather-oracle" for r in found)

    budget = asgi_request(app, "GET", "/api/budget", headers=headers).json()
    assert budget["remaining_stroops"] > 0
    assert "weather-oracle" in budget["remaining_by_vendor"]

    first = asgi_request(
        app, "POST", "/api/pay", json={"resource_id": "weather-oracle"}, headers=headers
    ).json()
    assert first["ok"] is True
    assert first["tx_hash"]

    second = asgi_request(
        app, "POST", "/api/pay", json={"resource_id": "weather-oracle"}, headers=headers
    ).json()
    assert second["ok"] is False
    assert second["error"] == "InsufficientBudget"

    price = asgi_request(
        app, "POST", "/api/pay", json={"resource_id": "price-feed"}, headers=headers
    ).json()
    assert price["ok"] is True
