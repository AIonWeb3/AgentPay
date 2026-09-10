from engine import AgentPayEngine
from store import connect, list_rules


def test_spend_windows_persist_across_pay(tmp_path):
    db = tmp_path / "w.db"
    engine = AgentPayEngine(db_path=db, session_id="win-1")
    before = list_rules(connect(db), "win-1")
    weather = next(r for r in before if r["resource_id"] == "weather-oracle")
    assert weather["spent"] == 0
    engine.pay_and_call("weather-oracle")
    after = list_rules(connect(db), "win-1")
    weather = next(r for r in after if r["resource_id"] == "weather-oracle")
    assert weather["spent"] == 50
    assert weather["calls"] == 1
