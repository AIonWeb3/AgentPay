"""Deterministic demo transaction hashes (not on-chain)."""

from __future__ import annotations

import hashlib


def tx_hash(seed: str) -> str:
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return digest[:16].upper()
