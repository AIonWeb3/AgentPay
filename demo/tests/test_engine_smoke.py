from engine import AgentPayEngine


def test_engine_loads_registry_and_policy():
    engine = AgentPayEngine()
    snap = engine.snapshot()
    assert snap["rule_count"] >= 1
    assert snap["resources"]
    assert snap["remaining_stroops"] > 0
