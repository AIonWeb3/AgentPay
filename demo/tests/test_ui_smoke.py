from httputil import asgi_request
from server import app


def test_index_and_static_assets():
    index = asgi_request(app, "GET", "/")
    assert index.status_code == 200
    assert "AgentPay" in index.text
    css = asgi_request(app, "GET", "/static/styles.css")
    assert css.status_code == 200
    assert "busy-bar" in css.text
    js = asgi_request(app, "GET", "/static/app.js")
    assert js.status_code == 200
    assert "setBusy" in js.text


def test_state_endpoint_ok():
    res = asgi_request(app, "GET", "/api/state")
    assert res.status_code == 200
    assert "rules" in res.json()
