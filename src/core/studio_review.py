from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
APPLICABILITY_STATES = {APPLICABLE, NOT_APPLICABLE}

PASS = "PASS"
FAIL = "FAIL"
UNVERIFIED = "UNVERIFIED"
CRITERION_STATES = {PASS, FAIL, UNVERIFIED}

PLANNED = "PLANNED"
GENERATED = "GENERATED"
DELIVERED = "DELIVERED"
REVIEWED = "REVIEWED"
EVIDENCE_STATES = {PLANNED, GENERATED, DELIVERED, REVIEWED}
EVIDENCE_RANK = {PLANNED: 0, GENERATED: 1, DELIVERED: 2, REVIEWED: 3}

REFINEMENT_REQUIRED = "REFINEMENT_REQUIRED"
VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
ASSISTANT_ACCEPTED = "ASSISTANT_ACCEPTED"
USER_ACCEPTED = "USER_ACCEPTED"
PROMOTION_STATES = {
    REFINEMENT_REQUIRED,
    VERIFICATION_REQUIRED,
    ASSISTANT_ACCEPTED,
    USER_ACCEPTED,
}

FAIL_LIKE = {FAIL, REFINEMENT_REQUIRED, "FAILED"}
PENDING_LIKE = {"PENDING", UNVERIFIED, "UNKNOWN", "VERIFICATION_REQUIRED"}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _legacy_gate(data: Mapping[str, Any], name: str) -> dict[str, Any]:
    gates = _mapping(data.get("gates"))
    raw = _mapping(gates.get(name))
    if raw:
        return dict(raw)
    review = _mapping(data.get("review"))
    status = review.get(name)
    if status in {"PASS", "FAIL", "PENDING"}:
        return {"status": status}
    return {"status": "PENDING"}


def normalized_studio_review(data: Mapping[str, Any]) -> dict[str, Any]:
    workflow = _mapping(data.get("workflow"))
    raw = _mapping(data.get("studio_review"))
    required = bool(
        raw.get("required")
        if "required" in raw
        else workflow.get("studio_review_required", False)
    )
    return {
        "schema_version": int(raw.get("schema_version") or 1),
        "required": required,
        "candidate_sha256": raw.get("candidate_sha256"),
        "criteria": deepcopy(dict(_mapping(raw.get("criteria")))),
        "evidence": deepcopy(dict(_mapping(raw.get("evidence")))),
        "notes": raw.get("notes"),
    }


def validate_evidence_item(item_id: str, item: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    state = item.get("state")
    if state not in EVIDENCE_STATES:
        errors.append(f"studio_review.evidence.{item_id}.state is invalid")
    history = item.get("history")
    if history is not None:
        if not isinstance(history, list):
            errors.append(f"studio_review.evidence.{item_id}.history must be an array")
        else:
            previous = -1
            for index, event in enumerate(history):
                if not isinstance(event, Mapping):
                    errors.append(
                        f"studio_review.evidence.{item_id}.history[{index}] must be an object"
                    )
                    continue
                event_state = event.get("state")
                if event_state not in EVIDENCE_STATES:
                    errors.append(
                        f"studio_review.evidence.{item_id}.history[{index}].state is invalid"
                    )
                    continue
                rank = EVIDENCE_RANK[str(event_state)]
                if rank < previous:
                    errors.append(
                        f"studio_review.evidence.{item_id}.history cannot move backward"
                    )
                previous = max(previous, rank)
            if history and state in EVIDENCE_STATES:
                if history[-1].get("state") != state:
                    errors.append(
                        f"studio_review.evidence.{item_id}.history must end at current state"
                    )
    return errors


def validate_studio_review(
    review: Mapping[str, Any],
    *,
    candidate_sha256: str | None = None,
) -> list[str]:
    errors: list[str] = []
    normalized = normalized_studio_review({"studio_review": review})
    required = normalized["required"]
    bound = normalized["candidate_sha256"]

    if required and not bound:
        errors.append("studio_review.required review must bind candidate_sha256")
    if candidate_sha256 and bound and bound != candidate_sha256:
        errors.append("studio_review candidate_sha256 does not match current candidate")

    evidence = normalized["evidence"]
    for item_id, item in evidence.items():
        if not isinstance(item_id, str) or not item_id:
            errors.append("studio_review evidence IDs must be non-empty strings")
            continue
        if not isinstance(item, Mapping):
            errors.append(f"studio_review.evidence.{item_id} must be an object")
            continue
        errors.extend(validate_evidence_item(item_id, item))

    criteria = normalized["criteria"]
    if required and not criteria:
        errors.append("studio_review.required review must contain criteria")

    for criterion_id, item in criteria.items():
        if not isinstance(item, Mapping):
            errors.append(f"studio_review.criteria.{criterion_id} must be an object")
            continue
        applicability = item.get("applicability", APPLICABLE)
        if applicability not in APPLICABILITY_STATES:
            errors.append(
                f"studio_review.criteria.{criterion_id}.applicability is invalid"
            )
            continue

        refs = item.get("evidence") or []
        if not isinstance(refs, list) or not all(isinstance(x, str) and x for x in refs):
            errors.append(
                f"studio_review.criteria.{criterion_id}.evidence must be an array of IDs"
            )
            refs = []

        if applicability == NOT_APPLICABLE:
            if not str(item.get("reason") or "").strip():
                errors.append(
                    f"studio_review.criteria.{criterion_id} NOT_APPLICABLE requires reason"
                )
            if item.get("status") not in {None, ""}:
                errors.append(
                    f"studio_review.criteria.{criterion_id} NOT_APPLICABLE must not carry PASS/FAIL/UNVERIFIED"
                )
            continue

        status = item.get("status", UNVERIFIED)
        if status not in CRITERION_STATES:
            errors.append(f"studio_review.criteria.{criterion_id}.status is invalid")
            continue

        unknown_refs = [ref for ref in refs if ref not in evidence]
        if unknown_refs:
            errors.append(
                f"studio_review.criteria.{criterion_id} references unknown evidence: "
                + ", ".join(sorted(unknown_refs))
            )

        blocking = item.get("blocking", True)
        if not isinstance(blocking, bool):
            errors.append(
                f"studio_review.criteria.{criterion_id}.blocking must be boolean"
            )

        if status == PASS and bool(blocking):
            if not refs:
                errors.append(
                    f"studio_review.criteria.{criterion_id} blocking PASS requires evidence"
                )
            for ref in refs:
                evidence_item = evidence.get(ref)
                if isinstance(evidence_item, Mapping) and evidence_item.get("state") != REVIEWED:
                    errors.append(
                        f"studio_review.criteria.{criterion_id} PASS requires REVIEWED evidence {ref}"
                    )

    return errors


def _studio_findings(data: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    review = normalized_studio_review(data)
    if not review["required"]:
        return [], []

    failures: list[str] = []
    unverified: list[str] = []
    candidate_sha = _mapping(data.get("artifacts")).get("candidate_sha256")
    errors = validate_studio_review(review, candidate_sha256=candidate_sha)
    if errors:
        unverified.extend(errors)

    if review["candidate_sha256"] != candidate_sha:
        unverified.append("studio review is stale or not bound to current candidate")

    evidence = review["evidence"]
    for criterion_id, item in review["criteria"].items():
        if not isinstance(item, Mapping):
            continue
        applicability = item.get("applicability", APPLICABLE)
        if applicability == NOT_APPLICABLE:
            continue
        status = item.get("status", UNVERIFIED)
        blocking = item.get("blocking", True) is not False
        if blocking and status == FAIL:
            failures.append(f"criterion:{criterion_id}")
        elif blocking and status == UNVERIFIED:
            unverified.append(f"criterion:{criterion_id}")
        elif blocking and status == PASS:
            refs = item.get("evidence") or []
            if not refs or any(
                not isinstance(evidence.get(ref), Mapping)
                or evidence[ref].get("state") != REVIEWED
                for ref in refs
            ):
                unverified.append(f"criterion:{criterion_id}:evidence_not_reviewed")

    return sorted(set(failures)), sorted(set(unverified))


def promotion_diagnostics(data: Mapping[str, Any]) -> dict[str, Any]:
    artifacts = _mapping(data.get("artifacts"))
    candidate_sha = artifacts.get("candidate_sha256")
    failures: list[str] = []
    unverified: list[str] = []

    technical = _legacy_gate(data, "technical")
    assistant = _legacy_gate(data, "assistant")
    user = _legacy_gate(data, "user")

    technical_status = str(technical.get("status") or "PENDING").upper()
    assistant_status = str(assistant.get("status") or "PENDING").upper()
    user_status = str(user.get("status") or "PENDING").upper()

    if technical_status in FAIL_LIKE:
        failures.append("gate:technical")
    elif technical_status != PASS:
        unverified.append("gate:technical")
    elif candidate_sha and technical.get("candidate_sha256") not in {None, candidate_sha}:
        unverified.append("gate:technical:stale_binding")

    # Any additional gate is authoritative when present. A specialized QA gate
    # may veto promotion even if a legacy assistant field still says PASS.
    gates = _mapping(data.get("gates"))
    for name, raw in gates.items():
        if name in {"technical", "assistant", "user"} or not isinstance(raw, Mapping):
            continue
        status = str(raw.get("status") or "PENDING").upper()
        if status in FAIL_LIKE:
            failures.append(f"gate:{name}")
        elif status in PENDING_LIKE:
            unverified.append(f"gate:{name}")
        if status == PASS and candidate_sha and raw.get("candidate_sha256") not in {None, candidate_sha}:
            unverified.append(f"gate:{name}:stale_binding")

    studio_failures, studio_unverified = _studio_findings(data)
    failures.extend(studio_failures)
    unverified.extend(studio_unverified)

    if assistant_status == FAIL:
        failures.append("gate:assistant")
    elif assistant_status != PASS:
        unverified.append("gate:assistant")
    elif candidate_sha and assistant.get("candidate_sha256") not in {None, candidate_sha}:
        unverified.append("gate:assistant:stale_binding")

    if user_status == FAIL:
        failures.append("gate:user")
    elif user_status == PASS and candidate_sha and user.get("candidate_sha256") not in {None, candidate_sha}:
        unverified.append("gate:user:stale_binding")

    failures = sorted(set(failures))
    unverified = sorted(set(unverified))

    if failures:
        state = REFINEMENT_REQUIRED
    elif unverified:
        state = VERIFICATION_REQUIRED
    elif user_status == PASS:
        state = USER_ACCEPTED
    else:
        state = ASSISTANT_ACCEPTED

    return {
        "state": state,
        "blocking_failures": failures,
        "unverified_requirements": unverified,
        "candidate_sha256": candidate_sha,
    }


def derive_promotion_state(data: Mapping[str, Any]) -> str:
    return str(promotion_diagnostics(data)["state"])


def legacy_review_aliases(data: Mapping[str, Any]) -> dict[str, str]:
    diagnostics = promotion_diagnostics(data)
    state = diagnostics["state"]
    assistant_gate = str(_legacy_gate(data, "assistant").get("status") or "PENDING").upper()
    user_gate = str(_legacy_gate(data, "user").get("status") or "PENDING").upper()

    assistant_alias = PASS if state in {ASSISTANT_ACCEPTED, USER_ACCEPTED} else (
        FAIL if assistant_gate == FAIL else "PENDING"
    )
    user_alias = PASS if state == USER_ACCEPTED else (
        FAIL if user_gate == FAIL else "PENDING"
    )
    return {"assistant": assistant_alias, "user": user_alias}
