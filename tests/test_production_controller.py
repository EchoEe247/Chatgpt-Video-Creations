import copy
import json
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.core.final_screening import DEPARTMENTS
from src.core.director_execution import compile_plan

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

    def make_manifest(self, name: str, *, width: int = 320, creative_required: bool = False) -> Path:
        package = self.root / name
        package.mkdir(parents=True, exist_ok=True)
        data = copy.deepcopy(TEMPLATE)
        data["production_id"] = name
        # Most controller tests exercise legacy/runtime behavior unrelated to the
        # fresh-session bootstrap gate. Dedicated workflow-contract tests cover
        # the required-binding path.
        data["workflow"]["bootstrap_required"] = False
        data["workflow"]["quality_floor_required"] = False
        data["workflow"]["studio_review_required"] = False
        data["workflow"]["creative_qa_required"] = creative_required
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

    def build_final_quality_plan(self, manifest: Path) -> Path:
        package=manifest.parent
        development=package/"development"
        development.mkdir(parents=True,exist_ok=True)
        shutil.copy2(self.source, development/"previs.mp4")
        subprocess.run(
            [
                "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                "-i", "color=c=gray:s=64x64:d=0.1", "-frames:v", "1",
                str(development/"lookdev.png"),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            capture_output=True,
        )
        brief={
            "schema_version":1,
            "title":"quality-floor-controller",
            "goal":{"audience":"test","runtime_seconds":1,"one_sentence_promise":"test","ending_takeaway":""},
            "quality_floor":{
                "delivery_level":"final",
                "visual_mode":"cinematic_3d",
                "character_mode":"none",
                "environment_mode":"graphic",
                "proxy_assets_allowed":False,
                "minimum_delivery_height":720,
                "notes":""
            },
            "story":{"setup":"A","escalation":"B","turn":"C","resolution":"D","emotional_arc":[]},
            "reference_decomposition":[],
            "visual_grammar":{"style":"3D","palette_arc":[],"lighting":"lit","depth_rules":[],"typography_rules":[],"texture_rules":[],"forbidden_patterns":[]},
            "camera_grammar":{"default_behavior":"camera","allowed_moves":[],"physical_camera_assumptions":[],"intentional_imperfections":[],"avoid":[]},
            "audio_grammar":{"narration_or_dialogue":"","score_arc":[],"ambience":[],"effects":[],"silence_rules":[],"sync_rules":[]},
            "editing_grammar":{"pace_arc":[],"cut_motivations":[],"transition_rules":[],"avoid":[]},
            "asset_strategy":{"principle":"source_nouns_author_verbs","requirements":[]},
            "visual_development":{
                "previs":{"decision":"required","status":"approved","artifact":"development/previs.mp4","review_focus":["timing"],"notes":""},
                "lookdev":{"decision":"required","status":"approved","artifact":"development/lookdev.png","review_focus":["materials","lighting"],"notes":""}
            },
            "hero_shots":["shot-01"],
            "shots":[{
                "id":"shot-01","duration_seconds":1,"narrative_purpose":"test","visible_event":"object moves",
                "camera":"locked","subject_motion":"move","environment_motion":"light","depth_layers":[],"palette":"",
                "transition_in":"cut","transition_out":"cut","audio_cue":"tone","renderer":"blender","assets":[],
                "continuity_dependencies":[],"review_points_seconds":[0.5],"failure_modes":[],
                "compositing":{"mode":"beauty_only","passes":[],"goals":[],"output":"","notes":""}
            }],
            "handoff":{"critical_files":[],"known_limits":[],"acceptance_focus":[]}
        }
        director=package/"director-brief.json"
        director.write_text(json.dumps(brief,indent=2)+"\n",encoding="utf-8")
        plan=compile_plan(director,ROOT/"assets/catalog.json",width=1280,height=720,fps=24)
        plan_path=package/"execution-plan.json"
        plan_path.write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
        return plan_path

    def prepare_to_user_review(self, manifest: Path) -> dict:
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        review = self.run_ctl("prepare-review", manifest)
        self.assertEqual(review.returncode, 0, review.stderr + review.stdout)
        passed = self.run_ctl("assistant-pass", manifest, "--notes", "integration pass")
        self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
        return self.load(manifest)


    def build_creative_evidence(self, manifest: Path) -> tuple[Path, Path]:
        data = self.load(manifest)
        digest = data["artifacts"]["candidate_sha256"]
        root = manifest.parent / "creative"
        (root / "phone").mkdir(parents=True, exist_ok=True)
        (root / "normal").mkdir(parents=True, exist_ok=True)
        contact = root / "contact.jpg"
        phone = root / "phone" / "shot-01.jpg"
        clip = root / "normal" / "shot-01.mp4"
        contact.write_bytes(b"contact")
        phone.write_bytes(b"phone")
        shutil.copy2(self.source, clip)

        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        report = {
            "schema_version": 1,
            "media_sha256": digest,
            "evidence": {
                "contact_sheet": "contact.jpg",
                "contact_sheet_sha256": sha(contact),
                "review_points": [
                    {
                        "shot_id": "shot-01",
                        "phone_frame": "phone/shot-01.jpg",
                        "normal_speed_clip": "normal/shot-01.mp4",
                        "frame_sha256": sha(phone),
                        "clip_sha256": sha(clip),
                    }
                ],
            },
        }
        report_path = root / "creative-qa.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        report_sha = sha(report_path)
        criteria = {
            key: {"pass": True, "notes": "inspected exact candidate evidence", "evidence": ["contact.jpg"]}
            for key in (
                "composition",
                "phone_scale_readability",
                "visible_motion",
                "camera_variety",
                "normal_speed_story_read",
            )
        }
        review = {
            "schema_version": 1,
            "candidate_sha256": digest,
            "creative_qa_sha256": report_sha,
            "criteria": criteria,
            "defects": [],
            "next_change": "",
        }
        review_path = root / "assistant-review.json"
        review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
        return report_path, review_path

    def test_quality_floor_render_preflight_requires_real_artifacts_and_studio_review(self):
        manifest=self.make_manifest("quality-floor-preflight")
        plan_path=self.build_final_quality_plan(manifest)
        data=self.load(manifest)
        data["workflow"]["quality_floor_required"]=True
        data["workflow"]["creative_qa_required"]=True
        data["workflow"]["studio_review_required"]=False
        data["render"]["scene_plan"]=str(plan_path)
        data["delivery"]["height"]=720
        data["delivery"]["audio_required"]=True
        data["delivery"]["audio_codec"]="aac"
        data["delivery"]["max_unintended_silence_seconds"]=1
        manifest.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

        # Missing on-disk look-dev evidence blocks before rendering.
        lookdev_path = manifest.parent/"development"/"lookdev.png"
        lookdev_bytes = lookdev_path.read_bytes()
        lookdev_path.unlink()
        missing=self.run_ctl("render-spec",manifest)
        self.assertNotEqual(missing.returncode,0)
        self.assertIn("visual-development artifact is missing",missing.stderr)

        lookdev_path.write_bytes(lookdev_bytes)
        blocked=self.run_ctl("render-spec",manifest)
        self.assertNotEqual(blocked.returncode,0)
        self.assertIn("studio_review_required=true",blocked.stderr)

        data=self.load(manifest)
        data["workflow"]["studio_review_required"]=True
        manifest.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
        ready=self.run_ctl("render-spec",manifest)
        self.assertEqual(ready.returncode,0,ready.stderr+ready.stdout)

        # Approved development evidence is hash-bound; replacement invalidates preflight.
        previs_path = manifest.parent/"development"/"previs.mp4"
        original_previs = previs_path.read_bytes()
        previs_path.write_bytes(b"")
        tampered=self.run_ctl("render-spec",manifest)
        self.assertNotEqual(tampered.returncode,0)
        self.assertIn("changed after approval",tampered.stderr)
        previs_path.write_bytes(original_previs)

    def test_quality_floor_proof_paths_follow_director_brief_when_plan_moves(self):
        manifest = self.make_manifest("quality-floor-plan-relocation")
        plan_path = self.build_final_quality_plan(manifest)
        moved_dir = manifest.parent / "compiled"
        moved_dir.mkdir()
        moved_plan = moved_dir / "execution-plan.json"
        plan_path.replace(moved_plan)

        data = self.load(manifest)
        data["workflow"]["quality_floor_required"] = True
        data["workflow"]["creative_qa_required"] = True
        data["workflow"]["studio_review_required"] = True
        data["render"]["scene_plan"] = str(moved_plan)
        data["delivery"]["height"] = 720
        data["delivery"]["audio_required"] = True
        data["delivery"]["audio_codec"] = "aac"
        data["delivery"]["max_unintended_silence_seconds"] = 1
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        ready = self.run_ctl("render-spec", manifest)
        self.assertEqual(ready.returncode, 0, ready.stderr + ready.stdout)

    def test_studio_review_required_blocks_missing_and_accepts_complete_screening(self):
        manifest = self.make_manifest("studio-required")
        data = self.load(manifest)
        data["workflow"]["studio_review_required"] = True
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        prepared = self.run_ctl("prepare-review", manifest)
        self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
        blocked = self.run_ctl("assistant-pass", manifest)
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("--studio-review", blocked.stderr)

        data = self.load(manifest)
        digest = data["artifacts"]["candidate_sha256"]
        departments = {
            name: {
                "applicability": "APPLICABLE",
                "status": "PASS",
                "evidence": ["ev-main"],
                "observations": ["reviewed exact final candidate"],
                "claim_types": ["perceived"],
            }
            for name in DEPARTMENTS
        }
        review = {
            "schema_version": 2,
            "required": True,
            "candidate_sha256": digest,
            "criteria": {
                "final_screening": {
                    "applicability": "APPLICABLE",
                    "status": "PASS",
                    "blocking": True,
                    "evidence": ["ev-main"],
                }
            },
            "evidence": {
                "ev-main": {
                    "state": "REVIEWED",
                    "candidate_sha256": digest,
                    "modalities": ["still_image", "sampled_temporal"],
                },
                "ev-continuous": {
                    "state": "REVIEWED",
                    "candidate_sha256": digest,
                    "modalities": ["continuous_video"],
                },
            },
            "final_screening": {
                "candidate_sha256": digest,
                "duration_seconds": 1.0,
                "departments": departments,
                "modalities": {
                    "still_image": {"applicability": "APPLICABLE", "status": "PASS", "evidence": ["ev-main"]},
                    "sampled_temporal": {"applicability": "APPLICABLE", "status": "PASS", "evidence": ["ev-main"]},
                    "continuous_video": {"applicability": "APPLICABLE", "status": "PASS", "evidence": ["ev-continuous"]},
                    "auditory": {"applicability": "NOT_APPLICABLE", "status": None, "reason": "silent delivery", "evidence": []},
                    "synchronized_av": {"applicability": "NOT_APPLICABLE", "status": None, "reason": "silent delivery", "evidence": []},
                },
                "coverage": {
                    "still_image": [{"start_seconds": 0, "end_seconds": 0.1}],
                    "sampled_temporal": [{"start_seconds": 0, "end_seconds": 1.0}],
                    "continuous_video": [{"start_seconds": 0, "end_seconds": 1.0}],
                    "auditory": [],
                    "synchronized_av": [],
                },
                "evidence_ids": ["ev-main", "ev-continuous"],
                "opening_reviewed": True,
                "ending_reviewed": True,
                "authored_points": {"planned_ids": [], "reviewed_ids": []},
                "second_pass": {"required": False, "status": "NOT_REQUIRED", "targets": [], "disposed_ids": []},
                "declaration": {
                    "reviewer": "model_plus_human",
                    "reviewed_at": "2026-09-28T00:00:00Z",
                    "modalities_actually_perceived": ["still_image", "sampled_temporal", "continuous_video"],
                    "candidate_sha256": digest,
                },
            },
        }
        review_path = manifest.parent / "studio-review-input.json"
        invalid_review = copy.deepcopy(review)
        invalid_review["final_screening"]["ending_reviewed"] = False
        review_path.write_text(json.dumps(invalid_review, indent=2) + "\n", encoding="utf-8")
        rejected = self.run_ctl("assistant-pass", manifest, "--studio-review", review_path)
        self.assertNotEqual(rejected.returncode, 0)
        after_reject = self.load(manifest)
        review_dest = manifest.parent / after_reject["artifacts"]["iteration_dir"] / "qa" / "studio-review.json"
        self.assertFalse(review_dest.exists(), "rejected studio review must not occupy immutable accepted path")

        review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
        passed = self.run_ctl("assistant-pass", manifest, "--studio-review", review_path)
        self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
        final = self.load(manifest)
        self.assertEqual(final["status"], "USER_REVIEW")
        self.assertTrue(final["artifacts"]["studio_review"]
        )

    def test_creative_qa_required_blocks_unbound_assistant_pass(self):
        manifest = self.make_manifest("creative-required", creative_required=True)
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        prepared = self.run_ctl("prepare-review", manifest)
        self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)

        blocked = self.run_ctl("assistant-pass", manifest, "--notes", "should block")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("--creative-qa and --creative-review", blocked.stderr)

        report, review = self.build_creative_evidence(manifest)
        passed = self.run_ctl(
            "assistant-pass",
            manifest,
            "--notes",
            "creative QA passed",
            "--creative-qa",
            report,
            "--creative-review",
            review,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
        data = self.load(manifest)
        self.assertEqual(data["status"], "USER_REVIEW")
        self.assertTrue(data["artifacts"]["creative_qa"])
        self.assertTrue(data["artifacts"]["creative_review"])

    def test_specialized_failure_blocks_legacy_assistant_pass(self):
        manifest = self.make_manifest("specialized-veto")
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        self.assertEqual(self.run_ctl("prepare-review", manifest).returncode, 0)
        data = self.load(manifest)
        digest = data["artifacts"]["candidate_sha256"]
        data["gates"]["cinematic"] = {
            "status": "REFINEMENT_REQUIRED",
            "candidate_sha256": digest,
            "evidence": "qa/cinematic.json",
        }
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        blocked = self.run_ctl("assistant-pass", manifest, "--notes", "legacy pass must not win")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("gate:cinematic", blocked.stderr)
        after = self.load(manifest)
        self.assertNotEqual(after["status"], "USER_REVIEW")

    def test_creative_bundle_tampering_breaks_user_review_integrity(self):
        manifest = self.make_manifest("creative-tamper", creative_required=True)
        self.assertEqual(self.run_ctl("candidate", manifest, self.source).returncode, 0)
        self.assertEqual(self.run_ctl("prepare-review", manifest).returncode, 0)
        report, review = self.build_creative_evidence(manifest)
        passed = self.run_ctl(
            "assistant-pass", manifest,
            "--creative-qa", report,
            "--creative-review", review,
        )
        self.assertEqual(passed.returncode, 0, passed.stderr + passed.stdout)
        (report.parent / "contact.jpg").write_bytes(b"tampered")
        accepted = self.run_ctl("user-accept", manifest)
        self.assertNotEqual(accepted.returncode, 0)
        self.assertIn("creative QA evidence bundle is invalid", accepted.stderr)

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