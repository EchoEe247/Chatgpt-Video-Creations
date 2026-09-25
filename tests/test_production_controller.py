import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = json.loads((ROOT / "templates/production-v2.json").read_text())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class ProductionControllerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "source.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x180:rate=12:duration=1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(cls.source),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def make_manifest(self, name: str, *, width: int = 320) -> Path:
        package = self.root / name
        package.mkdir(parents=True, exist_ok=True)
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = name
        data["source"]["show"] = "test-show"
        data["delivery"].update(
            {
                "width": width,
                "height": 180,
                "fps": 12,
                "audio_required": False,
                "expected_duration_seconds": 1.0,
                "duration_tolerance_seconds": 0.15,
            }
        )
        data["render"]["command"] = ["python", "-c", "print('render')"]
        data["render"]["output"] = str(package / "render-output.mp4")
        path = package / "production.json"
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return path

    def run_ctl(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "scripts/productionctl.py", *map(str, args)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    def load(self, manifest: Path) -> dict:
        return json.loads(manifest.read_text(encoding="utf-8"))

    def prepare_to_user_review(self, manifest: Path) -> dict:
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        review = self.run_ctl("prepare-review", manifest)
        self.assertEqual(review.returncode, 0, review.stderr + review.stdout)
        passed = self.run_ctl("assistant-pass", manifest, "--notes", "integration pass")
        self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
        return self.load(manifest)

    def test_user_accept_rejects_missing_candidate(self):
        manifest = self.make_manifest("missing-candidate")
        data = self.prepare_to_user_review(manifest)
        candidate = manifest.parent / data["artifacts"]["candidate_master"]
        candidate.unlink()

        result = self.run_ctl("user-accept", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("candidate_master is missing", result.stderr)
        self.assertEqual(self.load(manifest)["status"], "USER_REVIEW")

    def test_done_status_detects_post_acceptance_tampering(self):
        manifest = self.make_manifest("done-integrity")
        data = self.prepare_to_user_review(manifest)
        accepted = self.run_ctl("user-accept", manifest, "--notes", "accepted")
        self.assertEqual(accepted.returncode, 0, accepted.stderr + accepted.stdout)
        data = self.load(manifest)
        candidate = manifest.parent / data["artifacts"]["candidate_master"]
        candidate.write_bytes(candidate.read_bytes() + b"tampered-after-accept")

        status = self.run_ctl("status", manifest)
        self.assertNotEqual(status.returncode, 0)
        self.assertIn('"next_action": "repair_integrity"', status.stdout)
        self.assertIn('"pass": false', status.stdout)
        self.assertEqual(self.load(manifest)["status"], "DONE")

    def test_user_accept_rejects_replaced_candidate_bytes(self):
        manifest = self.make_manifest("replaced-candidate")
        data = self.prepare_to_user_review(manifest)
        candidate = manifest.parent / data["artifacts"]["candidate_master"]
        candidate.write_bytes(candidate.read_bytes() + b"tampered")

        result = self.run_ctl("user-accept", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("candidate hash mismatch", result.stderr)
        self.assertEqual(self.load(manifest)["status"], "USER_REVIEW")

    def test_user_accept_rejects_missing_review_pack_evidence(self):
        manifest = self.make_manifest("missing-review-evidence")
        data = self.prepare_to_user_review(manifest)
        review_pack = manifest.parent / data["artifacts"]["review_pack"]
        pack = json.loads(review_pack.read_text(encoding="utf-8"))
        contact_sheet = review_pack.parent / pack["contact_sheet"]
        contact_sheet.unlink()

        result = self.run_ctl("user-accept", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contact_sheet is missing", result.stderr)
        self.assertEqual(self.load(manifest)["status"], "USER_REVIEW")

    def test_user_accept_rejects_review_pack_hash_mismatch(self):
        manifest = self.make_manifest("review-pack-binding")
        data = self.prepare_to_user_review(manifest)
        review_pack = manifest.parent / data["artifacts"]["review_pack"]
        pack = json.loads(review_pack.read_text(encoding="utf-8"))
        pack["candidate_sha256"] = "0" * 64
        review_pack.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

        result = self.run_ctl("user-accept", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("review pack is not bound", result.stderr)
        self.assertEqual(self.load(manifest)["status"], "USER_REVIEW")

    def test_render_job_identity_is_persisted_and_reconciled(self):
        manifest = self.make_manifest("render-job")
        started = self.run_ctl("rendering", manifest, "--job-id", "job-test-123")
        self.assertEqual(started.returncode, 0, started.stderr + started.stdout)
        data = self.load(manifest)
        self.assertEqual(data["status"], "RENDERING")
        self.assertEqual(data["workflow"]["render_job"]["job_id"], "job-test-123")

        status = self.run_ctl("status", manifest)
        self.assertIn('"next_action": "reconcile_render_job"', status.stdout)

        failed = self.run_ctl(
            "reconcile-render",
            manifest,
            "--state",
            "missing",
            "--exit-code",
            "1",
        )
        self.assertNotEqual(failed.returncode, 0)
        data = self.load(manifest)
        self.assertEqual(data["status"], "REFINEMENT_REQUIRED")
        self.assertEqual(data["workflow"]["render_job"]["state"], "MISSING")

    def test_configured_missing_review_resources_fail_closed(self):
        manifest = self.make_manifest("missing-resources")
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        data = self.load(manifest)
        data["render"]["scene_plan"] = "missing-scene-plan.json"
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = self.run_ctl("prepare-review", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configured scene plan is missing", result.stderr)

        data = self.load(manifest)
        data["render"]["scene_plan"] = None
        data["artifacts"]["baseline_master"] = "missing-baseline.mp4"
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        result = self.run_ctl("prepare-review", manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("configured baseline is missing", result.stderr)

    def test_repair_preserves_immutable_iteration_evidence(self):
        manifest = self.make_manifest("iteration-history")
        data = self.prepare_to_user_review(manifest)
        rejected = self.run_ctl("user-reject", manifest, "--notes", "fix framing")
        self.assertEqual(rejected.returncode, 0, rejected.stderr + rejected.stdout)

        repair = self.run_ctl("repair-start", manifest, "--reason", "fix framing")
        self.assertEqual(repair.returncode, 0, repair.stderr + repair.stdout)
        data = self.load(manifest)
        self.assertEqual(data["status"], "PLANNED")
        self.assertEqual(data["workflow"]["repair_cycle"], 1)
        self.assertEqual(len(data["history"]), 1)

        previous = data["history"][0]["artifacts"]
        previous_candidate = manifest.parent / previous["candidate_master"]
        previous_receipt = manifest.parent / previous["artifact_receipt"]
        previous_review = manifest.parent / previous["review_pack"]
        self.assertTrue(previous_candidate.is_file())
        self.assertTrue(previous_receipt.is_file())
        self.assertTrue(previous_review.is_file())
        self.assertIn("iterations/iteration-00", previous["candidate_master"])
        self.assertIsNone(data["artifacts"]["candidate_master"])

    def test_exhausted_budget_blocks_after_technical_failure(self):
        manifest = self.make_manifest("budget-exhausted", width=999)
        data = self.load(manifest)
        data["workflow"]["max_autonomous_repair_cycles"] = 1
        data["workflow"]["repair_cycle"] = 1
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        result = self.run_ctl("prepare-review", manifest)
        self.assertNotEqual(result.returncode, 0)
        data = self.load(manifest)
        self.assertEqual(data["status"], "BLOCKED")
        self.assertEqual(
            data["workflow"]["escalation_reason"],
            "autonomous_repair_budget_exhausted",
        )


if __name__ == "__main__":
    unittest.main()