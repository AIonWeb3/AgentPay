//! Least-privilege checks shared by MCP pay_and_call.

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PolicyOutcome {
    Allow { remaining: i128 },
    Denied { reason: String },
    InsufficientBudget { required: i128, available: i128 },
}

pub fn evaluate_call(
    allowlisted: bool,
    amount: i128,
    spent: i128,
    max_spend: i128,
    calls: u32,
    max_calls: u32,
) -> PolicyOutcome {
    let remaining = max_spend - spent;
    if !allowlisted {
        return PolicyOutcome::Denied {
            reason: "not_allowlisted".to_string(),
        };
    }
    if calls.saturating_add(1) > max_calls {
        return PolicyOutcome::Denied {
            reason: format!("rate limited: {calls}/{max_calls} calls this period"),
        };
    }
    if spent + amount > max_spend {
        return PolicyOutcome::InsufficientBudget {
            required: amount,
            available: remaining,
        };
    }
    PolicyOutcome::Allow {
        remaining: remaining - amount,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn under_cap() {
        let out = evaluate_call(true, 50, 0, 1000, 0, 10);
        assert_eq!(out, PolicyOutcome::Allow { remaining: 950 });
    }

    #[test]
    fn over_cap() {
        let out = evaluate_call(true, 1500, 0, 1000, 0, 10);
        assert!(matches!(out, PolicyOutcome::InsufficientBudget { .. }));
    }
}
