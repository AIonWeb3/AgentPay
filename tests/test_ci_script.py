"""Local CI script must stay aligned with GitHub Actions."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "ci.sh"


def test_local_ci_script_exists():
    assert SCRIPT.is_file()


def test_local_ci_runs_same_core_gates():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "cargo test --workspace" in text
    assert "ruff check" in text
    assert "pytest -q" in text
    assert "set -euo pipefail" in text
