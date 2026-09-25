from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

PASS = "PASS"
FAIL = "FAIL"
PENDING = "PENDING"
GATE_STATES = {PASS, FAIL, PENDING}

DEFAULT_WORKFLOW = {
    "mode": "autonomous_until_final_review",
    "user_review_policy": "final_candidate_only",
    "max_autonomous_repair_cycles": 4,
    "repair_cycle": 0,
    "escalation_reason": None,
    "last_action": None,
}

DEFAULT_GATES = {
    "technical": {"status": PENDING, "evidence": None},
    "assistant": {"status": PENDING, "notes": None},
    "user": {"status": PENDING, "notes": None},
}


def normalized_runtime(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return workflow/gate state with safe defaults for older v2 manifests."""
    workflow = deepcopy(DEFAULT_WORKFLOW)
    raw_workflow = data.get("workflow")
    if isinstance(raw_workflow, Mapping):
        workflow.update(raw_workflow)

    gates = deepcopy(DEFAULT_GATES)
    raw_gates = data.get("gates")
    explicit_gates = isinstance(raw_gates, Mapping)
    if explicit_gates:
        for name in gates:
            raw_gate = raw_gates.get(name)
            if isinstance(raw_gate, Mapping):
                gates[name].update(raw_gate)

    # Backward-compatibility with the first v2 template. Once explicit gates
    # exist they are authoritative; the legacy review aliases must never
    # resurrect an old FAIL/PASS state after a gate is intentionally reset.
    review = data.get("review")
    if isinstance(review, Mapping) and not explicit_gates:
        assistant = review.get("assistant")
        user = review.get("user")
        if assistant in GATE_STATES:
            gates["assistant"]["status"] = assistant
        if user in GATE_STATES:
            gates["user"]["status"] = user

    return {"workflow": workflow, "gates": gates}


def apply_runtime_defaults(data: dict[str, Any]) -> dict[str, Any]:
    runtime = normalized_runtime(data)
    data["workflow"] = runtime["workflow"]
    data["gates"] = runtime["gates"]
    review = data.setdefault("review", {})
    review["assistant"] = runtime["gates"]["assistant"]["status"]
    review["user"] = runtime["gates"]["user"]["status"]
    return data


def sync_review_aliases(data: dict[str, Any]) -> None:
    runtime = normalized_runtime(data)
    data["workflow"] = runtime["workflow"]
    data["gates"] = runtime["gates"]
    review = data.setdefault("review", {})
    review["assistant"] = data["gates"]["assistant"]["status"]
    review["user"] = data["gates"]["user"]["status"]


def technical_passed(data: Mapping[str, Any]) -> bool:
    return normalized_runtime(data)["gates"]["technical"]["status"] == PASS


def assistant_passed(data: Mapping[str, Any]) -> bool:
    return normalized_runtime(data)["gates"]["assistant"]["status"] == PASS


def user_passed(data: Mapping[str, Any]) -> bool:
    return normalized_runtime(data)["gates"]["user"]["status"] == PASS


def artifact_evidence_complete(data: Mapping[str, Any]) -> bool:
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return False
    return all(
        artifacts.get(key)
        for key in ("candidate_master", "artifact_receipt", "review_pack")
    )


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


def next_action(data: Mapping[str, Any]) -> str:
    status = data.get("status")
    runtime = normalized_runtime(data)
    gates = runtime["gates"]
    artifacts = data.get("artifacts") if isinstance(data.get("artifacts"), Mapping) else {}

    if status == "DONE":
        return "none"
    if status == "BLOCKED" or runtime["workflow"].get("escalation_reason"):
        return "human_decision"
    if status == "PLANNED":
        return "render"
    if status == "RENDERING":
        return "wait_for_render"
    if not artifacts.get("candidate_master"):
        return "record_candidate"
    if gates["technical"]["status"] != PASS:
        return "technical_qa"
    if not artifacts.get("artifact_receipt") or not artifacts.get("review_pack"):
        return "build_review_evidence"
    if gates["assistant"]["status"] == PENDING:
        return "assistant_review"
    if gates["assistant"]["status"] == FAIL:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if ready_for_user_review(data) and gates["user"]["status"] == PENDING:
        return "user_final_review"
    if gates["user"]["status"] == FAIL:
        return "repair" if repair_budget_remaining(data) > 0 else "human_decision"
    if gates["user"]["status"] == PASS:
        return "finalize"
    return "inspect_state"


def status_summary(data: Mapping[str, Any]) -> dict[str, Any]:
    runtime = normalized_runtime(data)
    return {
        "production_id": data.get("production_id"),
        "status": data.get("status"),
        "next_action": next_action(data),
        "ready_for_user_review": ready_for_user_review(data),
        "repair_budget_remaining": repair_budget_remaining(data),
        "workflow": runtime["workflow"],
        "gates": runtime["gates"],
        "artifacts_complete": artifact_evidence_complete(data),
    }