from engine import AgentPayEngine
from store import connect, get_policy


def test_generated_policy_is_stored(tmp_path):
    db = tmp_path / "p.db"
    engine = AgentPayEngine(db_path=db, session_id="pol-1")
    row = get_policy(connect(db), "pol-1")
    assert row is not None
    assert row["source_tx_count"] == engine.state.source_tx_count
    assert "allowed_contracts" in row["spec_json"]
