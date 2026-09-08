"""Guard that CI configuration stays present and complete."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    assert WORKFLOW.is_file()


def test_ci_runs_rust_and_python_gates():
    text = WORKFLOW.read_text(encoding="utf-8")
    for needle in (
        "cargo test",
        "pytest",
    ):
        assert needle in text, f"CI workflow missing: {needle}"
