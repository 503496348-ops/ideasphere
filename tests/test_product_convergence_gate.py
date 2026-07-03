import json
import subprocess
import sys
from pathlib import Path


def test_product_convergence_gate_runs_and_reports_schema():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "product_convergence_gate.py"
    assert script.exists()
    result = subprocess.run(
        [sys.executable, str(script), "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.stdout, result.stderr
    payload = json.loads(result.stdout)
    assert payload["repo"] == root.name
    assert "issues" in payload and "warnings" in payload and "metrics" in payload
    assert payload["metrics"]["code_files"] >= 1
