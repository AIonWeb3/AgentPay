from engine import AgentPayEngine
from store import connect, list_audit


def test_audit_events_persist(tmp_path):
    db = tmp_path / "a.db"
    engine = AgentPayEngine(db_path=db, session_id="audit-1")
    engine.pay_and_call("weather-oracle")
    rows = list_audit(connect(db), "audit-1")
    decisions = {row["decision"] for row in rows}
    assert "applied" in decisions
    assert "approved" in decisions
    snap = engine.snapshot()
    assert snap["audit"]
    assert snap["audit"][0]["decision"] in {"approved", "applied", "denied"}
