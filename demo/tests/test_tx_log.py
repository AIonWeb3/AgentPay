from auth import READER_ENV
from httputil import asgi_request
from server import app


def test_tx_log_export(monkeypatch):
    monkeypatch.setenv(READER_ENV, "read")
    res = asgi_request(app, "GET", "/api/tx-log", headers={"X-Api-Key": "read"})
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == len(body["transactions"])
    assert body["count"] >= 1
    assert {"contract_id", "method", "amount", "timestamp"} <= set(body["transactions"][0])
