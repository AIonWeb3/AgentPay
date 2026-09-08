from engine import AgentPayEngine
from store import connect, list_resources


def test_registry_imported_to_sqlite(tmp_path):
    db = tmp_path / "r.db"
    engine = AgentPayEngine(db_path=db)
    rows = list_resources(connect(db))
    ids = {row["id"] for row in rows}
    assert "weather-oracle" in ids
    assert {r["id"] for r in engine.resources} == ids
    weather = engine.discover("weather")
    assert weather and weather[0]["id"] == "weather-oracle"
