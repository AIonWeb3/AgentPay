"""
PolicySpec Schema — Shared Source of Truth

Pydantic models defining the JSON shape used by both the policy generator
and the Soroban contract's `apply_policy` entrypoint. The contract uses
equivalent `#[contracttype]` structs in `policy_spec.rs`.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class AllowedMethod(BaseModel):
    """A single method the agent is permitted to call on a contract."""

    name: str = Field(
        ..., description="The method name (e.g., 'get_weather', 'transfer')"
    )


class AllowedContract(BaseModel):
    """A vendor/resource contract with its allowed methods and spend cap."""

    contract_id: str = Field(
        ...,
        description="The Soroban contract address (C... format)",
    )
    allowed_methods: List[AllowedMethod] = Field(
        ...,
        description="Methods the agent is allowed to call on this contract",
    )
    max_spend_per_period: int = Field(
        ...,
        ge=0,
        description="Maximum spend in stroops per period for this contract",
    )


class PolicySpec(BaseModel):
    """
    Top-level policy specification.

    Produced by `generate_policy.py`, consumed by the smart account's
    `apply_policy` entrypoint (after conversion to Soroban-native types).
    """

    allowed_contracts: List[AllowedContract] = Field(
        ...,
        min_length=1,
        description="List of vendor contracts the agent may interact with",
    )
    period_ledgers: int = Field(
        default=17280,
        ge=1,
        description="Rolling window size in ledger sequences (~17280 ≈ 1 day)",
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp when this policy was generated",
    )
    source_tx_count: int = Field(
        default=0,
        ge=0,
        description="Number of transactions in the source log used to generate this policy",
    )


# ---------------------------------------------------------------------------
# Example / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    example = PolicySpec(
        allowed_contracts=[
            AllowedContract(
                contract_id="CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC",
                allowed_methods=[AllowedMethod(name="get_weather")],
                max_spend_per_period=50_000,
            ),
            AllowedContract(
                contract_id="CBQHNAXSI55GX2GN6D67GK7BHVPSLJUGZQEU7WJ5LKR5PNUCGLIMAO4K",
                allowed_methods=[AllowedMethod(name="get_price")],
                max_spend_per_period=100_000,
            ),
        ],
        period_ledgers=17280,
        source_tx_count=42,
    )
    print(example.model_dump_json(indent=2))
