#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> cargo test"
cargo test --workspace

echo "==> pytest"
export PYTHONPATH="policy-generator:scripts:."
pytest -q tests policy-generator
