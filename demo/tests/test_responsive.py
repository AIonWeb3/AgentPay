from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "static" / "styles.css"


def test_mobile_breakpoints():
    text = CSS.read_text(encoding="utf-8")
    assert "@media (max-width: 900px)" in text
    assert "@media (max-width: 480px)" in text
    assert "flex-wrap: wrap" in text
