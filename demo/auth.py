"""Operator API key checks for mutating demo routes."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException

OPERATOR_ENV = "DEMO_API_KEY"


def configured_operator_key() -> str:
    return os.environ.get(OPERATOR_ENV, "dev-operator-key")


def require_operator(x_api_key: str | None = Header(default=None, alias="X-Api-Key")) -> str:
    expected = configured_operator_key()
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return x_api_key
