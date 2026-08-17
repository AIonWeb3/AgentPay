//! # Unit Tests for AgentPay Smart Account
//!
//! Tests for `apply_policy`, authorized/denied spend flows, and
//! audit event emission.

#![cfg(test)]

use soroban_sdk::{
    testutils::{Address as _, Events},
    vec, Address, Env, IntoVal, Symbol, Vec,
};

use crate::{
    policy_spec::{AllowedContract, PolicySpec},
    AgentAccountContract, AgentAccountContractClient,
};

/// Helper: create a test environment and deploy the contract.
fn setup() -> (Env, AgentAccountContractClient<'static>, Address) {
    let env = Env::default();
    env.mock_all_auths();

    let contract_id = env.register(AgentAccountContract, ());
    let client = AgentAccountContractClient::new(&env, &contract_id);
    let admin = Address::generate(&env);

    client.initialize(&admin);

    (env, client, admin)
}

/// Helper: create a sample PolicySpec with one allowed contract.
fn sample_policy(env: &Env, vendor: &Address, cap: i128, period: u32) -> PolicySpec {
    let mut methods: Vec<Symbol> = Vec::new(env);
    methods.push_back(Symbol::new(env, "get_data"));

    let allowed = AllowedContract {
        contract_id: vendor.clone(),
        allowed_methods: methods,
        max_spend_per_period: cap,
        max_calls_per_period: 100, // Default call limit for tests
    };

    let mut contracts: Vec<AllowedContract> = Vec::new(env);
    contracts.push_back(allowed);

    PolicySpec {
        allowed_contracts: contracts,
        period_ledgers: period,
    }
}

// -----------------------------------------------------------------------
// Test: apply_policy installs rules correctly
// -----------------------------------------------------------------------

#[test]
fn test_apply_policy() {
    let (env, client, admin) = setup();
    let vendor = Address::generate(&env);

    let spec = sample_policy(&env, &vendor, 10_000_000, 17280);
    client.apply_policy(&admin, &spec);

    // Verify rule count is 1
    assert_eq!(client.get_rule_count(), 1);

    // Verify remaining budget equals the cap (nothing spent yet)
    let remaining = client.get_remaining_budget(&1u32);
    assert_eq!(remaining, 10_000_000);
}

// -----------------------------------------------------------------------
// Test: authorized call under the spend cap
// -----------------------------------------------------------------------

#[test]
fn test_authorized_call_under_cap() {
    let (env, client, admin) = setup();
    let vendor = Address::generate(&env);

    let spec = sample_policy(&env, &vendor, 10_000_000, 17280);
    client.apply_policy(&admin, &spec);

    // Record a spend of 5,000,000 (under the 10,000,000 cap)
    let method = Symbol::new(&env, "get_data");
    let approved = client.record_spend(&admin, &1u32, &vendor, &method, &5_000_000i128);
    assert!(approved);

    // Remaining budget should be 5,000,000
    let remaining = client.get_remaining_budget(&1u32);
    assert_eq!(remaining, 5_000_000);


}

// -----------------------------------------------------------------------
// Test: denied call over the spend cap
// -----------------------------------------------------------------------

#[test]
fn test_denied_call_over_cap() {
    let (env, client, admin) = setup();
    let vendor = Address::generate(&env);

    let spec = sample_policy(&env, &vendor, 10_000_000, 17280);
    client.apply_policy(&admin, &spec);

    // Try to spend 15,000,000 (over the 10,000,000 cap)
    let method = Symbol::new(&env, "get_data");
    let approved = client.record_spend(&admin, &1u32, &vendor, &method, &15_000_000i128);
    assert!(!approved, "Expected spend over cap to be denied");

    // Remaining budget should still be full (spend was rejected)
    let remaining = client.get_remaining_budget(&1u32);
    assert_eq!(remaining, 10_000_000);


}

// -----------------------------------------------------------------------
// Test: double initialization fails
// -----------------------------------------------------------------------

#[test]
fn test_double_initialize_fails() {
    let (env, client, admin) = setup();
    let result = client.try_initialize(&admin);
    assert!(result.is_err(), "Double initialization should fail");
}

// -----------------------------------------------------------------------
// Test: apply_policy with empty spec fails
// -----------------------------------------------------------------------

#[test]
fn test_empty_policy_fails() {
    let (env, client, admin) = setup();
    let spec = PolicySpec {
        allowed_contracts: Vec::new(&env),
        period_ledgers: 17280,
    };
    let result = client.try_apply_policy(&admin, &spec);
    assert!(result.is_err(), "Empty policy should fail");
}

// -----------------------------------------------------------------------
// Test: cumulative spending tracks correctly
// -----------------------------------------------------------------------

#[test]
fn test_cumulative_spending() {
    let (env, client, admin) = setup();
    let vendor = Address::generate(&env);

    let spec = sample_policy(&env, &vendor, 10_000_000, 17280);
    client.apply_policy(&admin, &spec);

    // Spend 3M, then 4M (total 7M, under 10M cap)
    let method = Symbol::new(&env, "get_data");
    assert!(client.record_spend(&admin, &1u32, &vendor, &method, &3_000_000i128));
    assert!(client.record_spend(&admin, &1u32, &vendor, &method, &4_000_000i128));
    assert_eq!(client.get_remaining_budget(&1u32), 3_000_000);

    // Next spend of 4M would push to 11M — denied
    assert!(!client.record_spend(&admin, &1u32, &vendor, &method, &4_000_000i128));
    assert_eq!(client.get_remaining_budget(&1u32), 3_000_000);
}

// -----------------------------------------------------------------------
// Test: denied call over the rate limit
// -----------------------------------------------------------------------

#[test]
fn test_denied_call_over_rate_limit() {
    let (env, client, admin) = setup();
    let vendor = Address::generate(&env);

    let mut spec = sample_policy(&env, &vendor, 10_000_000, 17280);
    // Overwrite the default 100 call limit to 2 for this test
    let mut methods: Vec<Symbol> = Vec::new(&env);
    methods.push_back(Symbol::new(&env, "get_data"));
    
    let mut contracts: Vec<AllowedContract> = Vec::new(&env);
    contracts.push_back(AllowedContract {
        contract_id: vendor.clone(),
        allowed_methods: methods,
        max_spend_per_period: 10_000_000,
        max_calls_per_period: 2,
    });
    spec.allowed_contracts = contracts;
    
    client.apply_policy(&admin, &spec);

    let method = Symbol::new(&env, "get_data");
    // First call works
    assert!(client.record_spend(&admin, &1u32, &vendor, &method, &100i128));
    // Second call works
    assert!(client.record_spend(&admin, &1u32, &vendor, &method, &100i128));
    // Third call should fail due to rate limit, even though under spend cap
    assert!(!client.record_spend(&admin, &1u32, &vendor, &method, &100i128));
}

// -----------------------------------------------------------------------
// Test: context-rule scoping per vendor
// -----------------------------------------------------------------------

#[test]
fn test_scoping_per_vendor() {
    let (env, client, admin) = setup();
    let vendor_a = Address::generate(&env);
    let vendor_b = Address::generate(&env);

    let method_a = Symbol::new(&env, "get_data_a");
    let method_b = Symbol::new(&env, "get_data_b");

    let mut contracts: Vec<AllowedContract> = Vec::new(&env);
    contracts.push_back(AllowedContract {
        contract_id: vendor_a.clone(),
        allowed_methods: vec![&env, method_a.clone()],
        max_spend_per_period: 10_000_000,
        max_calls_per_period: 100,
    });
    contracts.push_back(AllowedContract {
        contract_id: vendor_b.clone(),
        allowed_methods: vec![&env, method_b.clone()],
        max_spend_per_period: 5_000_000,
        max_calls_per_period: 100,
    });

    let spec = PolicySpec {
        allowed_contracts: contracts,
        period_ledgers: 17280,
    };

    client.apply_policy(&admin, &spec);

    // Rule 1 is vendor A, Rule 2 is vendor B
    assert_eq!(client.get_rule_count(), 2);

    // A call against Vendor A's rule (rule 1) using Vendor B's contract ID should fail
    // even though the amount is well within the cap (100 < 10M)
    assert!(!client.record_spend(&admin, &1u32, &vendor_b, &method_a, &100i128));

    // A call against Vendor A's rule using Vendor A's contract but Vendor B's method should fail
    assert!(!client.record_spend(&admin, &1u32, &vendor_a, &method_b, &100i128));

    // A proper call to Vendor A works
    assert!(client.record_spend(&admin, &1u32, &vendor_a, &method_a, &100i128));
}
