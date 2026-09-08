"""In-memory smart account that mirrors contracts/agent-account enforcement."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from store import (
    clear_audit,
    clear_rules,
    connect,
    import_registry,
    insert_audit,
    insert_policy,
    insert_rule,
    insert_session,
    list_audit,
    list_resources,
    migrate,
    update_rule_window,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "policy-generator"))
sys.path.insert(0, str(ROOT / "scripts"))

from generate_policy import score_transactions  # noqa: E402
from simulate_agent import generate_transaction_log  # noqa: E402

REGISTRY_PATH = ROOT / "registry" / "resources.json"

RESOURCE_RESPONSES = {
    "weather-oracle": {
        "location": "San Francisco, CA",
        "temp_c": 18.4,
        "humidity": 62,
        "conditions": "partly cloudy",
        "source": "weather-oracle",
        "as_of": "live",
    },
    "price-feed": {
        "asset": "XLM",
        "usd": 0.1124,
        "change_24h": 0.031,
        "volume_24h": 84200000,
        "exchanges": 5,
    },
    "ai-inference": {
        "model": "agentpay-demo-v1",
        "output": "Least-privilege policy recommended: allow weather + price feeds; cap inference separately.",
        "tokens": 128,
        "verified": True,
    },
}


def _tx_hash(seed: str) -> str:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return digest[:16].upper()


@dataclass
class RuleState:
    rule_id: int
    resource_id: str
    contract_id: str
    method: str
    name: str
    price: int
    max_spend_per_period: int
    max_calls_per_period: int
    spent: int = 0
    calls: int = 0
    last_reset: int = 0


@dataclass
class AuditEvent:
    ts: float
    decision: str
    reason: str
    resource_id: str
    amount: int
    remaining: int
    tx_hash: str | None = None
    ledger: int | None = None


@dataclass
class AccountState:
    ledger: int = 12_400_000
    period_ledgers: int = 17_280
    source_tx_count: int = 0
    generated_at: str = ""
    rules: list[RuleState] = field(default_factory=list)
    audit: list[AuditEvent] = field(default_factory=list)
    tx_log: list[dict[str, Any]] = field(default_factory=list)
    policy: dict[str, Any] = field(default_factory=dict)


class AgentPayEngine:
    def __init__(
        self,
        db_path: str | Path | None = None,
        session_id: str = "demo",
    ) -> None:
        self.session_id = session_id
        self.conn = None
        if db_path is not None:
            self.conn = connect(db_path)
            migrate(self.conn)
        self.resources: list[dict[str, Any]] = json.loads(REGISTRY_PATH.read_text())
        if self.conn is not None:
            import_registry(self.conn, self.resources)
            self.resources = [dict(row) for row in list_resources(self.conn)]
        self.state = AccountState()
        self.reset_demo()

    def _persist_session(self) -> None:
        if self.conn is None:
            return
        insert_session(
            self.conn,
            self.session_id,
            ledger=self.state.ledger,
            period_ledgers=self.state.period_ledgers,
        )

    def reset_demo(self) -> dict[str, Any]:
        self.state = AccountState()
        self._persist_session()
        if self.conn is not None:
            clear_audit(self.conn, self.session_id)
        self.state.tx_log = generate_transaction_log(
            num_transactions=75, span_hours=24, seed=42
        )
        spec = score_transactions(self.state.tx_log)
        self.state.policy = json.loads(spec.model_dump_json())
        self.state.period_ledgers = spec.period_ledgers
        self.state.source_tx_count = spec.source_tx_count
        self.state.generated_at = spec.generated_at

        by_contract = {c.contract_id: c for c in spec.allowed_contracts}
        if self.conn is not None:
            clear_rules(self.conn, self.session_id)
        for i, resource in enumerate(self.resources, start=1):
            contract = by_contract.get(resource["contract_id"])
            if not contract:
                continue
            rule = RuleState(
                rule_id=i,
                resource_id=resource["id"],
                contract_id=resource["contract_id"],
                method=resource["method"],
                name=resource["name"],
                price=int(resource["price"]),
                max_spend_per_period=contract.max_spend_per_period,
                max_calls_per_period=contract.max_calls_per_period,
                last_reset=self.state.ledger,
            )
            self.state.rules.append(rule)
            if self.conn is not None:
                insert_rule(
                    self.conn,
                    rule_id=rule.rule_id,
                    session_id=self.session_id,
                    resource_id=rule.resource_id,
                    contract_id=rule.contract_id,
                    method=rule.method,
                    name=rule.name,
                    price=rule.price,
                    max_spend_per_period=rule.max_spend_per_period,
                    max_calls_per_period=rule.max_calls_per_period,
                    spent=rule.spent,
                    calls=rule.calls,
                    last_reset=rule.last_reset,
                )
        self._audit("applied", "policy_installed", "", 0, self.total_remaining())
        self._persist_session()
        if self.conn is not None:
            insert_policy(
                self.conn,
                self.session_id,
                spec.model_dump_json(),
                source_tx_count=spec.source_tx_count,
                period_ledgers=spec.period_ledgers,
                generated_at=spec.generated_at,
            )
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "account": "GAGENTPAYDEMOACCOUNTXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "network": "Test SDF Network ; September 2015",
            "ledger": self.state.ledger,
            "period_ledgers": self.state.period_ledgers,
            "source_tx_count": self.state.source_tx_count,
            "generated_at": self.state.generated_at,
            "rule_count": len(self.state.rules),
            "remaining_stroops": self.total_remaining(),
            "remaining_xlm": self.total_remaining() / 10_000_000,
            "rules": [self._rule_view(r) for r in self.state.rules],
            "policy": self.state.policy,
            "audit": self._audit_view(),
            "tx_log": self.state.tx_log,
            "resources": self.resources,
        }

    def total_remaining(self) -> int:
        return sum(max(0, r.max_spend_per_period - r.spent) for r in self.state.rules)

    def discover(self, query: str) -> list[dict[str, Any]]:
        q = query.lower().strip()
        results = []
        for r in self.resources:
            hay = f"{r['id']} {r['name']} {r['description']}".lower()
            if not q or q in hay:
                results.append(r)
        return results

    def pay_and_call(self, resource_id: str, params: str = "{}") -> dict[str, Any]:
        resource = next((r for r in self.resources if r["id"] == resource_id), None)
        if resource is None:
            raise KeyError(resource_id)
        rule = next((r for r in self.state.rules if r.resource_id == resource_id), None)
        if rule is None:
            self._audit("denied", "not_allowlisted", resource_id, 0, self.total_remaining())
            return {
                "ok": False,
                "error": "PolicyDenied",
                "reason": f"{resource_id} is not on the allowlist",
            }

        amount = int(resource["price"])
        remaining = rule.max_spend_per_period - rule.spent
        if rule.calls + 1 > rule.max_calls_per_period:
            self._audit("denied", "rate_limited", resource_id, amount, remaining)
            return {
                "ok": False,
                "error": "PolicyDenied",
                "reason": f"rate limited: {rule.calls}/{rule.max_calls_per_period} calls this period",
            }
        if rule.spent + amount > rule.max_spend_per_period:
            self._audit("denied", "over_budget", resource_id, amount, remaining)
            return {
                "ok": False,
                "error": "InsufficientBudget",
                "reason": (
                    f"required {amount} stroops, remaining {remaining} stroops "
                    f"on {rule.name}"
                ),
                "required": amount,
                "available": remaining,
            }

        self.state.ledger += 1
        rule.spent += amount
        rule.calls += 1
        if self.conn is not None:
            update_rule_window(
                self.conn,
                self.session_id,
                resource_id,
                spent=rule.spent,
                calls=rule.calls,
                last_reset=rule.last_reset,
            )
        tx_hash = _tx_hash(f"{self.state.ledger}:{resource_id}:{rule.spent}")
        payload = dict(RESOURCE_RESPONSES.get(resource_id, {"status": "ok"}))
        payload["params"] = json.loads(params) if params.strip() else {}
        remaining = rule.max_spend_per_period - rule.spent
        self._audit(
            "approved",
            "under_cap",
            resource_id,
            amount,
            remaining,
            tx_hash=tx_hash,
            ledger=self.state.ledger,
        )
        return {
            "ok": True,
            "tx_hash": tx_hash,
            "ledger": self.state.ledger,
            "amount_spent": amount,
            "resource_response": payload,
            "remaining": remaining,
        }

    def _rule_view(self, rule: RuleState) -> dict[str, Any]:
        remaining = max(0, rule.max_spend_per_period - rule.spent)
        return {
            **rule.__dict__,
            "remaining": remaining,
            "used_pct": round(100 * rule.spent / max(rule.max_spend_per_period, 1), 1),
        }

    def _audit(
        self,
        decision: str,
        reason: str,
        resource_id: str,
        amount: int,
        remaining: int,
        tx_hash: str | None = None,
        ledger: int | None = None,
    ) -> None:
        event = AuditEvent(
            ts=time.time(),
            decision=decision,
            reason=reason,
            resource_id=resource_id,
            amount=amount,
            remaining=remaining,
            tx_hash=tx_hash,
            ledger=ledger,
        )
        self.state.audit.append(event)
        if self.conn is not None:
            insert_audit(
                self.conn,
                self.session_id,
                ts=event.ts,
                decision=event.decision,
                reason=event.reason,
                resource_id=event.resource_id,
                amount=event.amount,
                remaining=event.remaining,
                tx_hash=event.tx_hash,
                ledger=event.ledger,
            )

    def _audit_view(self) -> list[dict[str, Any]]:
        if self.conn is None:
            return [e.__dict__ for e in reversed(self.state.audit[-40:])]
        return [dict(row) for row in list_audit(self.conn, self.session_id)]
