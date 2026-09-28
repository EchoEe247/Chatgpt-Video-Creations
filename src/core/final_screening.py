from __future__ import annotations

from typing import Any, Mapping

APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
PASS = "PASS"
FAIL = "FAIL"
UNVERIFIED = "UNVERIFIED"

DEPARTMENTS = (
    "director_story",
    "cinematography",
    "animation_physics",
    "continuity",
    "editing",
    "vfx",
    "sound",
    "music",
    "dialogue_narration",
    "mix_master",
    "delivery",
)

MODALITIES = (
    "still_image",
    "sampled_temporal",
    "continuous_video",
    "auditory",
    "synchronized_av",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _intervals_cover_duration(intervals: list[Any], duration: float, tolerance: float = 0.05) -> bool:
    normalized: list[tuple[float, float]] = []
    for raw in intervals:
        if not isinstance(raw, Mapping):
            continue
        try:
            start = max(0.0, float(raw["start_seconds"]))
            end = min(duration, float(raw["end_seconds"]))
        except (KeyError, TypeError, ValueError):
            continue
        if end > start:
            normalized.append((start, end))
    if not normalized:
        return False
    normalized.sort()
    cursor = 0.0
    for start, end in normalized:
        if start > cursor + tolerance:
            return False
        cursor = max(cursor, end)
    return cursor >= duration - tolerance


def _validate_applicable_record(
    prefix: str,
    record: Mapping[str, Any],
    *,
    require_evidence_for_pass: bool = True,
) -> list[str]:
    errors: list[str] = []
    applicability = record.get("applicability", APPLICABLE)
    if applicability not in {APPLICABLE, NOT_APPLICABLE}:
        return [f"{prefix}.applicability is invalid"]
    if applicability == NOT_APPLICABLE:
        if not str(record.get("reason") or "").strip():
            errors.append(f"{prefix} NOT_APPLICABLE requires reason")
        if record.get("status") not in {None, ""}:
            errors.append(f"{prefix} NOT_APPLICABLE must not carry PASS/FAIL/UNVERIFIED")
        return errors

    status = record.get("status", UNVERIFIED)
    if status not in {PASS, FAIL, UNVERIFIED}:
        errors.append(f"{prefix}.status is invalid")
    evidence = record.get("evidence") or []
    if not isinstance(evidence, list) or not all(isinstance(x, str) and x for x in evidence):
        errors.append(f"{prefix}.evidence must be an array of IDs")
        evidence = []
    if status == PASS and require_evidence_for_pass and not evidence:
        errors.append(f"{prefix} PASS requires evidence")
    return errors


def validate_final_screening(
    review: Mapping[str, Any],
    *,
    candidate_sha256: str | None,
    duration_seconds: float | None,
    audio_required: bool | None = None,
) -> list[str]:
    errors: list[str] = []
    screening = _mapping(review.get("final_screening"))
    if not screening:
        return ["studio_review.final_screening is required"]
    if screening.get("candidate_sha256") != candidate_sha256:
        errors.append("studio_review.final_screening candidate binding is stale")

    try:
        duration = float(screening.get("duration_seconds"))
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        errors.append("studio_review.final_screening.duration_seconds must be positive")
    if duration_seconds and duration > 0 and abs(duration - float(duration_seconds)) > 0.25:
        errors.append("studio_review.final_screening duration does not match candidate")

    departments = _mapping(screening.get("departments"))
    for name in DEPARTMENTS:
        record = departments.get(name)
        if not isinstance(record, Mapping):
            errors.append(f"studio_review.final_screening.departments.{name} is required")
            continue
        errors.extend(
            _validate_applicable_record(
                f"studio_review.final_screening.departments.{name}",
                record,
            )
        )
        observations = record.get("observations")
        if record.get("applicability", APPLICABLE) == APPLICABLE:
            if not isinstance(observations, list):
                errors.append(
                    f"studio_review.final_screening.departments.{name}.observations must be an array"
                )
            claim_types = record.get("claim_types") or []
            if not isinstance(claim_types, list) or not all(
                x in {"perceived", "measured", "inferred"} for x in claim_types
            ):
                errors.append(
                    f"studio_review.final_screening.departments.{name}.claim_types is invalid"
                )

    modalities = _mapping(screening.get("modalities"))
    coverage = _mapping(screening.get("coverage"))
    for name in MODALITIES:
        record = modalities.get(name)
        if not isinstance(record, Mapping):
            errors.append(f"studio_review.final_screening.modalities.{name} is required")
            continue
        errors.extend(
            _validate_applicable_record(
                f"studio_review.final_screening.modalities.{name}",
                record,
                require_evidence_for_pass=True,
            )
        )
        if name == "continuous_video" and record.get("applicability", APPLICABLE) == NOT_APPLICABLE:
            errors.append("studio_review.final_screening continuous_video is required for video final screening")
        if audio_required is True and name in {"auditory", "synchronized_av"} and record.get("applicability", APPLICABLE) == NOT_APPLICABLE:
            errors.append(f"studio_review.final_screening {name} is required when delivery audio is required")
        if record.get("applicability", APPLICABLE) == APPLICABLE and record.get("status") == PASS:
            ranges = coverage.get(name)
            if not isinstance(ranges, list):
                errors.append(
                    f"studio_review.final_screening.coverage.{name} must be an array"
                )
            elif name in {"continuous_video", "auditory", "synchronized_av"} and duration > 0:
                if not _intervals_cover_duration(ranges, duration):
                    errors.append(
                        f"studio_review.final_screening.coverage.{name} does not cover full candidate"
                    )

    evidence_ids = screening.get("evidence_ids") or []
    if not isinstance(evidence_ids, list) or not all(isinstance(x, str) and x for x in evidence_ids):
        errors.append("studio_review.final_screening.evidence_ids must be an array")
        evidence_ids = []

    opening = screening.get("opening_reviewed")
    ending = screening.get("ending_reviewed")
    if opening is not True:
        errors.append("studio_review.final_screening opening must be reviewed")
    if ending is not True:
        errors.append("studio_review.final_screening ending must be reviewed")

    authored = _mapping(screening.get("authored_points"))
    planned = authored.get("planned_ids") or []
    reviewed = authored.get("reviewed_ids") or []
    if not isinstance(planned, list) or not isinstance(reviewed, list):
        errors.append("studio_review.final_screening.authored_points ids must be arrays")
    else:
        missing = sorted(set(map(str, planned)) - set(map(str, reviewed)))
        if missing:
            errors.append(
                "studio_review.final_screening authored points are not fully reviewed: "
                + ", ".join(missing[:20])
            )

    second = _mapping(screening.get("second_pass"))
    required = bool(second.get("required"))
    if required:
        if second.get("status") != PASS:
            errors.append("studio_review.final_screening required second pass is not PASS")
        targets = second.get("targets") or []
        disposed = second.get("disposed_ids") or []
        if not isinstance(targets, list) or not isinstance(disposed, list):
            errors.append("studio_review.final_screening second-pass target/disposition IDs must be arrays")
        else:
            target_ids = {
                str(x.get("id"))
                for x in targets
                if isinstance(x, Mapping) and x.get("id")
            }
            missing = sorted(target_ids - set(map(str, disposed)))
            if missing:
                errors.append(
                    "studio_review.final_screening second-pass targets are unresolved: "
                    + ", ".join(missing[:20])
                )

    declaration = _mapping(screening.get("declaration"))
    if declaration.get("reviewer") not in {"model", "human", "model_plus_human"}:
        errors.append("studio_review.final_screening.declaration.reviewer is invalid")
    if not str(declaration.get("reviewed_at") or "").strip():
        errors.append("studio_review.final_screening.declaration.reviewed_at is required")
    if not isinstance(declaration.get("modalities_actually_perceived"), list):
        errors.append(
            "studio_review.final_screening.declaration.modalities_actually_perceived must be an array"
        )
    if declaration.get("candidate_sha256") != candidate_sha256:
        errors.append("studio_review.final_screening declaration candidate binding is stale")
    perceived = declaration.get("modalities_actually_perceived")
    if isinstance(perceived, list):
        perceived_set = set(map(str, perceived))
        for name in MODALITIES:
            record = modalities.get(name)
            if (
                isinstance(record, Mapping)
                and record.get("applicability", APPLICABLE) == APPLICABLE
                and record.get("status") == PASS
                and name not in perceived_set
            ):
                errors.append(
                    f"studio_review.final_screening modality {name} PASS is not declared as actually perceived"
                )

    allowed_ids = set(map(str, evidence_ids))
    for name, record in departments.items():
        if isinstance(record, Mapping) and record.get("applicability", APPLICABLE) == APPLICABLE and record.get("status") == PASS:
            missing_refs = sorted(set(map(str, record.get("evidence") or [])) - allowed_ids)
            if missing_refs:
                errors.append(
                    f"studio_review.final_screening department {name} references evidence outside screening evidence_ids: "
                    + ", ".join(missing_refs)
                )
    for name, record in modalities.items():
        if isinstance(record, Mapping) and record.get("applicability", APPLICABLE) == APPLICABLE and record.get("status") == PASS:
            missing_refs = sorted(set(map(str, record.get("evidence") or [])) - allowed_ids)
            if missing_refs:
                errors.append(
                    f"studio_review.final_screening modality {name} references evidence outside screening evidence_ids: "
                    + ", ".join(missing_refs)
                )

    return errors


def final_screening_findings(
    data: Mapping[str, Any],
    review: Mapping[str, Any],
) -> tuple[list[str], list[str]]:
    artifacts = _mapping(data.get("artifacts"))
    delivery = _mapping(data.get("delivery"))
    errors = validate_final_screening(
        review,
        candidate_sha256=artifacts.get("candidate_sha256"),
        duration_seconds=delivery.get("expected_duration_seconds"),
        audio_required=delivery.get("audio_required") if isinstance(delivery.get("audio_required"), bool) else None,
    )
    failures: list[str] = []
    unverified: list[str] = list(errors)
    screening = _mapping(review.get("final_screening"))

    for group_name in ("departments", "modalities"):
        group = _mapping(screening.get(group_name))
        for name, record in group.items():
            if not isinstance(record, Mapping):
                continue
            if record.get("applicability", APPLICABLE) == NOT_APPLICABLE:
                continue
            status = record.get("status", UNVERIFIED)
            if status == FAIL:
                failures.append(f"final_screening:{group_name}:{name}")
            elif status == UNVERIFIED:
                unverified.append(f"final_screening:{group_name}:{name}")

    return sorted(set(failures)), sorted(set(unverified))


def make_blind_audit_package(
    review_bundle: Mapping[str, Any],
    *,
    requirements: list[str],
) -> dict[str, Any]:
    """Return a neutral package without prior findings, repairs, or answer keys."""
    return {
        "schema_version": 1,
        "purpose": "controlled_perception_benchmark",
        "candidate_sha256": review_bundle.get("candidate_sha256"),
        "candidate_duration_seconds": review_bundle.get("candidate_duration_seconds"),
        "requirements": list(requirements),
        "evidence_ids": [
            str(x.get("id"))
            for x in (review_bundle.get("evidence") or [])
            if isinstance(x, Mapping) and x.get("id")
        ],
        "allowed_context": [
            "candidate",
            "neutral requirements",
            "review tools",
            "fixture IDs",
        ],
        "excluded_context": [
            "prior audit findings",
            "repair history",
            "triage findings",
            "answer keys",
            "user withheld issue",
        ],
        "contamination_status": "UNKNOWN",
        "findings_frozen_before_reveal": False,
    }
