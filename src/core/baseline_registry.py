from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

BASELINE_ID = re.compile(r"^B([1-9][0-9]*)$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_LANES = {"business", "2d", "3d", "shared"}
PASS_OR_NOT_REQUIRED = {"PASS", "NOT_REQUIRED"}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_nonempty_string(item) for item in value)


def validate_registry(data: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    entries = data.get("validated_baselines")
    if not isinstance(entries, list):
        return errors + ["validated_baselines must be a list"]

    seen_ids: set[str] = set()
    numeric_ids: list[int] = []

    for index, raw in enumerate(entries):
        prefix = f"validated_baselines[{index}]"
        if not isinstance(raw, Mapping):
            errors.append(f"{prefix} must be an object")
            continue

        baseline_id = raw.get("id")
        match = BASELINE_ID.fullmatch(str(baseline_id)) if baseline_id is not None else None
        if not match:
            errors.append(f"{prefix}.id must match B<number>")
        else:
            if baseline_id in seen_ids:
                errors.append(f"{prefix}.id duplicates {baseline_id}")
            seen_ids.add(str(baseline_id))
            numeric_ids.append(int(match.group(1)))

        lane = raw.get("lane")
        if lane not in ALLOWED_LANES:
            errors.append(f"{prefix}.lane must be one of {sorted(ALLOWED_LANES)}")

        if not _nonempty_string(raw.get("scope")):
            errors.append(f"{prefix}.scope must be a non-empty string")

        commit = raw.get("commit")
        if not isinstance(commit, str) or not COMMIT_SHA.fullmatch(commit):
            errors.append(f"{prefix}.commit must be an exact 40-character lowercase commit SHA")

        artifacts = raw.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{prefix}.artifacts must contain at least one exact artifact")
        else:
            for artifact_index, artifact in enumerate(artifacts):
                ap = f"{prefix}.artifacts[{artifact_index}]"
                if not isinstance(artifact, Mapping):
                    errors.append(f"{ap} must be an object")
                    continue
                if not _nonempty_string(artifact.get("ref")):
                    errors.append(f"{ap}.ref must be a stable artifact reference")
                digest = artifact.get("sha256")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(f"{ap}.sha256 must be a lowercase SHA-256 digest")

        conditions = raw.get("conditions")
        if not isinstance(conditions, Mapping) or not conditions:
            errors.append(f"{prefix}.conditions must be a non-empty object")

        if not _string_list(raw.get("validated_capabilities")) or not raw.get("validated_capabilities"):
            errors.append(f"{prefix}.validated_capabilities must be a non-empty string list")

        for field in ("known_limitations", "not_validated"):
            if not _string_list(raw.get(field)):
                errors.append(f"{prefix}.{field} must be a string list")

        if raw.get("technical_validation") != "PASS":
            errors.append(f"{prefix}.technical_validation must be PASS")

        visual = raw.get("visual_validation")
        if visual not in PASS_OR_NOT_REQUIRED:
            errors.append(f"{prefix}.visual_validation must be PASS or NOT_REQUIRED")

        user_review = raw.get("user_review")
        if user_review not in PASS_OR_NOT_REQUIRED:
            errors.append(f"{prefix}.user_review must be PASS or NOT_REQUIRED")
        if visual == "PASS" and user_review != "PASS":
            errors.append(f"{prefix}.user_review must be PASS when visual_validation is PASS")

        if not _nonempty_string(raw.get("receipt")):
            errors.append(f"{prefix}.receipt must identify a durable validation receipt")

    expected_next = f"B{max(numeric_ids, default=0) + 1}"
    if data.get("next_id") != expected_next:
        errors.append(f"next_id must be {expected_next}")
    return errors


def next_baseline_id(data: Mapping[str, Any]) -> str:
    entries = data.get("validated_baselines", [])
    if not isinstance(entries, Sequence):
        raise ValueError("validated_baselines must be a sequence")
    numbers: list[int] = []
    for entry in entries:
        if isinstance(entry, Mapping):
            match = BASELINE_ID.fullmatch(str(entry.get("id", "")))
            if match:
                numbers.append(int(match.group(1)))
    return f"B{max(numbers, default=0) + 1}"
