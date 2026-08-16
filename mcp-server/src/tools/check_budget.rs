//! # Check Budget Tool
//!
//! MCP tool that queries the smart account's remaining spending allowance.
//! First pass: returns hardcoded stub data. Second pass will query testnet.

use serde::Serialize;

/// Budget status response.
#[derive(Debug, Serialize)]
pub struct BudgetStatus {
    /// Remaining spend allowance in stroops.
    pub remaining_stroops: i128,
    /// Human-readable remaining in XLM.
    pub remaining_xlm: f64,
    /// The period in ledgers over which this budget applies.
    pub period_ledgers: u32,
    /// Number of context rules being tracked.
    pub rule_count: u32,
}

/// Check the remaining budget.
///
/// # First Pass
/// Returns hardcoded stub data. The agent gets a realistic-looking
/// response to develop against.
///
/// # TODO
/// Query the smart account contract's `get_remaining_budget` on testnet
/// via the Soroban RPC client in `soroban_client.rs`.
pub fn check_budget() -> BudgetStatus {
    // TODO: Replace with real testnet query via soroban_client::query_budget()
    BudgetStatus {
        remaining_stroops: 10_000_000,
        remaining_xlm: 1.0,
        period_ledgers: 17280,
        rule_count: 3,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_budget_stub() {
        let status = check_budget();
        assert_eq!(status.remaining_stroops, 10_000_000);
        assert_eq!(status.remaining_xlm, 1.0);
        assert!(status.rule_count > 0);
    }
}
