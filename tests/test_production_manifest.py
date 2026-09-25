import copy
import json
import pathlib
import unittest

from src.core.production_manifest import validate_production_v2

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/production-v2.json").read_text())


class ProductionManifestTests(unittest.TestCase):
    def test_template_is_valid(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "wrong-shift-s01e01-v2"
        data["source"] = {
            "show": "wrong-shift",
            "season": "season-01",
            "episode": "episode-01",
        }
        self.assertEqual(validate_production_v2(data), [])

    def test_done_requires_evidence_and_both_reviews(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "done-test"
        data["source"] = {
            "show": "wrong-shift",
            "season": "season-01",
            "episode": "episode-01",
        }
        data["status"] = "DONE"
        errors = validate_production_v2(data)
        self.assertTrue(any("review PASS" in error for error in errors))
        self.assertTrue(any("candidate_master" in error for error in errors))

    def test_business_source_requires_release_provenance(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "business-test"
        data["lane"] = "business"
        data["source"] = {"project": "demo"}
        errors = validate_production_v2(data)
        self.assertIn("business source.release is required", errors)
        self.assertIn("business source.exact_commit is required", errors)


if __name__ == "__main__":
    unittest.main()
