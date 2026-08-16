//! # Soroban Client
//!
//! Stub module for interacting with the Soroban testnet via RPC.
//! All functions here are placeholders for the second pass, which
//! will wire up real Soroban transaction submission and querying.

use anyhow::Result;

/// Configuration for connecting to the Soroban testnet.
#[derive(Debug, Clone)]
pub struct SorobanConfig {
    /// The RPC endpoint URL.
    pub rpc_url: String,
    /// The network passphrase.
    pub network_passphrase: String,
    /// The smart account contract address.
    pub account_contract_id: String,
}

impl Default for SorobanConfig {
    fn default() -> Self {
        Self {
            rpc_url: "https://soroban-testnet.stellar.org".to_string(),
            network_passphrase: "Test SDF Network ; September 2015".to_string(),
            account_contract_id: String::new(),
        }
    }
}

/// Query the remaining budget from the smart account contract.
///
/// # TODO
/// Implement via Soroban RPC `simulateTransaction` or `getContractData`
/// to read the account's spending limit state.
pub async fn query_budget(_config: &SorobanConfig, _rule_id: u32) -> Result<i128> {
    // TODO: Implement real RPC call to get_remaining_budget
    Ok(10_000_000) // Stub: 10M stroops = 1 XLM
}

/// Submit a payment transaction to the smart account.
///
/// # TODO
/// 1. Build the Soroban transaction invoking `record_spend` on the account
/// 2. Sign with the agent's keypair
/// 3. Submit via `sendTransaction` RPC
/// 4. Poll `getTransaction` until confirmed or failed
/// 5. Return the transaction hash and ledger
pub async fn submit_transaction(
    _config: &SorobanConfig,
    _resource_contract: &str,
    _method: &str,
    _amount: i128,
) -> Result<(String, u32)> {
    // TODO: Implement real transaction submission
    Ok(("stub_tx_hash".to_string(), 0))
}

/// Call the underlying resource after payment is confirmed.
///
/// # TODO
/// This may be a second Soroban invocation, an HTTP call to an
/// off-chain API, or a combination. The resource registry entry
/// determines the call mechanism.
pub async fn call_resource(
    _config: &SorobanConfig,
    _resource_contract: &str,
    _method: &str,
    _params: &str,
) -> Result<String> {
    // TODO: Implement real resource invocation
    Ok(r#"{"status": "ok", "data": "stub response"}"#.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_query_budget_stub() {
        let config = SorobanConfig::default();
        let budget = query_budget(&config, 1).await.unwrap();
        assert_eq!(budget, 10_000_000);
    }

    #[tokio::test]
    async fn test_submit_transaction_stub() {
        let config = SorobanConfig::default();
        let (hash, _ledger) = submit_transaction(&config, "CABC", "transfer", 100)
            .await
            .unwrap();
        assert!(!hash.is_empty());
    }
}
