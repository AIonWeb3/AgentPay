from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_keyboard_and_aria():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    assert 'aria-live="polite"' in html
    assert 'aria-label="Discover paid resources"' in html
    assert "focus-visible" in css
