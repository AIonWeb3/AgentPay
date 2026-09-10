from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_policy_cards_show_xlm_and_selection():
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    assert "function xlm" in js
    assert "selected" in js
    assert ".card.selected" in css
    assert ".tag" in css
