import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_seed_pitch_writes_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "seed_pitch.py")])
    tx = ROOT / "demo" / "data" / "seed_tx_log.json"
    pol = ROOT / "demo" / "data" / "seed_policy.json"
    assert tx.is_file()
    assert pol.is_file()
    import json

    log = json.loads(tx.read_text(encoding="utf-8"))
    assert len(log) == 75
    policy = json.loads(pol.read_text(encoding="utf-8"))
    assert policy["allowed_contracts"]


def test_run_pitch_script_exists():
    text = (ROOT / "scripts" / "run_pitch.sh").read_text(encoding="utf-8")
    assert "seed_pitch.py" in text
    assert "demo/server.py" in text
