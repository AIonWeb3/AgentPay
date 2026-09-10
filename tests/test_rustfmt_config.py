"""Rust formatting gates stay enabled in CI."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_rustfmt_toml_exists():
    assert (ROOT / "rustfmt.toml").is_file()
    assert 'edition = "2021"' in (ROOT / "rustfmt.toml").read_text(encoding="utf-8")
