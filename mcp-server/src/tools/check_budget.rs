//! # Check Budget Tool
//!
//! Reads remaining allowance from `AGENTPAY_STATE` JSON when set,
//! otherwise a local default snapshot.

pub use crate::account_state::BudgetStatus;
use crate::account_state::load_budget;

pub fn check_budget() -> BudgetStatus {
    load_budget()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::account_state::load_budget_from_path;
    use std::io::Write;

    #[test]
    fn test_check_budget_default() {
        let status = BudgetStatus::default();
        assert_eq!(status.remaining_stroops, 10_000_000);
        assert_eq!(status.remaining_xlm, 1.0);
        assert!(status.rule_count > 0);
    }

    #[test]
    fn test_check_budget_from_state_file() {
        let dir = std::env::temp_dir();
        let path = dir.join("agentpay-budget-test.json");
        let mut f = std::fs::File::create(&path).unwrap();
        write!(
            f,
            r#"{{"remaining_stroops": 2500, "remaining_xlm": 0.0, "period_ledgers": 720, "rule_count": 2}}"#
        )
        .unwrap();
        let status = load_budget_from_path(&path);
        assert_eq!(status.remaining_stroops, 2500);
        assert_eq!(status.remaining_xlm, 0.00025);
        assert_eq!(status.rule_count, 2);
        let _ = std::fs::remove_file(path);
        let _ = check_budget();
    }
}
