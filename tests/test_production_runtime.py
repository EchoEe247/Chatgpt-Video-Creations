import copy
import json
import pathlib
import unittest

from src.core.production_runtime import (
    apply_runtime_defaults,
    next_action,
    ready_for_user_review,
    repair_budget_remaining,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/production-v2.json").read_text())


class ProductionRuntimeTests(unittest.TestCase):
    def make(self):
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = "test-production"
        data["source"]["show"] = "test-show"
        data["workflow"]["creative_qa_required"] = False
        data["workflow"]["quality_floor_required"] = False
        data["workflow"]["studio_review_required"] = False
        return data

    def test_planned_starts_at_render(self):
        data = self.make()
        self.assertEqual(next_action(data), "render")
        self.assertEqual(repair_budget_remaining(data), 4)

    def test_final_user_review_only_after_internal_gates(self):
        data = self.make()
        data["status"] = "USER_REVIEW"
        data["artifacts"] = {
            "candidate_master": "final/master.mp4",
            "candidate_sha256": "a" * 64,
            "artifact_receipt": "qa/review/artifact-receipt.json",
            "review_pack": "qa/review/review-pack.json",
        }
        data["gates"]["technical"]["status"] = "PASS"
        data["gates"]["assistant"]["status"] = "PASS"
        data["review"]["assistant"] = "PASS"
        self.assertTrue(ready_for_user_review(data))
        self.assertEqual(next_action(data), "user_final_review")

    def test_failed_internal_review_goes_to_repair_not_user(self):
        data = self.make()
        data["status"] = "REFINEMENT_REQUIRED"
        data["artifacts"]["candidate_master"] = "candidate.mp4"
        data["gates"]["technical"]["status"] = "PASS"
        data["gates"]["assistant"]["status"] = "FAIL"
        data["review"]["assistant"] = "FAIL"
        self.assertEqual(next_action(data), "build_review_evidence")
        data["artifacts"]["artifact_receipt"] = "receipt.json"
        data["artifacts"]["review_pack"] = "review.json"
        self.assertEqual(next_action(data), "repair")

    def test_technical_fail_routes_to_repair_or_human(self):
        data = self.make()
        data["status"] = "REFINEMENT_REQUIRED"
        data["artifacts"]["candidate_master"] = "candidate.mp4"
        data["artifacts"]["candidate_sha256"] = "b" * 64
        data["gates"]["technical"]["status"] = "FAIL"
        self.assertEqual(next_action(data), "repair")
        data["workflow"]["repair_cycle"] = data["workflow"]["max_autonomous_repair_cycles"]
        self.assertEqual(next_action(data), "human_decision")

    def test_rendering_reconciles_persisted_job(self):
        data = self.make()
        data["status"] = "RENDERING"
        data["workflow"]["render_job"]["job_id"] = "job-123"
        data["workflow"]["render_job"]["state"] = "RUNNING"
        self.assertEqual(next_action(data), "reconcile_render_job")

    def test_required_creative_qa_is_a_distinct_next_action(self):
        data = self.make()
        data["workflow"]["creative_qa_required"] = True
        data["status"] = "ASSISTANT_REVIEW"
        data["artifacts"].update({
            "candidate_master": "candidate.mp4",
            "candidate_sha256": "c" * 64,
            "artifact_receipt": "receipt.json",
            "review_pack": "review.json",
        })
        data["gates"]["technical"]["status"] = "PASS"
        self.assertEqual(next_action(data), "creative_qa")
        data["artifacts"]["creative_qa"] = "creative/creative-qa.json"
        data["artifacts"]["creative_review"] = "creative/assistant-review.json"
        self.assertEqual(next_action(data), "assistant_review")

    def test_user_review_requires_creative_artifacts_when_enabled(self):
        data = self.make()
        data["workflow"]["creative_qa_required"] = True
        data["status"] = "USER_REVIEW"
        data["artifacts"].update({
            "candidate_master": "candidate.mp4",
            "candidate_sha256": "d" * 64,
            "artifact_receipt": "receipt.json",
            "review_pack": "review.json",
        })
        data["gates"]["technical"]["status"] = "PASS"
        data["gates"]["assistant"]["status"] = "PASS"
        self.assertFalse(ready_for_user_review(data))
        data["artifacts"]["creative_qa"] = "creative/creative-qa.json"
        data["artifacts"]["creative_review"] = "creative/assistant-review.json"
        self.assertTrue(ready_for_user_review(data))

    def test_explicit_gate_reset_beats_legacy_alias(self):
        data = self.make()
        data["gates"]["assistant"]["status"] = "PENDING"
        data["review"]["assistant"] = "FAIL"
        apply_runtime_defaults(data)
        self.assertEqual(data["gates"]["assistant"]["status"], "PENDING")
        self.assertEqual(data["review"]["assistant"], "PENDING")

    def test_legacy_final_candidate_migrates_to_verification_required(self):
        data = self.make()
        data["status"] = "FINAL_CANDIDATE"
        data["gates"]["assistant"]["status"] = "PASS_WITH_REVIEW_NOTES"
        data["review"]["assistant"] = "PASS_WITH_REVIEW_NOTES"
        apply_runtime_defaults(data)
        self.assertEqual(data["status"], "VERIFICATION_REQUIRED")
        self.assertEqual(data["gates"]["assistant"]["status"], "PENDING")
        self.assertEqual(data["review"]["assistant"], "PENDING")
        self.assertEqual(data["workflow"]["legacy_migration"]["original_status"], "FINAL_CANDIDATE")

    def test_older_v2_manifest_gets_runtime_defaults(self):
        old = {
            "schema_version": 2,
            "review": {"assistant": "PASS", "user": "PENDING"},
        }
        apply_runtime_defaults(old)
        self.assertEqual(old["workflow"]["user_review_policy"], "final_candidate_only")
        self.assertEqual(old["gates"]["assistant"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()