import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates" / "production-v2.json").read_text())


def _legacy_manifest(tmp_path: Path) -> Path:
    data = copy.deepcopy(TEMPLATE)
    data["production_id"] = "legacy-validator-contract"
    data["source"]["show"] = "legacy-test"
    data["status"] = "FINAL_CANDIDATE"
    data["delivery"]["expected_duration_seconds"] = 1
    data["workflow"]["bootstrap_required"] = False
    data["workflow"]["quality_floor_required"] = False
    data["workflow"]["creative_qa_required"] = False
    data["workflow"]["studio_review_required"] = False
    data["studio_review"]["required"] = False
    path = tmp_path / "production.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def test_default_cli_accepts_runtime_legacy_aliases(tmp_path):
    path = _legacy_manifest(tmp_path)
    result = subprocess.run(
        [sys.executable, "scripts/validate-production-v2.py", str(path)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_strict_cli_rejects_legacy_committed_aliases(tmp_path):
    path = _legacy_manifest(tmp_path)
    result = subprocess.run(
        [sys.executable, "scripts/validate-production-v2.py", "--strict", str(path)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "status is invalid" in result.stdout
