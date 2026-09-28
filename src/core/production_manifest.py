from __future__ import annotations

import re
from typing import Any, Mapping

from src.core.production_runtime import GATE_STATES, normalized_runtime
from src.core.studio_review import (
    ASSISTANT_ACCEPTED, USER_ACCEPTED, derive_promotion_state,
    legacy_review_aliases, validate_studio_review,
)
from src.core.final_screening import validate_final_screening

LANES = {"animation", "business"}
STATUSES = {
    "PLANNED",
    "RENDERING",
    "CANDIDATE",
    "ASSISTANT_REVIEW",
    "USER_REVIEW",
    "REFINEMENT_REQUIRED",
    "VERIFICATION_REQUIRED",
    "BLOCKED",
    "REJECTED_USER_QUALITY",
    "DONE",
}
REVIEWS = {"PENDING", "PASS", "FAIL"}
WORKFLOW_MODES = {"autonomous_until_final_review"}
USER_REVIEW_POLICIES = {"final_candidate_only"}
DELIVERY_PROFILES = {"h264_web", "custom"}
RENDER_JOB_STATES = {"NONE", "RUNNING", "COMPLETED", "FAILED", "MISSING", "UNKNOWN"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def validate_production_v2(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")

    production_id = data.get("production_id")
    if not isinstance(production_id, str) or not production_id.strip():
        errors.append("production_id must be a non-empty string")

    lane = data.get("lane")
    if lane not in LANES:
        errors.append("lane must be animation or business")

    status = data.get("status")
    if status not in STATUSES:
        errors.append("status is invalid")

    source = data.get("source")
    if not isinstance(source, Mapping):
        errors.append("source must be an object")
        source = {}

    if lane == "animation":
        for key in ("show", "season", "episode"):
            if not source.get(key):
                errors.append(f"animation source.{key} is required")
    elif lane == "business":
        for key in ("project", "release", "exact_commit"):
            if not source.get(key):
                errors.append(f"business source.{key} is required")

    render = data.get("render")
    if not isinstance(render, Mapping):
        errors.append("render must be an object")
        render = {}
    command = render.get("command")
    if command is not None and not (
        isinstance(command, list) and all(isinstance(item, str) and item for item in command)
    ):
        errors.append("render.command must be an argv string array")
    for key in ("cwd", "output", "scene_plan", "scene_directory", "master_recipe"):
        value = render.get(key)
        if value is not None and not isinstance(value, str):
            errors.append(f"render.{key} must be a string or null")

    delivery = data.get("delivery")
    if not isinstance(delivery, Mapping):
        errors.append("delivery must be an object")
        delivery = {}

    if delivery.get("profile") not in DELIVERY_PROFILES:
        errors.append("delivery.profile must be h264_web or custom")
    for key in ("width", "height"):
        value = delivery.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"delivery.{key} must be a positive integer")
    if not _positive_number(delivery.get("fps")):
        errors.append("delivery.fps must be positive")
    if not isinstance(delivery.get("audio_required"), bool):
        errors.append("delivery.audio_required must be boolean")

    for key in ("video_codec", "pixel_format"):
        value = delivery.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"delivery.{key} must be a non-empty string")
    if delivery.get("audio_required"):
        value = delivery.get("audio_codec")
        if not isinstance(value, str) or not value:
            errors.append("delivery.audio_codec is required when audio_required is true")
        silence_limit = delivery.get("max_unintended_silence_seconds")
        if not isinstance(silence_limit, (int, float)) or isinstance(silence_limit, bool) or silence_limit < 0:
            errors.append("delivery.max_unintended_silence_seconds must be >= 0 when audio is required")

    expected_duration = delivery.get("expected_duration_seconds")
    if expected_duration is not None and not _positive_number(expected_duration):
        errors.append("delivery.expected_duration_seconds must be positive or null")
    if status not in {"PLANNED", "BLOCKED"} and not _positive_number(expected_duration):
        errors.append("non-PLANNED production states require delivery.expected_duration_seconds")

    tolerance = delivery.get("duration_tolerance_seconds")
    if not _positive_number(tolerance):
        errors.append("delivery.duration_tolerance_seconds must be positive")

    compare_fps = delivery.get("baseline_compare_fps")
    if not _positive_number(compare_fps):
        errors.append("delivery.baseline_compare_fps must be positive")

    intervals = delivery.get("intentional_silence_intervals")
    if not isinstance(intervals, list):
        errors.append("delivery.intentional_silence_intervals must be an array")
    else:
        for index, interval in enumerate(intervals):
            if not (
                isinstance(interval, list)
                and len(interval) == 2
                and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in interval)
                and 0 <= float(interval[0]) < float(interval[1])
            ):
                errors.append(
                    f"delivery.intentional_silence_intervals[{index}] must be [start,end] with 0 <= start < end"
                )

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, Mapping):
        errors.append("artifacts must be an object")
        artifacts = {}
    candidate_path = artifacts.get("candidate_master")
    candidate_sha = artifacts.get("candidate_sha256")
    if candidate_path:
        if not isinstance(candidate_sha, str) or not SHA256_RE.fullmatch(candidate_sha):
            errors.append("artifacts.candidate_sha256 must be a lowercase SHA-256 when candidate_master is set")
    elif candidate_sha is not None:
        errors.append("artifacts.candidate_sha256 requires artifacts.candidate_master")

    runtime = normalized_runtime(data)
    workflow = runtime["workflow"]
    gates = runtime["gates"]

    if workflow.get("mode") not in WORKFLOW_MODES:
        errors.append("workflow.mode must be autonomous_until_final_review")
    if workflow.get("user_review_policy") not in USER_REVIEW_POLICIES:
        errors.append("workflow.user_review_policy must be final_candidate_only")
    if not isinstance(workflow.get("bootstrap_required"), bool):
        errors.append("workflow.bootstrap_required must be boolean")
    bootstrap = workflow.get("bootstrap")
    if not isinstance(bootstrap, Mapping):
        errors.append("workflow.bootstrap must be an object")
        bootstrap = {}
    if workflow.get("bootstrap_required") and status != "PLANNED":
        for key in ("workflow_id", "workflow_version", "manifest_sha256", "docs_sha256", "lane", "receipt_sha256"):
            value = bootstrap.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"workflow.bootstrap.{key} is required after PLANNED")
    max_cycles = workflow.get("max_autonomous_repair_cycles")
    creative_required = workflow.get("creative_qa_required")
    if not isinstance(creative_required, bool):
        errors.append("workflow.creative_qa_required must be boolean")
    studio_required = workflow.get("studio_review_required")
    if not isinstance(studio_required, bool):
        errors.append("workflow.studio_review_required must be boolean")
    quality_floor_required = workflow.get("quality_floor_required")
    if not isinstance(quality_floor_required, bool):
        errors.append("workflow.quality_floor_required must be boolean")
    current_cycle = workflow.get("repair_cycle")
    if not isinstance(max_cycles, int) or isinstance(max_cycles, bool) or max_cycles < 1:
        errors.append("workflow.max_autonomous_repair_cycles must be an integer >= 1")
    if not isinstance(current_cycle, int) or isinstance(current_cycle, bool) or current_cycle < 0:
        errors.append("workflow.repair_cycle must be a non-negative integer")
    if (
        isinstance(max_cycles, int)
        and isinstance(current_cycle, int)
        and current_cycle > max_cycles
    ):
        errors.append("workflow.repair_cycle cannot exceed max_autonomous_repair_cycles")

    render_job = workflow.get("render_job")
    if not isinstance(render_job, Mapping):
        errors.append("workflow.render_job must be an object")
        render_job = {}
    render_state = str(render_job.get("state") or "NONE").upper()
    if render_state not in RENDER_JOB_STATES:
        errors.append("workflow.render_job.state is invalid")
    if status == "RENDERING":
        if not render_job.get("job_id"):
            errors.append("RENDERING requires workflow.render_job.job_id")
        if render_state not in {"RUNNING", "UNKNOWN"}:
            errors.append("RENDERING requires render job state RUNNING or UNKNOWN")
        if not render.get("output"):
            errors.append("RENDERING requires render.output")

    for gate_name in ("technical", "assistant", "user"):
        if gates[gate_name]["status"] not in GATE_STATES:
            errors.append(f"gates.{gate_name}.status must be PENDING, PASS, or FAIL")
        bound_sha = gates[gate_name].get("candidate_sha256")
        if bound_sha is not None and (
            not isinstance(bound_sha, str) or not SHA256_RE.fullmatch(bound_sha)
        ):
            errors.append(f"gates.{gate_name}.candidate_sha256 must be a lowercase SHA-256 or null")

    if status in {"ASSISTANT_REVIEW", "USER_REVIEW", "DONE"}:
        technical_sha = gates["technical"].get("candidate_sha256")
        if technical_sha != candidate_sha:
            errors.append(f"{status} requires technical gate bound to artifacts.candidate_sha256")
    if status in {"USER_REVIEW", "DONE"}:
        assistant_sha = gates["assistant"].get("candidate_sha256")
        if assistant_sha != candidate_sha:
            errors.append(f"{status} requires assistant gate bound to artifacts.candidate_sha256")
    if status == "DONE":
        user_sha = gates["user"].get("candidate_sha256")
        if user_sha != candidate_sha:
            errors.append("DONE requires user gate bound to artifacts.candidate_sha256")

    studio_review = data.get("studio_review")
    if studio_review is not None:
        if not isinstance(studio_review, Mapping):
            errors.append("studio_review must be an object")
        else:
            errors.extend(
                validate_studio_review(
                    studio_review,
                    candidate_sha256=candidate_sha if isinstance(candidate_sha, str) else None,
                    require_complete=status in {"USER_REVIEW", "DONE"},
                )
            )
            if workflow.get("studio_review_required") and status in {"USER_REVIEW", "DONE"}:
                errors.extend(
                    validate_final_screening(
                        studio_review,
                        candidate_sha256=candidate_sha if isinstance(candidate_sha, str) else None,
                        duration_seconds=delivery.get("expected_duration_seconds"),
                        audio_required=delivery.get("audio_required") if isinstance(delivery.get("audio_required"), bool) else None,
                    )
                )
    elif workflow.get("studio_review_required"):
        errors.append("workflow.studio_review_required requires studio_review")

    review = data.get("review")
    if not isinstance(review, Mapping):
        errors.append("review must be an object")
        review = {}
    aliases = legacy_review_aliases(data)
    for key in ("assistant", "user"):
        if review.get(key) not in REVIEWS:
            errors.append(f"review.{key} must be PENDING, PASS, or FAIL")
        elif review.get(key) != aliases[key]:
            errors.append(
                f"review.{key} must mirror authoritative promotion state alias"
            )

    if status in {"CANDIDATE", "ASSISTANT_REVIEW", "USER_REVIEW", "DONE"}:
        for key in ("candidate_master", "candidate_sha256", "iteration_dir"):
            if not artifacts.get(key):
                errors.append(f"{status} requires artifacts.{key}")

    if status == "USER_REVIEW":
        if gates["technical"]["status"] != "PASS":
            errors.append("USER_REVIEW requires technical gate PASS")
        if derive_promotion_state(data) not in {ASSISTANT_ACCEPTED, USER_ACCEPTED}:
            errors.append("USER_REVIEW requires authoritative assistant acceptance")
        required_artifacts = ["artifact_receipt", "review_pack"]
        if workflow.get("creative_qa_required"):
            required_artifacts += ["creative_qa", "creative_review"]
        if workflow.get("studio_review_required"):
            required_artifacts += ["studio_review"]
        for key in required_artifacts:
            if not artifacts.get(key):
                errors.append(f"USER_REVIEW requires artifacts.{key}")

    if status == "DONE":
        if gates["technical"]["status"] != "PASS":
            errors.append("DONE requires technical gate PASS")
        if derive_promotion_state(data) != USER_ACCEPTED:
            errors.append("DONE requires authoritative USER_ACCEPTED promotion state")
        required_artifacts = ["artifact_receipt", "review_pack"]
        if workflow.get("creative_qa_required"):
            required_artifacts += ["creative_qa", "creative_review"]
        if workflow.get("studio_review_required"):
            required_artifacts += ["studio_review"]
        for key in required_artifacts:
            if not artifacts.get(key):
                errors.append(f"DONE requires artifacts.{key}")

    if status == "BLOCKED" and not workflow.get("escalation_reason"):
        errors.append("BLOCKED requires workflow.escalation_reason")

    return errors