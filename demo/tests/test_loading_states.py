from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_loading_states_present():
    css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "setBusy" in js
    assert "calling discover_resources" in js
    assert "busy-bar" in css and "busy-bar" in html
