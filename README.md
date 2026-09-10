# AgentPay

[![CI](https://github.com/AIonWeb3/AgentPay/actions/workflows/ci.yml/badge.svg)](https://github.com/AIonWeb3/AgentPay/actions/workflows/ci.yml)

> An AI agent discovers, authorizes, pays for, and calls on-chain resources — with
> spending policies generated from data and enforced by a Soroban smart account.

Repo: [github.com/AIonWeb3/AgentPay](https://github.com/AIonWeb3/AgentPay)

**AgentPay** targets two Stellar Community Fund RFPs:

1. **AI-Assisted Policy Toolkit** — Turns observed/simulated transactions into a
   minimal least-privilege account policy (spending caps + contract allowlists).
2. **MCP Discovery & Paid-Call Server** — Lets an AI agent find and pay for a
   resource from inside its own runtime via the Model Context Protocol.

## Pitch demo

A local operator console walks the full story on one screen: synthetic traffic →
policy → MCP discover → budget check → approved pay → policy deny → per-vendor
scope.

```bash
./scripts/run_pitch.sh
# or:
pip install -r demo/requirements.txt -r policy-generator/requirements.txt
python scripts/seed_pitch.py
python demo/server.py
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080), go fullscreen, click **Run pitch demo**.

**Simulated vs on-chain:** the console and MCP tools enforce the same allowlist,
spend cap, and rate-limit rules as `contracts/agent-account`. Payments use
deterministic local tx hashes. Live Soroban RPC submit is not required for a
client pitch.

Copy `.env.example` if you change keys (`DEMO_API_KEY`, `DEMO_READ_KEY`,
`DATABASE_URL`, `AGENTPAY_STATE`).

## Local CI

```bash
./scripts/ci.sh
```

Gates: `cargo fmt`, `clippy -p mcp-server`, `cargo test --workspace`, `ruff`, `pytest`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Agent Runtime                         │
│                                                                 │
│  ┌──────────┐    MCP/stdio    ┌──────────────────────────────┐ │
│  │ AI Agent  │◄──────────────►│      MCP Server (rmcp)       │ │
│  │           │                │  • discover_resources(query)  │ │
│  └──────────┘                │  • check_budget()             │ │
│                               │  • pay_and_call(id, params)   │ │
│                               └──────────┬───────────────────┘ │
└──────────────────────────────────────────┼───────────────────┘
                                           │ Soroban RPC
                                           ▼
                              ┌────────────────────────┐
                              │  Stellar Testnet       │
                              │                        │
                              │  ┌──────────────────┐  │
                              │  │ Agent Account    │  │
                              │  │ (Smart Account)  │  │
                              │  │                  │  │
                              │  │ Context Rules    │  │
                              │  │ Spending Limits  │  │
                              │  │ Audit Events     │  │
                              │  └──────────────────┘  │
                              └────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Policy Generation Pipeline                   │
│                                                                  │
│  Transaction Log ──► generate_policy.py ──► PolicySpec JSON     │
│  (observed data)      (p95 caps + allowlist)   (apply on-chain) │
│                                                                  │
│  simulate_agent.py ──► synthetic log for demos                  │
│  demo/server.py      ──► visual operator console                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Language | Description |
|-----------|----------|-------------|
| `contracts/agent-account/` | Rust (Soroban) | Smart account with context rules, spending limits, audit events |
| `mcp-server/` | Rust | MCP server with 3 tools: discover, check_budget, pay_and_call |
| `policy-generator/` | Python | Rule-based policy generator (p95 caps from tx logs) |
| `demo/` | Python + HTML | Pitch console: HTTP API + in-memory policy engine |
| `registry/` | JSON | Seed data for paid resource discovery |
| `scripts/` | Bash/Python | Testnet deployment + synthetic data generation |

## Quick Start

### Prerequisites

- [Rust](https://rustup.rs/) 1.84+ with `wasm32v1-none` target
- [Stellar CLI](https://developers.stellar.org/docs/tools/developer-tools/cli/install-cli)
- Python 3.10+

### 1. Build & Test the Smart Account

```bash
cargo test -p agent-account
```

### 2. Run the MCP Server

```bash
cargo run -p mcp-server
```

The server starts on stdio. Tools take real arguments (`query`, `resource_id`,
`params`). Connect any MCP-compatible client to use them.

### 3. Generate a Policy (Python)

```bash
pip install -r policy-generator/requirements.txt
python scripts/simulate_agent.py > transaction_log.json
python policy-generator/generate_policy.py transaction_log.json > policy.json
```

## End-to-End Demo Flow

```
1. SIMULATE  →  python scripts/simulate_agent.py > tx_log.json
                 Generates 75 synthetic transactions across 3 resources.

2. GENERATE  →  python policy-generator/generate_policy.py tx_log.json > policy.json
                 Produces a PolicySpec with per-contract spend caps derived
                 from the p95 of observed amounts.

3. DEPLOY    →  ./scripts/deploy_testnet.sh
                 Deploys the smart account to Stellar testnet with a
                 throwaway funded identity.

4. APPLY     →  stellar contract invoke --id <CONTRACT> ... -- apply_policy ...
                 Installs the generated policy as context rules + spending
                 limits on the smart account.

5. DISCOVER  →  Agent calls discover_resources("weather") via MCP
                 Gets back matching resources with pricing info.

6. CHECK     →  Agent calls check_budget() via MCP
                 Sees remaining allowance under current policy.

7. PAY+CALL  →  Agent calls pay_and_call("weather-oracle", "{}") via MCP
                 Transaction authorized by smart account, spend recorded,
                 resource invoked, response returned.

8. AUDIT     →  Check auth_decision events
                 Every approve/deny is logged with amounts for review.
```

Steps 1–2 and 5–8 can be shown in one take via `python demo/server.py`.

## Project Structure

```
AgentPay/
├── Cargo.toml
├── contracts/agent-account/          # Soroban smart account
├── mcp-server/                       # MCP tools over stdio
├── policy-generator/                 # PolicySpec from tx logs
├── demo/                             # Pitch console (FastAPI + static UI)
│   ├── server.py
│   ├── engine.py                     # In-memory enforcement
│   └── static/
├── registry/resources.json
├── scripts/
│   ├── deploy_testnet.sh
│   └── simulate_agent.py
└── README.md
```

## Tech Stack

- **Soroban Contracts**: `soroban-sdk`, `#![no_std]`
- **Smart Account Framework**: OpenZeppelin `stellar-accounts` 0.7.x
- **MCP Server**: `rmcp` 3.1.x, stdio transport
- **Policy Generator**: Python 3.10+, `pydantic` 2.x
- **Pitch console**: FastAPI + vanilla HTML/CSS/JS

## Current Status

- Smart account: initialize, apply_policy, remaining budget, record_spend, rolling window, per-vendor scope, rate limits (unit tests)
- MCP: discover, check_budget from `AGENTPAY_STATE`, pay_and_call with policy checks, bounded retry, structured errors (stub RPC)
- Policy generator: p95 × 1.5 caps + allowlist; empty logs rejected
- Demo console: SQLite persistence, operator/reader keys, stepped pitch API, polished operator UI

**Out of scope for this MVP (follow-up)**

- Live Soroban RPC submission and funded testnet deploy in CI
- LLM-based policy generation
- Integration tests against public testnet

## License

See [LICENSE](LICENSE).
