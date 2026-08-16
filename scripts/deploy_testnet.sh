#!/usr/bin/env bash
# deploy_testnet.sh — Deploy the AgentPay smart account to Stellar testnet
#
# Usage:
#   ./scripts/deploy_testnet.sh
#
# This script:
# 1. Generates a throwaway testnet identity
# 2. Funds it via Friendbot
# 3. Builds the agent-account contract
# 4. Deploys it to testnet
# 5. Initializes it with the generated identity as admin
#
# No secrets are committed. Everything is ephemeral.

set -euo pipefail

NETWORK="testnet"
IDENTITY="agentpay-deployer-$(date +%s)"

echo "=== AgentPay Testnet Deployment ==="
echo ""

# -----------------------------------------------------------------------
# 1. Generate a throwaway identity
# -----------------------------------------------------------------------
echo "[1/5] Generating testnet identity: $IDENTITY"
stellar keys generate "$IDENTITY" --network "$NETWORK"
ADDRESS=$(stellar keys address "$IDENTITY")
echo "      Address: $ADDRESS"

# -----------------------------------------------------------------------
# 2. Fund via Friendbot
# -----------------------------------------------------------------------
echo "[2/5] Funding via Friendbot..."
curl -s "https://friendbot.stellar.org?addr=$ADDRESS" > /dev/null
echo "      Funded ✓"

# -----------------------------------------------------------------------
# 3. Build the contract
# -----------------------------------------------------------------------
echo "[3/5] Building agent-account contract..."
stellar contract build --manifest-path contracts/agent-account/Cargo.toml
WASM_PATH="target/wasm32v1-none/release/agent_account.wasm"

if [ ! -f "$WASM_PATH" ]; then
    echo "ERROR: WASM not found at $WASM_PATH"
    echo "       Trying alternative path..."
    WASM_PATH=$(find target -name "agent_account.wasm" -type f | head -1)
    if [ -z "$WASM_PATH" ]; then
        echo "ERROR: Could not find compiled WASM. Aborting."
        exit 1
    fi
fi
echo "      WASM: $WASM_PATH"

# -----------------------------------------------------------------------
# 4. Deploy to testnet
# -----------------------------------------------------------------------
echo "[4/5] Deploying to testnet..."
CONTRACT_ID=$(stellar contract deploy \
    --wasm "$WASM_PATH" \
    --source "$IDENTITY" \
    --network "$NETWORK")
echo "      Contract ID: $CONTRACT_ID"

# -----------------------------------------------------------------------
# 5. Initialize with admin
# -----------------------------------------------------------------------
echo "[5/5] Initializing contract with admin..."
stellar contract invoke \
    --id "$CONTRACT_ID" \
    --source "$IDENTITY" \
    --network "$NETWORK" \
    -- \
    initialize \
    --admin "$ADDRESS"
echo "      Initialized ✓"

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------
echo ""
echo "=== Deployment Complete ==="
echo "  Network:     $NETWORK"
echo "  Identity:    $IDENTITY"
echo "  Address:     $ADDRESS"
echo "  Contract ID: $CONTRACT_ID"
echo ""
echo "To interact with the contract:"
echo "  stellar contract invoke --id $CONTRACT_ID --source $IDENTITY --network $NETWORK -- get_admin"
echo ""
echo "To apply a policy:"
echo "  stellar contract invoke --id $CONTRACT_ID --source $IDENTITY --network $NETWORK -- apply_policy --admin $ADDRESS --policy_spec '<JSON>'"
