PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'operator',
    ledger INTEGER NOT NULL DEFAULT 12400000,
    period_ledgers INTEGER NOT NULL DEFAULT 17280,
    pitch_step INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    source_tx_count INTEGER NOT NULL DEFAULT 0,
    period_ledgers INTEGER NOT NULL DEFAULT 17280,
    generated_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    method TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS rules (
    rule_id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    method TEXT NOT NULL,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    max_spend_per_period INTEGER NOT NULL,
    max_calls_per_period INTEGER NOT NULL,
    spent INTEGER NOT NULL DEFAULT 0,
    calls INTEGER NOT NULL DEFAULT 0,
    last_reset INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    ts REAL NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    resource_id TEXT NOT NULL DEFAULT '',
    amount INTEGER NOT NULL DEFAULT 0,
    remaining INTEGER NOT NULL DEFAULT 0,
    tx_hash TEXT,
    ledger INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
