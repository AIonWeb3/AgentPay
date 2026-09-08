#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> cargo test"
cargo test --workspace

echo "==> ruff"
ruff check policy-generator demo tests scripts

echo "==> pytest"
pytest -q
