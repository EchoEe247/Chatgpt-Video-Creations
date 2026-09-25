from __future__ import annotations

from typing import Any, Mapping

from src.core.production_runtime import GATE_STATES, normalized_runtime

LANES = {"animation", "business"}
STATUSES = {
    "PLANNED",
    "RENDERING",
    "CANDIDATE",
    "ASSISTANT_REVIEW",
    "USER_REVIEW",
    "REFINEMENT_REQUIRED",
    "BLOCKED",
    "DONE",
}
REVIEWS = {"PENDING", "PASS", "FAIL"}
WORKFLOW_MODES = {"autonomous_until_final_review"}
USER_REVIEW_POLICIES = {"final_candidate_only"}


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

    delivery = data.get("delivery")
    if not isinstance(delivery, Mapping):
        errors.append("delivery must be an object")
        delivery = {}
    for key in ("width", "height"):
        value = delivery.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"delivery.{key} must be a positive integer")
    fps = delivery.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        errors.append("delivery.fps must be positive")
    if not isinstance(delivery.get("audio_required"), bool):
        errors.append("delivery.audio_required must be boolean")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, Mapping):
        errors.append("artifacts must be an object")
        artifacts = {}

    runtime = normalized_runtime(data)
    workflow = runtime["workflow"]
    gates = runtime["gates"]

    if workflow.get("mode") not in WORKFLOW_MODES:
        errors.append("workflow.mode must be autonomous_until_final_review")
    if workflow.get("user_review_policy") not in USER_REVIEW_POLICIES:
        errors.append("workflow.user_review_policy must be final_candidate_only")
    max_cycles = workflow.get("max_autonomous_repair_cycles")
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

    for gate_name in ("technical", "assistant", "user"):
        if gates[gate_name]["status"] not in GATE_STATES:
            errors.append(f"gates.{gate_name}.status must be PENDING, PASS, or FAIL")

    review = data.get("review")
    if not isinstance(review, Mapping):
        errors.append("review must be an object")
        review = {}
    for key in ("assistant", "user"):
        if review.get(key) not in REVIEWS:
            errors.append(f"review.{key} must be PENDING, PASS, or FAIL")
        elif review.get(key) != gates[key]["status"]:
            errors.append(f"review.{key} must mirror gates.{key}.status")

    if status == "USER_REVIEW":
        if gates["technical"]["status"] != "PASS":
            errors.append("USER_REVIEW requires technical gate PASS")
        if gates["assistant"]["status"] != "PASS":
            errors.append("USER_REVIEW requires assistant gate PASS")
        for key in ("candidate_master", "artifact_receipt", "review_pack"):
            if not artifacts.get(key):
                errors.append(f"USER_REVIEW requires artifacts.{key}")

    if status == "DONE":
        if gates["technical"]["status"] != "PASS":
            errors.append("DONE requires technical gate PASS")
        if gates["assistant"]["status"] != "PASS" or gates["user"]["status"] != "PASS":
            errors.append("DONE requires assistant and user review PASS")
        for key in ("candidate_master", "artifact_receipt", "review_pack"):
            if not artifacts.get(key):
                errors.append(f"DONE requires artifacts.{key}")

    if status == "BLOCKED" and not workflow.get("escalation_reason"):
        errors.append("BLOCKED requires workflow.escalation_reason")

    return errors
