from auth import OPERATOR_ENV
from httputil import asgi_request
from server import app


def test_pitch_steps_through_story(monkeypatch):
    monkeypatch.setenv(OPERATOR_ENV, "op")
    headers = {"X-Api-Key": "op"}
    asgi_request(app, "POST", "/api/reset", headers=headers)
    names = []
    for _ in range(7):
        res = asgi_request(app, "POST", "/api/pitch/step", headers=headers)
        assert res.status_code == 200
        body = res.json()
        names.append(body["name"])
        assert body["script"]
    assert names == ["simulate", "generate", "discover", "budget", "pay", "deny", "scope"]
    deny = asgi_request(app, "POST", "/api/pitch/step", headers=headers)
    # wrapped after 7: reset then step 1
    assert deny.status_code == 200
