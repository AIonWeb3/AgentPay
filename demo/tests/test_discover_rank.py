from engine import AgentPayEngine


def test_discover_ranks_weather_first():
    engine = AgentPayEngine()
    results = engine.discover("weather")
    assert results[0]["id"] == "weather-oracle"


def test_empty_query_returns_all():
    engine = AgentPayEngine()
    assert len(engine.discover("")) == len(engine.resources)
