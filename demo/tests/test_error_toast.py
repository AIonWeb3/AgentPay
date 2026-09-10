from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_error_toast_and_deny_banner():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "showToast" in js
    assert 'id="toast"' in html
    assert "policy denied" in js
