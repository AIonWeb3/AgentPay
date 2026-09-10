#!/usr/bin/env python3
"""Write deterministic pitch seed artifacts (75 txs, policy JSON)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "policy-generator"))

from generate_policy import score_transactions  # noqa: E402
from simulate_agent import generate_transaction_log  # noqa: E402

OUT = ROOT / "demo" / "data"
TX = OUT / "seed_tx_log.json"
POLICY = OUT / "seed_policy.json"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    log = generate_transaction_log(num_transactions=75, span_hours=24, seed=42)
    spec = score_transactions(log)
    TX.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    POLICY.write_text(spec.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"wrote {TX} ({len(log)} txs)")
    print(f"wrote {POLICY} ({len(spec.allowed_contracts)} vendors)")


if __name__ == "__main__":
    main()
