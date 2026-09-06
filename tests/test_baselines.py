import pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.baseline_registry import next_baseline_id, validate_registry

def valid_entry(baseline_id: str = "B1") -> dict:
    return {
        "id": baseline_id,
        "lane": "2d",
        "scope": "character floor and portal alignment reference",
        "commit": "a" * 40,
        "artifacts": [{"ref": "artifacts/B1/reference.mp4", "sha256": "b" * 64}],
        "conditions": {"canvas": "1280x720", "fps": 24, "video_codec": "h264"},
        "validated_capabilities": [
            "character foot anchor lands on validated floor",
            "portal energy is concentric with physical portal opening",
        ],
        "known_limitations": ["single-set reference only"],
        "not_validated": ["3D animation"],
        "technical_validation": "PASS",
        "visual_validation": "PASS",
        "user_review": "PASS",
        "receipt": "receipts/baselines/B1.md",
    }

class BaselineRegistryTests(unittest.TestCase):
    def test_empty_registry_is_valid(self):
        data = {"schema_version": 1, "next_id": "B1", "validated_baselines": []}
        self.assertEqual(validate_registry(data), [])
        self.assertEqual(next_baseline_id(data), "B1")

    def test_valid_visual_baseline_requires_user_pass(self):
        entry = valid_entry(); entry["user_review"] = "NOT_REQUIRED"
        data = {"schema_version": 1, "next_id": "B2", "validated_baselines": [entry]}
        self.assertTrue(any("user_review must be PASS" in e for e in validate_registry(data)))

    def test_rejects_artifact_without_exact_hash(self):
        entry = valid_entry(); entry["artifacts"][0]["sha256"] = "not-a-hash"
        data = {"schema_version": 1, "next_id": "B2", "validated_baselines": [entry]}
        self.assertTrue(any("sha256" in e for e in validate_registry(data)))

    def test_next_id_tracks_highest_promoted_baseline(self):
        data = {"schema_version": 1, "next_id": "B3", "validated_baselines": [valid_entry("B1"), valid_entry("B2")]}
        self.assertEqual(validate_registry(data), [])
        self.assertEqual(next_baseline_id(data), "B3")

    def test_rejects_wrong_next_id(self):
        data = {"schema_version": 1, "next_id": "B9", "validated_baselines": [valid_entry("B1")]}
        self.assertTrue(any("next_id must be B2" in e for e in validate_registry(data)))

if __name__ == "__main__": unittest.main()
