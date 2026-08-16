# AgentPay-Soroban

> An AI agent discovers, authorizes, pays for, and calls on-chain resources — with
> spending policies generated from data and enforced by a Soroban smart account.

**AgentPay** targets two Stellar Community Fund RFPs simultaneously:

1. **AI-Assisted Policy Toolkit** — Turns observed/simulated transactions into a
   minimal least-privilege account policy (spending caps + contract allowlists).
2. **MCP Discovery & Paid-Call Server** — Lets an AI agent find and pay for a
   resource from inside its own runtime via the Model Context Protocol.

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
└──────────────────────────────────────────┼─────────────────────┘
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
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Language | Description |
|-----------|----------|-------------|
| `contracts/agent-account/` | Rust (Soroban) | Smart account with context rules, spending limits, audit events |
| `mcp-server/` | Rust | MCP server with 3 tools: discover, check_budget, pay_and_call |
| `policy-generator/` | Python | Rule-based policy generator (p95 caps from tx logs) |
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

The server starts on stdio. Connect any MCP-compatible client to use the tools.

### 3. Generate a Policy (Python)

```bash
# Install dependencies
pip install -r policy-generator/requirements.txt

# Generate a synthetic transaction log
python scripts/simulate_agent.py > transaction_log.json

# Generate a policy from the log
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

8. AUDIT     →  Check auth_decision events on-chain
                 Every approve/deny is logged with amounts for review.
```

## Project Structure

```
agentpay-soroban/
├── Cargo.toml                         # Workspace
├── contracts/
│   └── agent-account/
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs                 # Contract: smart account + policy mgmt
│           ├── policy_spec.rs         # PolicySpec contracttypes
│           └── test.rs                # Unit tests
├── mcp-server/
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs                    # MCP server (rmcp, stdio)
│       ├── soroban_client.rs          # Soroban RPC client (stub)
│       └── tools/
│           ├── mod.rs
│           ├── discover.rs            # discover_resources tool
│           ├── check_budget.rs        # check_budget tool
│           └── pay_and_call.rs        # pay_and_call tool
├── policy-generator/
│   ├── requirements.txt
│   ├── schema.py                      # PolicySpec pydantic models
│   └── generate_policy.py             # Rule-based policy generator
├── registry/
│   └── resources.json                 # Seed paid resources
├── scripts/
│   ├── deploy_testnet.sh              # Testnet deployment
│   └── simulate_agent.py              # Synthetic tx log generator
└── README.md
```

## Tech Stack

- **Soroban Contracts**: `soroban-sdk` 27.x, `#![no_std]`, Rust 2021 edition
- **Smart Account Framework**: OpenZeppelin `stellar-accounts` 0.7.x
  - Context rules, spending-limit policies, composable signers
- **MCP Server**: `rmcp` 3.1.x (official Rust MCP SDK), stdio transport
- **Policy Generator**: Python 3.10+, `pydantic` 2.x

## Current Status

**First pass** — the scaffold is complete:
- ✅ `contracts/agent-account` builds with tests green
- ✅ `mcp-server` runs over stdio with three tools returning stub responses
- ✅ `registry/resources.json` populated with 3 test resources
- ✅ `policy-generator` produces valid PolicySpec from transaction logs

**Second pass** (TODO):
- [ ] Wire MCP server tools to real Soroban testnet calls
- [ ] Deploy SpendingLimitPolicy contract alongside the account
- [ ] Implement rolling-window spend tracking
- [ ] Add bounded retry logic to `pay_and_call`
- [ ] Integration tests with testnet

## License

See [LICENSE](LICENSE).
