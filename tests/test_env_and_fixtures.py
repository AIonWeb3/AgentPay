from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
ENV_EXAMPLE = ROOT / ".env.example"


def test_env_example_documents_required_keys():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for key in (
        "DEMO_API_KEY",
        "DEMO_READ_KEY",
        "DATABASE_URL",
        "AGENTPAY_DB",
        "SOROBAN_RPC_URL",
    ):
        assert key in text


def test_sample_tx_log_fixture_is_valid():
    import json

    log = json.loads((FIXTURES / "sample_tx_log.json").read_text(encoding="utf-8"))
    assert len(log) >= 2
    for row in log:
        assert {"contract_id", "method", "amount", "timestamp"} <= set(row)


def test_gitignore_keeps_secrets_and_local_db_out_of_git():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in text
    assert "*.db" in text
