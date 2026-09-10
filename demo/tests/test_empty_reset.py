from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_empty_states_and_reset_confirm():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    assert "No auth_decision events yet." in js
    assert "Marketplace is empty." in js
    assert "window.confirm" in js
    assert ".empty" in css
