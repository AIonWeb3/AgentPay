#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python -m pip install -q -r demo/requirements.txt -r policy-generator/requirements.txt
python scripts/seed_pitch.py
python demo/server.py
