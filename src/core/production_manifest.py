from __future__ import annotations

from typing import Any, Mapping

LANES = {"animation", "business"}
STATUSES = {
    "PLANNED",
    "RENDERING",
    "CANDIDATE",
    "ASSISTANT_REVIEW",
    "USER_REVIEW",
    "REFINEMENT_REQUIRED",
    "DONE",
}
REVIEWS = {"PENDING", "PASS", "FAIL"}


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

    review = data.get("review")
    if not isinstance(review, Mapping):
        errors.append("review must be an object")
        review = {}
    for key in ("assistant", "user"):
        if review.get(key) not in REVIEWS:
            errors.append(f"review.{key} must be PENDING, PASS, or FAIL")

    if status == "DONE":
        if review.get("assistant") != "PASS" or review.get("user") != "PASS":
            errors.append("DONE requires assistant and user review PASS")
        for key in ("candidate_master", "artifact_receipt", "review_pack"):
            if not artifacts.get(key):
                errors.append(f"DONE requires artifacts.{key}")

    return errors
