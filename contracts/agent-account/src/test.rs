//! Unit tests: auth-path deny/approve, per-vendor isolation, rolling window,
//! rate limits, and `auth_decision` events.

#![cfg(test)]

extern crate std;

use soroban_sdk::{
    auth::{Context, ContractContext},
    testutils::{Address as _, Events, Ledger},
    vec, Address, BytesN, Env, IntoVal, Map, Symbol, Val, Vec,
};
use stellar_accounts::smart_account::AuthPayload;

use crate::{
    agent_guard::Role,
    policy_spec::{AllowedContract, PolicySpec},
    spend::SpendPolicyContract,
    AgentAccountContract, AgentAccountContractClient,
};

#[soroban_sdk::contract]
pub struct MockAgentGuard;

#[soroban_sdk::contractimpl]
impl MockAgentGuard {
    pub fn verify_agent(_env: soroban_sdk::Env, _agent_id: Address, _required_role: Role) -> bool {
        true
    }
}

#[soroban_sdk::contract]
pub struct DenyingAgentGuard;

#[soroban_sdk::contractimpl]
impl DenyingAgentGuard {
    pub fn verify_agent(_env: soroban_sdk::Env, _agent_id: Address, _required_role: Role) -> bool {
        false
    }
}

fn setup() -> (Env, AgentAccountContractClient<'static>, Address, Address) {
    let env = Env::default();
    env.mock_all_auths();

    let policy = env.register(SpendPolicyContract, ());
    let account = env.register(AgentAccountContract, ());
    let client = AgentAccountContractClient::new(&env, &account);
    let admin = Address::generate(&env);
    client.initialize(&admin);
    client.set_spend_policy(&admin, &policy);
    (env, client, admin, account)
}

fn sample_policy(env: &Env, vendor: &Address, cap: i128, period: u32) -> PolicySpec {
    sample_policy_calls(env, vendor, cap, period, 100)
}

fn sample_policy_calls(
    env: &Env,
    vendor: &Address,
    cap: i128,
    period: u32,
    max_calls: u32,
) -> PolicySpec {
    let mut methods: Vec<Symbol> = Vec::new(env);
    methods.push_back(Symbol::new(env, "get_data"));
    let allowed = AllowedContract {
        contract_id: vendor.clone(),
        allowed_methods: methods,
        max_spend_per_period: cap,
        max_calls_per_period: max_calls,
    };
    let mut contracts: Vec<AllowedContract> = Vec::new(env);
    contracts.push_back(allowed);
    PolicySpec {
        allowed_contracts: contracts,
        period_ledgers: period,
    }
}

fn try_auth(
    env: &Env,
    account: &Address,
    vendor: &Address,
    method: Symbol,
    amount: i128,
    rule_id: u32,
) -> Result<(), u32> {
    let mut args: Vec<Val> = Vec::new(env);
    args.push_back(amount.into_val(env));
    let ctx = Context::Contract(ContractContext {
        contract: vendor.clone(),
        fn_name: method,
        args,
    });
    let payload = AuthPayload {
        signers: Map::new(env),
        context_rule_ids: vec![env, rule_id],
    };
    let hash = BytesN::<32>::from_array(env, &[7u8; 32]);
    match env.try_invoke_contract_check_auth::<stellar_accounts::smart_account::SmartAccountError>(
        account,
        &hash,
        payload.into_val(env),
        &vec![env, ctx],
    ) {
        Ok(()) => Ok(()),
        Err(Ok(_)) => Err(1),
        Err(Err(soroban_sdk::InvokeError::Contract(code))) => Err(code),
        Err(Err(_)) => Err(0),
    }
}

fn has_auth_reason(env: &Env, reason: &str) -> bool {
    use soroban_sdk::xdr::ContractEventBody;
    env.events().all().events().iter().any(|ev| {
        let ContractEventBody::V0(body) = &ev.body;
        std::format!("{body:?}").contains(reason)
    })
}

#[test]
fn test_apply_policy() {
    let (env, client, admin, _account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    assert_eq!(client.get_rule_count(), 1);
    assert_eq!(client.get_remaining_budget(&0u32), 10_000_000);
}

#[test]
fn test_authorized_call_under_cap() {
    let (env, client, admin, account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method, 5_000_000, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 5_000_000);
}

#[test]
fn test_denied_call_over_cap() {
    let (env, client, admin, account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    let method = Symbol::new(&env, "get_data");
    assert_eq!(
        try_auth(&env, &account, &vendor, method, 15_000_000, 0).unwrap_err(),
        5
    );
    assert_eq!(client.get_remaining_budget(&0u32), 10_000_000);
}

#[test]
fn test_double_initialize_fails() {
    let (_env, client, admin, _account) = setup();
    assert!(client.try_initialize(&admin).is_err());
}

#[test]
fn test_empty_policy_fails() {
    let (env, client, admin, _account) = setup();
    let spec = PolicySpec {
        allowed_contracts: Vec::new(&env),
        period_ledgers: 17280,
    };
    assert!(client.try_apply_policy(&admin, &spec).is_err());
}

#[test]
fn test_cumulative_spending() {
    let (env, client, admin, account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method.clone(), 3_000_000, 0).is_ok());
    assert!(try_auth(&env, &account, &vendor, method.clone(), 4_000_000, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 3_000_000);
    assert!(try_auth(&env, &account, &vendor, method, 4_000_000, 0).is_err());
    assert_eq!(client.get_remaining_budget(&0u32), 3_000_000);
}

#[test]
fn test_rolling_window_reset() {
    let env = Env::default();
    env.mock_all_auths();
    env.ledger().set_sequence_number(100);
    let policy = env.register(SpendPolicyContract, ());
    let account = env.register(AgentAccountContract, ());
    let client = AgentAccountContractClient::new(&env, &account);
    let admin = Address::generate(&env);
    client.initialize(&admin);
    client.set_spend_policy(&admin, &policy);
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 100, 100));
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method.clone(), 60, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 40);
    assert!(try_auth(&env, &account, &vendor, method.clone(), 50, 0).is_err());
    env.ledger().set_sequence_number(201);
    assert_eq!(client.get_remaining_budget(&0u32), 100);
    assert!(try_auth(&env, &account, &vendor, method, 80, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 20);
}

#[test]
fn test_denied_call_over_rate_limit() {
    let (env, client, admin, account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(
        &admin,
        &sample_policy_calls(&env, &vendor, 10_000_000, 17280, 2),
    );
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method.clone(), 100, 0).is_ok());
    assert!(try_auth(&env, &account, &vendor, method.clone(), 100, 0).is_ok());
    assert_eq!(
        try_auth(&env, &account, &vendor, method, 100, 0).unwrap_err(),
        6
    );
}

#[test]
fn test_scoping_per_vendor() {
    let (env, client, admin, account) = setup();
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
    client.apply_policy(
        &admin,
        &PolicySpec {
            allowed_contracts: contracts,
            period_ledgers: 17280,
        },
    );
    assert_eq!(client.get_rule_count(), 2);

    // Vendor B with vendor A's rule → context type / policy deny
    assert!(try_auth(&env, &account, &vendor_b, method_a.clone(), 100, 0).is_err());
    // Vendor A contract with B's method on A's rule
    assert!(try_auth(&env, &account, &vendor_a, method_b.clone(), 100, 0).is_err());
    assert!(try_auth(&env, &account, &vendor_a, method_a, 100, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 9_999_900);
    assert_eq!(client.get_remaining_budget(&1u32), 5_000_000);
}

#[test]
fn test_auth_decision_events_approved_and_denied() {
    let (env, client, admin, account) = setup();
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 100, 17280));
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method.clone(), 10, 0).is_ok());
    assert!(has_auth_reason(&env, "approved"));
    assert_eq!(
        try_auth(&env, &account, &vendor, method, 200, 0).unwrap_err(),
        5
    );
}

#[test]
fn test_agent_guard_allows_then_spend() {
    let (env, client, admin, account) = setup();
    let guard = env.register(MockAgentGuard, ());
    client.set_agent_guard(&admin, &guard, &Role::Basic);
    assert!(client.get_agent_guard().is_some());
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    let method = Symbol::new(&env, "get_data");
    assert!(try_auth(&env, &account, &vendor, method, 1_000_000, 0).is_ok());
    assert_eq!(client.get_remaining_budget(&0u32), 9_000_000);
}

#[test]
fn test_agent_guard_denies_before_spend() {
    let (env, client, admin, account) = setup();
    let guard = env.register(DenyingAgentGuard, ());
    client.set_agent_guard(&admin, &guard, &Role::Premium);
    let vendor = Address::generate(&env);
    client.apply_policy(&admin, &sample_policy(&env, &vendor, 10_000_000, 17280));
    let method = Symbol::new(&env, "get_data");
    assert_eq!(
        try_auth(&env, &account, &vendor, method, 1_000_000, 0).unwrap_err(),
        8
    );
    assert_eq!(client.get_remaining_budget(&0u32), 10_000_000);
}
