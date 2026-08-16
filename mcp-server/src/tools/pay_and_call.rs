//! # Pay and Call Tool
//!
//! MCP tool that builds and submits a Soroban transaction authorized by
//! the agent's smart account, waits for confirmation, then calls the
//! underlying resource. Returns typed errors for policy denial,
//! insufficient budget, and resource call failure.

use serde::Serialize;
use std::fmt;

// ---------------------------------------------------------------------------
// Typed errors — the agent gets a legible reason, not a panic
// ---------------------------------------------------------------------------

/// Errors that can occur during pay_and_call.
#[derive(Debug)]
pub enum PayAndCallError {
    /// The smart account's spending policy denied the transaction.
    PolicyDenied(String),
    /// The agent's budget is insufficient for this call.
    InsufficientBudget {
        required: i128,
        available: i128,
    },
    /// The underlying resource call failed.
    ResourceCallFailed(String),
    /// The resource ID was not found in the registry.
    ResourceNotFound(String),
    /// A transient network error occurred (retryable).
    TransientError(String),
}

impl fmt::Display for PayAndCallError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::PolicyDenied(reason) => write!(f, "Policy denied: {reason}"),
            Self::InsufficientBudget { required, available } => {
                write!(
                    f,
                    "Insufficient budget: required {required} stroops, available {available} stroops"
                )
            }
            Self::ResourceCallFailed(reason) => write!(f, "Resource call failed: {reason}"),
            Self::ResourceNotFound(id) => write!(f, "Resource not found: {id}"),
            Self::TransientError(msg) => write!(f, "Transient error (retryable): {msg}"),
        }
    }
}

impl std::error::Error for PayAndCallError {}

/// Successful response from pay_and_call.
#[derive(Debug, Serialize)]
pub struct PayAndCallResult {
    /// The Soroban transaction hash.
    pub tx_hash: String,
    /// The ledger sequence where the transaction was confirmed.
    pub ledger: u32,
    /// The amount spent in stroops.
    pub amount_spent: i128,
    /// The response from the underlying resource.
    pub resource_response: String,
}

/// Pay for and call a resource.
///
/// # First Pass
/// Returns a hardcoded stub response simulating a successful call.
/// Validates the resource_id against the registry but does not submit
/// real transactions.
///
/// # TODO
/// 1. Build the Soroban transaction via `soroban_client::submit_transaction()`
/// 2. Wait for confirmation with bounded retry on transient failure
/// 3. Call the underlying resource via `soroban_client::call_resource()`
/// 4. Return the real transaction hash and resource response
///
/// # Arguments
/// * `resource_id` - The ID of the resource to call (from registry).
/// * `params` - JSON-encoded parameters to pass to the resource.
///
/// # Errors
/// Returns typed errors for policy denial, insufficient budget,
/// resource not found, and resource call failure.
pub fn pay_and_call(
    resource_id: &str,
    params: &str,
) -> Result<PayAndCallResult, PayAndCallError> {
    // Validate the resource exists in the registry
    let resources = super::discover::load_registry();
    let resource = resources
        .iter()
        .find(|r| r.id == resource_id)
        .ok_or_else(|| PayAndCallError::ResourceNotFound(resource_id.to_string()))?;

    // TODO: Check budget via soroban_client::query_budget()
    // TODO: Build and submit Soroban transaction
    // TODO: Wait for confirmation with bounded retry (max 3 attempts)
    // TODO: Call the underlying resource
    // TODO: Record the spend on-chain

    // Stub response: simulate a successful call
    Ok(PayAndCallResult {
        tx_hash: "stub_tx_abc123def456".to_string(),
        ledger: 12345678,
        amount_spent: resource.price as i128,
        resource_response: format!(
            "{{\"status\": \"ok\", \"resource\": \"{}\", \"params\": {}}}",
            resource.name, params
        ),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pay_and_call_stub_success() {
        let result = pay_and_call("weather-oracle", "{}");
        assert!(result.is_ok());
        let res = result.unwrap();
        assert_eq!(res.amount_spent, 50);
        assert!(res.tx_hash.starts_with("stub_"));
    }

    #[test]
    fn test_pay_and_call_not_found() {
        let result = pay_and_call("nonexistent-resource", "{}");
        assert!(result.is_err());
        match result.unwrap_err() {
            PayAndCallError::ResourceNotFound(id) => {
                assert_eq!(id, "nonexistent-resource");
            }
            other => panic!("Expected ResourceNotFound, got: {other}"),
        }
    }
}
