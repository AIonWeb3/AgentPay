#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> cargo fmt"
cargo fmt --all -- --check

echo "==> cargo clippy"
cargo clippy -p mcp-server --all-targets -- -D warnings

echo "==> cargo test"
cargo test --workspace

echo "==> ruff"
ruff check policy-generator demo tests scripts

echo "==> pytest"
pytest -q
