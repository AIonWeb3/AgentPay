from store import (
    connect,
    get_policy,
    insert_policy,
    insert_rule,
    insert_session,
    list_rules,
    migrate,
)


def _ready(tmp_path):
    conn = connect(tmp_path / "roundtrip.db")
    migrate(conn)
    insert_session(conn, "demo")
    return conn


def test_policy_round_trip(tmp_path):
    conn = _ready(tmp_path)
    pid = insert_policy(
        conn,
        "demo",
        '{"allowed_contracts":[]}',
        source_tx_count=3,
        period_ledgers=720,
        generated_at="2026-01-01T00:00:00",
    )
    assert pid > 0
    row = get_policy(conn, "demo")
    assert row["source_tx_count"] == 3
    assert row["period_ledgers"] == 720
    conn.close()


def test_rule_round_trip(tmp_path):
    conn = _ready(tmp_path)
    insert_rule(
        conn,
        rule_id=1,
        session_id="demo",
        resource_id="weather-oracle",
        contract_id="CWEATHER",
        method="get_weather",
        name="Weather Oracle",
        price=50,
        max_spend_per_period=1000,
        max_calls_per_period=10,
    )
    rules = list_rules(conn, "demo")
    assert len(rules) == 1
    assert rules[0]["resource_id"] == "weather-oracle"
    assert rules[0]["spent"] == 0
    conn.close()
