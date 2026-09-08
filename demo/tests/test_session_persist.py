from engine import AgentPayEngine
from store import connect, get_session, migrate


def test_reset_persists_session_metadata(tmp_path):
    db = tmp_path / "s.db"
    engine = AgentPayEngine(db_path=db, session_id="run-1")
    engine.state.ledger = 12_400_042
    engine._persist_session()
    conn = connect(db)
    migrate(conn)
    row = get_session(conn, "run-1")
    assert row is not None
    assert row["ledger"] == 12_400_042
    assert row["period_ledgers"] == engine.state.period_ledgers
    conn.close()
