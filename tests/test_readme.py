from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"


def test_readme_covers_pitch_ci_and_simulation_boundary():
    text = README.read_text(encoding="utf-8")
    assert "scripts/run_pitch.sh" in text
    assert "scripts/ci.sh" in text
    assert "DEMO_API_KEY" in text
    assert "Simulated vs on-chain" in text
    assert "actions/workflows/ci.yml" in text
