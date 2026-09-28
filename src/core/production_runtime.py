from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from src.core.studio_review import (
    ASSISTANT_ACCEPTED,
    REFINEMENT_REQUIRED as PROMOTION_REFINEMENT_REQUIRED,
    USER_ACCEPTED,
    VERIFICATION_REQUIRED,
    derive_promotion_state,
    legacy_review_aliases,
    promotion_diagnostics,
)

PASS = "PASS"
FAIL = "FAIL"
PENDING = "PENDING"
GATE_STATES = {PASS, FAIL, PENDING}
LEGACY_STATUS_MAP = {"FINAL_CANDIDATE": "VERIFICATION_REQUIRED"}
LEGACY_GATE_STATUS_MAP = {
    "PASS_WITH_REVIEW_NOTES": PENDING,
    "PASS_WITH_CINEMATIC_REFINEMENT_REQUIRED": PENDING,
}

DEFAULT_RENDER_JOB = {
    "job_id": None,
    "state": "NONE",
    "command": None,
    "cwd": None,
    "output": None,
    "started_at": None,
    "completed_at": None,
    "exit_code": None,
}

DEFAULT_WORKFLOW = {
    "mode": "autonomous_until_final_review",
    "user_review_policy": "final_candidate_only",
    "bootstrap_required": False,
    "bootstrap": {},
    "max_autonomous_repair_cycles": 4,
    "creative_qa_required": False,
    "studio_review_required": False,
    "quality_floor_required": False,
    "repair_cycle": 0,
    "escalation_reason": None,
    "last_action": None,
    "render_job": deepcopy(DEFAULT_RENDER_JOB),
}

DEFAULT_GATES = {
    "technical": {"status": PENDING, "evidence": None, "candidate_sha256": None},
    "assistant": {"status": PENDING, "notes": None, "candidate_sha256": None},
    "user": {"status": PENDING, "notes": None, "candidate_sha256": None},
}


def normalized_runtime(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return workflow/gate state with safe defaults for older v2 manifests."""
    workflow = deepcopy(DEFAULT_WORKFLOW)
    raw_workflow = data.get("workflow")
    if isinstance(raw_workflow, Mapping):
        for key, value in raw_workflow.items():
            if key == "render_job" and isinstance(value, Mapping):
                workflow["render_job"].update(value)
            elif key == "bootstrap" and isinstance(value, Mapping):
                workflow["bootstrap"].update(value)
            else:
                workflow[key] = value

    gates = deepcopy(DEFAULT_GATES)
    raw_gates = data.get("gates")
    explicit_gates = isinstance(raw_gates, Mapping)
    if explicit_gates:
        for name in gates:
            raw_gate = raw_gates.get(name)
            if isinstance(raw_gate, Mapping):
                gates[name].update(raw_gate)
                legacy_status = LEGACY_GATE_STATUS_MAP.get(str(gates[name].get("status") or ""))
                if legacy_status:
                    gates[name]["status"] = legacy_status

    # Backward compatibility with the earliest v2 shape. Once explicit gates
    # exist they are authoritative; legacy aliases must never resurrect a
    # previous PASS/FAIL after a gate was intentionally reset.
    review = data.get("review")
    if isinstance(review, Mapping) and not explicit_gates:
        assistant = review.get("assistant")
        user = review.get("user")
        if assistant in GATE_STATES:
            gates["assistant"]["status"] = assistant
        if user in GATE_STATES:
            gates["user"]["status"] = user

    return {"workflow": workflow, "gates": gates}


def _with_normalized_runtime(data: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(dict(data))
    runtime = normalized_runtime(data)
    merged["workflow"] = runtime["workflow"]
    raw_gates = deepcopy(dict(data.get("gates") or {})) if isinstance(data.get("gates"), Mapping) else {}
    for name, value in runtime["gates"].items():
        existing = raw_gates.get(name)
        if isinstance(existing, Mapping):
            combined = deepcopy(dict(existing))
            combined.update(value)
            raw_gates[name] = combined
        else:
            raw_gates[name] = deepcopy(value)
    merged["gates"] = raw_gates
    return merged


def apply_runtime_defaults(data: dict[str, Any]) -> dict[str, Any]:
    raw_status = str(data.get("status") or "")
    if raw_status in LEGACY_STATUS_MAP:
        workflow = data.setdefault("workflow", {})
        migration = workflow.setdefault("legacy_migration", {})
        migration.setdefault("original_status", raw_status)
        data["status"] = LEGACY_STATUS_MAP[raw_status]
    delivery = data.get("delivery")
    if isinstance(delivery, dict):
        delivery.setdefault("baseline_compare_fps", 2.0)
    runtime = normalized_runtime(data)
    data["workflow"] = runtime["workflow"]
    raw_gates = data.get("gates")
    extras = {
        key: deepcopy(value)
        for key, value in (raw_gates.items() if isinstance(raw_gates, Mapping) else [])
        if key not in runtime["gates"]
    }
    data["gates"] = {**runtime["gates"], **extras}
    aliases = legacy_review_aliases(data)
    review = data.setdefault("review", {})
    review["assistant"] = aliases["assistant"]
    review["user"] = aliases["user"]
    return data


def sync_review_aliases(data: dict[str, Any]) -> None:
    apply_runtime_defaults(data)
    aliases = legacy_review_aliases(data)
    review = data.setdefault("review", {})
    review["assistant"] = aliases["assistant"]
    review["user"] = aliases["user"]


def technical_passed(data: Mapping[str, Any]) -> bool:
    return normalized_runtime(data)["gates"]["technical"]["status"] == PASS


def assistant_passed(data: Mapping[str, Any]) -> bool:
    return derive_promotion_state(_with_normalized_runtime(data)) in {
        ASSISTANT_ACCEPTED,
        USER_ACCEPTED,
    }


def user_passed(data: Mapping[str, Any]) -> bool:
    return derive_promotion_state(_with_normalized_runtime(data)) == USER_ACCEPTED


def artifact_evidence_complete(data: Mapping[str, Any]) -> bool:
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return False
    required = ["candidate_master", "candidate_sha256", "artifact_receipt", "review_pack"]
    workflow = normalized_runtime(data)["workflow"]
    if workflow.get("creative_qa_required"):
        required += ["creative_qa", "creative_review"]
    if workflow.get("studio_review_required"):
        required += ["studio_review"]
    return all(artifacts.get(key) for key in required)


def ready_for_user_review(data: Mapping[str, Any]) -> bool:
    return (
        artifact_evidence_complete(data)
        and technical_passed(data)
        and assistant_passed(data)
    )


def repair_budget_remaining(data: Mapping[str, Any]) -> int:
    workflow = normalized_runtime(data)["workflow"]
    maximum = int(workflow.get("max_autonomous_repair_cycles", 0) or 0)
    current = int(workflow.get("repair_cycle", 0) or 0)
    return max(0, maximum - current)


def should_escalate(data: Mapping[str, Any]) -> bool:
    workflow = normalized_runtime(data)["workflow"]
    return bool(workflow.get("escalation_reason")) or repair_budget_remaining(data) <= 0


def _specialized_review_action(data: Mapping[str, Any]) -> str | None:
    merged = _with_normalized_runtime(data)
    diagnostics = promotion_diagnostics(merged)
    failures = diagnostics["blocking_failures"]
    unverified = diagnostics["unverified_requirements"]

    specialized_failures = [
        item for item in failures
        if item not in {"gate:technical", "gate:assistant", "gate:user"}
    ]
    if specialized_failures:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"

    if normalized_runtime(data)["workflow"].get("studio_review_required"):
        if any(
            item.startswith("criterion:")
            or item.startswith("studio review")
            for item in unverified
        ):
            return "studio_review"

    specialized_unverified = [
        item for item in unverified
        if item.startswith("gate:")
        and item not in {"gate:technical", "gate:assistant", "gate:user"}
    ]
    if specialized_unverified:
        return "verification_required"
    return None


def next_action(data: Mapping[str, Any]) -> str:
    status = data.get("status")
    runtime = normalized_runtime(data)
    gates = runtime["gates"]
    artifacts = data.get("artifacts") if isinstance(data.get("artifacts"), Mapping) else {}

    if status == "REJECTED_USER_QUALITY":
        return "rebuild_from_quality_floor"
    if status == "DONE":
        return "none" if user_passed(data) else (
            "repair_integrity"
            if derive_promotion_state(_with_normalized_runtime(data)) == PROMOTION_REFINEMENT_REQUIRED
            else "verification_required"
        )
    if status == "BLOCKED" or runtime["workflow"].get("escalation_reason"):
        return "human_decision"
    if status == "PLANNED":
        return "render"
    if status == "RENDERING":
        render_job = runtime["workflow"].get("render_job") or {}
        state = str(render_job.get("state") or "NONE").upper()
        if not render_job.get("job_id"):
            return "start_render_job"
        if state in {"NONE", "RUNNING", "UNKNOWN"}:
            return "reconcile_render_job"
        if state == "COMPLETED":
            return "record_candidate"
        if state in {"FAILED", "MISSING"}:
            return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
        return "reconcile_render_job"
    if status == "REFINEMENT_REQUIRED" and not artifacts.get("candidate_master"):
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if status == "VERIFICATION_REQUIRED" and not artifacts.get("candidate_master"):
        return "record_candidate"
    if not artifacts.get("candidate_master"):
        return "record_candidate"
    if gates["technical"]["status"] == PENDING:
        return "technical_qa"
    if gates["technical"]["status"] == FAIL:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if not artifacts.get("artifact_receipt") or not artifacts.get("review_pack"):
        return "build_review_evidence"
    if runtime["workflow"].get("creative_qa_required") and (
        not artifacts.get("creative_qa") or not artifacts.get("creative_review")
    ):
        return "creative_qa"

    specialized = _specialized_review_action(data)
    if specialized:
        return specialized

    if gates["assistant"]["status"] == PENDING:
        return "assistant_review"
    if gates["assistant"]["status"] == FAIL:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if ready_for_user_review(data) and gates["user"]["status"] == PENDING:
        return "user_final_review"
    if gates["user"]["status"] == FAIL:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if gates["user"]["status"] == PASS:
        return "finalize" if user_passed(data) else "verification_required"
    return "inspect_state"


def status_summary(data: Mapping[str, Any]) -> dict[str, Any]:
    runtime = normalized_runtime(data)
    merged = _with_normalized_runtime(data)
    promotion = promotion_diagnostics(merged)
    return {
        "production_id": data.get("production_id"),
        "status": data.get("status"),
        "promotion_state": promotion["state"],
        "promotion_diagnostics": promotion,
        "next_action": next_action(data),
        "ready_for_user_review": ready_for_user_review(data),
        "repair_budget_remaining": repair_budget_remaining(data),
        "workflow": runtime["workflow"],
        "gates": merged["gates"],
        "legacy_review_aliases": legacy_review_aliases(merged),
        "artifacts_complete": artifact_evidence_complete(data),
    }