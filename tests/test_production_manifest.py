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
        self.assertTrue(any("authoritative USER_ACCEPTED" in error for error in errors))
        self.assertTrue(any("candidate_master" in error for error in errors))

    def test_rendering_requires_persisted_job_identity(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "rendering-test"
        data["source"]["show"] = "test-show"
        data["status"] = "RENDERING"
        data["delivery"]["expected_duration_seconds"] = 8.0
        data["render"]["output"] = "render.mp4"
        errors = validate_production_v2(data)
        self.assertIn("RENDERING requires workflow.render_job.job_id", errors)

    def test_candidate_requires_sha256_binding(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "candidate-test"
        data["source"]["show"] = "test-show"
        data["status"] = "CANDIDATE"
        data["delivery"]["expected_duration_seconds"] = 8.0
        data["artifacts"]["candidate_master"] = "iterations/iteration-00/candidate.mp4"
        data["artifacts"]["iteration_dir"] = "iterations/iteration-00"
        errors = validate_production_v2(data)
        self.assertTrue(any("candidate_sha256" in error for error in errors))

    def test_audio_delivery_requires_explicit_silence_limit(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "audio-profile-test"
        data["source"]["show"] = "test-show"
        data["delivery"]["max_unintended_silence_seconds"] = None
        errors = validate_production_v2(data)
        self.assertIn(
            "delivery.max_unintended_silence_seconds must be >= 0 when audio is required",
            errors,
        )

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