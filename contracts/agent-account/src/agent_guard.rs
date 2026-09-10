//! Cross-contract client for [AgentGuard](https://github.com/AIonWeb3/AgentGuard).
//!
//! `Role` matches AgentGuard's ABI (`Basic < Premium < Admin`).
//! `verify_agent` is a pure read (no auth, no writes).

use soroban_sdk::{contracttype, Address, Env, IntoVal, Symbol};

/// Privilege level required by AgentGuard's `verify_agent`.
#[contracttype]
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)]
#[repr(u32)]
pub enum Role {
    Basic = 0,
    Premium = 1,
    Admin = 2,
}

/// Invoke AgentGuard `verify_agent(agent_id, required_role) -> bool`.
pub fn verify_agent(env: &Env, guard: &Address, agent_id: &Address, required_role: &Role) -> bool {
    env.invoke_contract(
        guard,
        &Symbol::new(env, "verify_agent"),
        soroban_sdk::vec![env, agent_id.into_val(env), required_role.into_val(env)],
    )
}
