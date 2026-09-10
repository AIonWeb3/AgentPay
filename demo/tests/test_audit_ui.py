from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_audit_shows_relative_time_and_remaining():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "function relTime" in js
    assert "rem ${e.remaining}" in js or "rem ${e.remaining}" in js.replace(" ", "")
    assert "<time>" in js
