//! Spend and rate-limit policy invoked by the smart-account framework
//! during `__check_auth` (`install` / `enforce` / `uninstall`).

use soroban_sdk::{
    auth::{Context, ContractContext},
    contract, contractimpl, contracttype, panic_with_error, Address, Env, Symbol, TryFromVal, Vec,
};
use stellar_accounts::smart_account::{ContextRule, ContextRuleType, Signer};

use crate::{emit_auth_decision, AgentAccountError};

#[contracttype]
#[derive(Clone, Debug, PartialEq)]
pub struct SpendPolicyParams {
    pub max_spend_per_period: i128,
    pub max_calls_per_period: u32,
    pub period_ledgers: u32,
    pub expected_method: Symbol,
}

#[contracttype]
#[derive(Clone)]
pub enum PolicyKey {
    SpendCap(Address, u32),
    CallCap(Address, u32),
    Period(Address, u32),
    LastReset(Address, u32),
    Spent(Address, u32),
    Calls(Address, u32),
    Contract(Address, u32),
    Method(Address, u32),
}

pub fn budget_remaining(env: &Env, smart_account: &Address, rule_id: u32) -> i128 {
    let cap: i128 = env
        .storage()
        .persistent()
        .get(&PolicyKey::SpendCap(smart_account.clone(), rule_id))
        .unwrap_or(0);
    reset_if_needed(env, smart_account, rule_id);
    let spent: i128 = env
        .storage()
        .persistent()
        .get(&PolicyKey::Spent(smart_account.clone(), rule_id))
        .unwrap_or(0);
    cap - spent
}

fn reset_if_needed(env: &Env, account: &Address, rule_id: u32) {
    let last_reset: u32 = env
        .storage()
        .persistent()
        .get(&PolicyKey::LastReset(account.clone(), rule_id))
        .unwrap_or(env.ledger().sequence());
    let period: u32 = env
        .storage()
        .persistent()
        .get(&PolicyKey::Period(account.clone(), rule_id))
        .unwrap_or(u32::MAX);
    if env.ledger().sequence() >= last_reset.saturating_add(period) {
        env.storage()
            .persistent()
            .set(&PolicyKey::Spent(account.clone(), rule_id), &0i128);
        env.storage()
            .persistent()
            .set(&PolicyKey::Calls(account.clone(), rule_id), &0u32);
        env.storage().persistent().set(
            &PolicyKey::LastReset(account.clone(), rule_id),
            &env.ledger().sequence(),
        );
    }
}

pub fn install(
    env: &Env,
    params: &SpendPolicyParams,
    context_rule: &ContextRule,
    smart_account: &Address,
) {
    let rule_id = context_rule.id;
    let contract_id = match &context_rule.context_type {
        ContextRuleType::CallContract(addr) => addr.clone(),
        _ => {
            panic_with_error!(env, AgentAccountError::InvalidContext);
        }
    };

    env.storage().persistent().set(
        &PolicyKey::SpendCap(smart_account.clone(), rule_id),
        &params.max_spend_per_period,
    );
    env.storage().persistent().set(
        &PolicyKey::CallCap(smart_account.clone(), rule_id),
        &params.max_calls_per_period,
    );
    env.storage().persistent().set(
        &PolicyKey::Period(smart_account.clone(), rule_id),
        &params.period_ledgers,
    );
    env.storage().persistent().set(
        &PolicyKey::LastReset(smart_account.clone(), rule_id),
        &env.ledger().sequence(),
    );
    env.storage()
        .persistent()
        .set(&PolicyKey::Spent(smart_account.clone(), rule_id), &0i128);
    env.storage()
        .persistent()
        .set(&PolicyKey::Calls(smart_account.clone(), rule_id), &0u32);
    env.storage().persistent().set(
        &PolicyKey::Contract(smart_account.clone(), rule_id),
        &contract_id,
    );
    env.storage().persistent().set(
        &PolicyKey::Method(smart_account.clone(), rule_id),
        &params.expected_method,
    );
}

pub fn uninstall(env: &Env, context_rule: &ContextRule, smart_account: &Address) {
    let rule_id = context_rule.id;
    let a = smart_account.clone();
    env.storage()
        .persistent()
        .remove(&PolicyKey::SpendCap(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::CallCap(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::Period(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::LastReset(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::Spent(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::Calls(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::Contract(a.clone(), rule_id));
    env.storage()
        .persistent()
        .remove(&PolicyKey::Method(a, rule_id));
}

pub fn extract_amount(env: &Env, args: &Vec<soroban_sdk::Val>) -> i128 {
    for i in 0..args.len() {
        if let Some(v) = args.get(i) {
            if let Ok(amount) = i128::try_from_val(env, &v) {
                return amount;
            }
        }
    }
    0
}

pub fn enforce(
    env: &Env,
    context: &Context,
    _authenticated_signers: &Vec<Signer>,
    context_rule: &ContextRule,
    smart_account: &Address,
) {
    let rule_id = context_rule.id;
    let Context::Contract(ContractContext {
        contract,
        fn_name,
        args,
    }) = context
    else {
        emit_auth_decision(
            env,
            Symbol::new(env, "denied"),
            Symbol::new(env, "invalid_context"),
            0,
            rule_id,
            None,
            None,
        );
        panic_with_error!(env, AgentAccountError::InvalidContext);
    };

    let expected_contract: Option<Address> = env
        .storage()
        .persistent()
        .get(&PolicyKey::Contract(smart_account.clone(), rule_id));
    let expected_method: Option<Symbol> = env
        .storage()
        .persistent()
        .get(&PolicyKey::Method(smart_account.clone(), rule_id));

    let amount = extract_amount(env, args);

    if expected_contract.as_ref() != Some(contract) || expected_method.as_ref() != Some(fn_name) {
        emit_auth_decision(
            env,
            Symbol::new(env, "denied"),
            Symbol::new(env, "invalid_context"),
            amount,
            rule_id,
            Some(contract.clone()),
            Some(fn_name.clone()),
        );
        panic_with_error!(env, AgentAccountError::InvalidContext);
    }

    reset_if_needed(env, smart_account, rule_id);

    let cap: i128 = env
        .storage()
        .persistent()
        .get(&PolicyKey::SpendCap(smart_account.clone(), rule_id))
        .unwrap_or(0);
    let spent: i128 = env
        .storage()
        .persistent()
        .get(&PolicyKey::Spent(smart_account.clone(), rule_id))
        .unwrap_or(0);
    let call_cap: u32 = env
        .storage()
        .persistent()
        .get(&PolicyKey::CallCap(smart_account.clone(), rule_id))
        .unwrap_or(0);
    let calls: u32 = env
        .storage()
        .persistent()
        .get(&PolicyKey::Calls(smart_account.clone(), rule_id))
        .unwrap_or(0);

    if calls.saturating_add(1) > call_cap {
        emit_auth_decision(
            env,
            Symbol::new(env, "denied"),
            Symbol::new(env, "rate_limited"),
            amount,
            rule_id,
            Some(contract.clone()),
            Some(fn_name.clone()),
        );
        panic_with_error!(env, AgentAccountError::RateLimited);
    }

    if spent + amount > cap {
        emit_auth_decision(
            env,
            Symbol::new(env, "denied"),
            Symbol::new(env, "over_budget"),
            amount,
            rule_id,
            Some(contract.clone()),
            Some(fn_name.clone()),
        );
        panic_with_error!(env, AgentAccountError::OverBudget);
    }

    env.storage().persistent().set(
        &PolicyKey::Spent(smart_account.clone(), rule_id),
        &(spent + amount),
    );
    env.storage().persistent().set(
        &PolicyKey::Calls(smart_account.clone(), rule_id),
        &(calls + 1),
    );

    emit_auth_decision(
        env,
        Symbol::new(env, "approved"),
        Symbol::new(env, "approved"),
        amount,
        rule_id,
        Some(contract.clone()),
        Some(fn_name.clone()),
    );
}

/// Separate contract instance so `PolicyClient` can call `install`/`enforce`
/// without re-entering the smart account.
#[contract]
pub struct SpendPolicyContract;

#[contractimpl]
impl SpendPolicyContract {
    pub fn install(
        env: Env,
        install_params: SpendPolicyParams,
        context_rule: ContextRule,
        smart_account: Address,
    ) {
        crate::spend::install(&env, &install_params, &context_rule, &smart_account);
    }

    pub fn enforce(
        env: Env,
        context: Context,
        authenticated_signers: Vec<Signer>,
        context_rule: ContextRule,
        smart_account: Address,
    ) {
        crate::spend::enforce(
            &env,
            &context,
            &authenticated_signers,
            &context_rule,
            &smart_account,
        );
    }

    pub fn uninstall(env: Env, context_rule: ContextRule, smart_account: Address) {
        crate::spend::uninstall(&env, &context_rule, &smart_account);
    }

    pub fn remaining_budget(env: Env, smart_account: Address, rule_id: u32) -> i128 {
        crate::spend::budget_remaining(&env, &smart_account, rule_id)
    }
}
