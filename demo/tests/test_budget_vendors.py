from auth import READER_ENV
from httputil import asgi_request
from server import app


def test_budget_includes_per_vendor_remaining(monkeypatch):
    monkeypatch.setenv(READER_ENV, "read")
    res = asgi_request(app, "GET", "/api/budget", headers={"X-Api-Key": "read"})
    assert res.status_code == 200
    vendors = res.json()["remaining_by_vendor"]
    assert "weather-oracle" in vendors
    assert "remaining_spend" in vendors["weather-oracle"]
    assert "remaining_calls" in vendors["weather-oracle"]
