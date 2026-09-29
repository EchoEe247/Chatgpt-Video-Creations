"""Contracts for local Blender Render Bundles and deterministic finishing recipes."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any

from src.core.director_execution import BLENDER_PASS_NAMES

BUNDLE_SCHEMA_VERSION = 1
RECIPE_SCHEMA_VERSION = 1
BUNDLE_KIND = "blender-render-bundle"
RECIPE_KIND = "finishing-recipe"
PROTECTION_TYPES = {
    "geometry_protected",
    "appearance_protected",
    "geometry_and_appearance_protected",
}
PROCESSOR_CLASSES = {"P", "S", "G"}
COLOR_STAGES = {"scene_linear", "display_referred"}
READBACK_STATUSES = {"verified"}
FORWARD_AXES = {"+X", "-X", "+Y", "-Y", "+Z", "-Z"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
SAFE_PROCESSOR = re.compile(r"^[a-z][a-z0-9_]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SAFE_ID.fullmatch(value))


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def _canonical_pass(value: Any) -> bool:
    return isinstance(value, str) and (value in BLENDER_PASS_NAMES or (value.startswith("aov:") and _safe_id(value[4:])))


def _safe_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    p = PurePosixPath(value)
    return not p.is_absolute() and ".." not in p.parts


def _vector3(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(_is_number(x) for x in value)


def validate_render_bundle(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {BUNDLE_SCHEMA_VERSION}")
    if data.get("kind") != BUNDLE_KIND:
        errors.append(f"kind must be {BUNDLE_KIND}")
    for key in ("production_id", "shot_id"):
        if not _safe_id(data.get(key)):
            errors.append(f"{key} must be a safe non-empty id")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if not _safe_relative_path(source.get("scene_path")):
            errors.append("source.scene_path must be a safe relative path")
        for key in ("scene_sha256", "execution_plan_sha256"):
            if not _sha(source.get(key)):
                errors.append(f"source.{key} must be a lowercase sha256")

    render = data.get("render")
    frame_start = frame_end = None
    if not isinstance(render, dict):
        errors.append("render must be an object")
    else:
        for key in ("width", "height"):
            value = render.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0 or value % 2:
                errors.append(f"render.{key} must be a positive even integer")
        if not _is_number(render.get("native_fps")) or render.get("native_fps", 0) <= 0:
            errors.append("render.native_fps must be finite and positive")
        frame_start, frame_end = render.get("frame_start"), render.get("frame_end")
        if not isinstance(frame_start, int) or isinstance(frame_start, bool) or frame_start < 0:
            errors.append("render.frame_start must be a nonnegative integer")
        if not isinstance(frame_end, int) or isinstance(frame_end, bool) or frame_end < 0:
            errors.append("render.frame_end must be a nonnegative integer")
        if isinstance(frame_start, int) and isinstance(frame_end, int) and frame_end < frame_start:
            errors.append("render.frame_end must be >= frame_start")
        for key in ("engine", "color_space", "view_transform"):
            if not isinstance(render.get(key), str) or not render[key].strip():
                errors.append(f"render.{key} must be a non-empty string")

    pass_map = data.get("pass_map")
    if not isinstance(pass_map, dict) or not pass_map:
        errors.append("pass_map must be a non-empty object")
        pass_map = {}
    else:
        if "beauty" not in pass_map:
            errors.append("pass_map must include beauty")
        seen_channels: set[str] = set()
        for name, channels in pass_map.items():
            if not _canonical_pass(name):
                errors.append(f"pass_map contains unsupported canonical pass: {name}")
                continue
            if not isinstance(channels, list) or not channels or any(not isinstance(x, str) or not x.strip() for x in channels):
                errors.append(f"pass_map.{name} must be a non-empty string list")
                continue
            if len(channels) != len(set(channels)):
                errors.append(f"pass_map.{name} contains duplicate channels")
            overlap = seen_channels.intersection(channels)
            if overlap:
                errors.append(f"pass_map channel mapped more than once: {sorted(overlap)[0]}")
            seen_channels.update(channels)

    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty list")
    else:
        nums: list[int] = []
        paths: set[str] = set()
        for i, row in enumerate(frames):
            prefix = f"frames[{i}]"
            if not isinstance(row, dict):
                errors.append(f"{prefix} must be an object")
                continue
            frame = row.get("frame")
            if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
                errors.append(f"{prefix}.frame must be a nonnegative integer")
            else:
                nums.append(frame)
            path = row.get("path")
            if not _safe_relative_path(path):
                errors.append(f"{prefix}.path must be a safe relative path")
            elif path in paths:
                errors.append(f"{prefix}.path must be unique")
            else:
                paths.add(path)
            if not _sha(row.get("sha256")):
                errors.append(f"{prefix}.sha256 must be a lowercase sha256")
            if not isinstance(row.get("bytes"), int) or isinstance(row.get("bytes"), bool) or row.get("bytes", 0) <= 0:
                errors.append(f"{prefix}.bytes must be a positive integer")
            if row.get("readback_status") not in READBACK_STATUSES:
                errors.append(f"{prefix}.readback_status must be verified")
        if len(nums) != len(set(nums)):
            errors.append("frames must not repeat frame numbers")
        if isinstance(frame_start, int) and isinstance(frame_end, int) and frame_end >= frame_start:
            expected = list(range(frame_start, frame_end + 1))
            if sorted(nums) != expected:
                errors.append("frames must exactly cover render.frame_start..render.frame_end")

    protections = data.get("protections", [])
    if not isinstance(protections, list):
        errors.append("protections must be a list")
        protections = []
    protection_ids: set[str] = set()
    for i, item in enumerate(protections):
        prefix = f"protections[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pid = item.get("id")
        if not _safe_id(pid) or pid in protection_ids:
            errors.append(f"{prefix}.id must be a unique safe id")
        else:
            protection_ids.add(pid)
        if item.get("type") not in PROTECTION_TYPES:
            errors.append(f"{prefix}.type is invalid")
        source_pass = item.get("source_pass")
        if source_pass not in pass_map:
            errors.append(f"{prefix}.source_pass must exist in pass_map")
        if not isinstance(item.get("selector"), str) or not item["selector"].strip():
            errors.append(f"{prefix}.selector must be non-empty")

    facts = data.get("approved_facts", {})
    if not isinstance(facts, dict):
        errors.append("approved_facts must be an object")
    else:
        if "forward_axis" in facts and facts["forward_axis"] not in FORWARD_AXES:
            errors.append("approved_facts.forward_axis is invalid")
        if "travel_vector" in facts and not _vector3(facts["travel_vector"]):
            errors.append("approved_facts.travel_vector must be a finite 3-vector")
        if "camera_binding_sha256" in facts and not _sha(facts["camera_binding_sha256"]):
            errors.append("approved_facts.camera_binding_sha256 must be a lowercase sha256")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        classes = policy.get("allowed_processor_classes")
        if not isinstance(classes, list) or not classes or any(x not in PROCESSOR_CLASSES for x in classes):
            errors.append("policy.allowed_processor_classes must be a non-empty subset of P/S/G")
        if isinstance(classes, list) and len(classes) != len(set(classes)):
            errors.append("policy.allowed_processor_classes must not contain duplicates")
        prohibited = policy.get("prohibited_transforms")
        if not isinstance(prohibited, list) or any(not isinstance(x, str) or not x.strip() for x in prohibited):
            errors.append("policy.prohibited_transforms must be a string list")

    runtime = data.get("runtime")
    if not isinstance(runtime, dict):
        errors.append("runtime must be an object")
    else:
        for key in ("blender_version", "readback_tool", "platform"):
            if not isinstance(runtime.get(key), str) or not runtime[key].strip():
                errors.append(f"runtime.{key} must be non-empty")
    return errors


def verify_render_bundle_files(data: dict[str, Any], root: str | Path) -> list[str]:
    errors: list[str] = []
    base = Path(root).resolve()
    for i, row in enumerate(data.get("frames", []) if isinstance(data.get("frames"), list) else []):
        path = row.get("path")
        if not _safe_relative_path(path):
            continue
        target = (base / path).resolve()
        try:
            target.relative_to(base)
        except ValueError:
            errors.append(f"frames[{i}].path escapes bundle root")
            continue
        if not target.is_file():
            errors.append(f"frames[{i}] missing file: {path}")
            continue
        size = target.stat().st_size
        if size != row.get("bytes"):
            errors.append(f"frames[{i}] byte size mismatch: {path}")
        if _sha(row.get("sha256")) and sha256_file(target) != row["sha256"]:
            errors.append(f"frames[{i}] sha256 mismatch: {path}")
    return errors


def validate_finishing_recipe(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != RECIPE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {RECIPE_SCHEMA_VERSION}")
    if data.get("kind") != RECIPE_KIND:
        errors.append(f"kind must be {RECIPE_KIND}")
    if not _safe_id(data.get("recipe_id")):
        errors.append("recipe_id must be a safe non-empty id")
    version = data.get("recipe_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("recipe_version must be an integer >= 1")

    operations = data.get("operations")
    if not isinstance(operations, list) or not operations:
        errors.append("operations must be a non-empty list")
        operations = []
    ids: set[str] = set()
    display_seen = False
    for i, op in enumerate(operations):
        prefix = f"operations[{i}]"
        if not isinstance(op, dict):
            errors.append(f"{prefix} must be an object")
            continue
        oid = op.get("id")
        if not _safe_id(oid) or oid in ids:
            errors.append(f"{prefix}.id must be a unique safe id")
        else:
            ids.add(oid)
        processor = op.get("processor")
        if not isinstance(processor, str) or not SAFE_PROCESSOR.fullmatch(processor):
            errors.append(f"{prefix}.processor must be snake_case")
        risk = op.get("risk_class")
        if risk not in PROCESSOR_CLASSES:
            errors.append(f"{prefix}.risk_class must be P, S, or G")
        stage = op.get("color_stage")
        if stage not in COLOR_STAGES:
            errors.append(f"{prefix}.color_stage is invalid")
        elif stage == "display_referred":
            display_seen = True
        elif display_seen:
            errors.append(f"{prefix} scene_linear operation cannot follow display_referred processing")
        inputs = op.get("inputs")
        if not isinstance(inputs, list) or not inputs or any(not _canonical_pass(x) for x in inputs):
            errors.append(f"{prefix}.inputs must be a non-empty list of canonical passes")
        elif len(inputs) != len(set(inputs)):
            errors.append(f"{prefix}.inputs must not contain duplicates")
        masks = op.get("masks", [])
        if not isinstance(masks, list) or any(not _safe_id(x) for x in masks):
            errors.append(f"{prefix}.masks must be a list of safe ids")
        elif len(masks) != len(set(masks)):
            errors.append(f"{prefix}.masks must not contain duplicates")
        params = op.get("params")
        if not isinstance(params, dict):
            errors.append(f"{prefix}.params must be an object")
        elif processor == "agx_display_transform":
            if risk != "P":
                errors.append(f"{prefix} agx_display_transform must use risk class P")
            if stage != "display_referred":
                errors.append(f"{prefix} agx_display_transform must be display_referred")
            if params.get("display") != "sRGB":
                errors.append(f"{prefix}.params.display must be sRGB")
            if params.get("view") != "AgX":
                errors.append(f"{prefix}.params.view must be AgX")
            if params.get("fromspace") != "Linear Rec.709":
                errors.append(f"{prefix}.params.fromspace must be Linear Rec.709")
            if not isinstance(params.get("looks", ""), str):
                errors.append(f"{prefix}.params.looks must be a string")
            for key in ("config_path", "lut_path"):
                if not isinstance(params.get(key), str) or not params[key].startswith("/"):
                    errors.append(f"{prefix}.params.{key} must be an absolute path")
            for key in ("config_sha256", "lut_sha256"):
                if not _sha(params.get(key)):
                    errors.append(f"{prefix}.params.{key} must be a lowercase sha256")
            if not _is_number(params.get("exposure_stops")):
                errors.append(f"{prefix}.params.exposure_stops must be finite")
        if not isinstance(op.get("deterministic"), bool):
            errors.append(f"{prefix}.deterministic must be boolean")
        randomness = op.get("uses_randomness")
        if not isinstance(randomness, bool):
            errors.append(f"{prefix}.uses_randomness must be boolean")
        if randomness and op.get("deterministic") is True and not isinstance(op.get("seed"), int):
            errors.append(f"{prefix}.seed is required for deterministic randomness")
        if risk == "G":
            if not isinstance(op.get("justification"), str) or not op["justification"].strip():
                errors.append(f"{prefix}.justification is required for Class G")
            verification = op.get("verification")
            if not isinstance(verification, list) or not verification or any(not isinstance(x, str) or not x.strip() for x in verification):
                errors.append(f"{prefix}.verification is required for Class G")

    output = data.get("output")
    if not isinstance(output, dict):
        errors.append("output must be an object")
    else:
        if output.get("lossless_format") not in {"OPEN_EXR", "PNG", "TIFF"}:
            errors.append("output.lossless_format must be OPEN_EXR, PNG, or TIFF")
        if output.get("delivery_color_stage") != "display_referred":
            errors.append("output.delivery_color_stage must be display_referred")
    return errors


def validate_recipe_against_bundle(recipe: dict[str, Any], bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    passes = set((bundle.get("pass_map") or {}).keys())
    protections = {x.get("id") for x in bundle.get("protections", []) if isinstance(x, dict)}
    allowed = set((bundle.get("policy") or {}).get("allowed_processor_classes") or [])
    for i, op in enumerate(recipe.get("operations", []) if isinstance(recipe.get("operations"), list) else []):
        if not isinstance(op, dict):
            continue
        for name in op.get("inputs", []) if isinstance(op.get("inputs"), list) else []:
            if name not in passes:
                errors.append(f"operations[{i}] input pass not present in bundle: {name}")
        for mask in op.get("masks", []) if isinstance(op.get("masks"), list) else []:
            if mask not in protections:
                errors.append(f"operations[{i}] mask not present in bundle protections: {mask}")
        risk = op.get("risk_class")
        if risk in PROCESSOR_CLASSES and risk not in allowed:
            errors.append(f"operations[{i}] risk class {risk} is not allowed by bundle policy")
    return errors

def validate_finishing_receipt(
    receipt: dict[str, Any],
    bundle: dict[str, Any],
    recipe: dict[str, Any],
) -> list[str]:
    """Validate a deterministic-finisher receipt against exact input contracts."""
    errors: list[str] = []
    if receipt.get("schema_version") != 1:
        errors.append("receipt.schema_version must be 1")
    if receipt.get("kind") != "finishing-receipt":
        errors.append("receipt.kind must be finishing-receipt")
    expected_bundle = canonical_json_sha256(bundle)
    expected_recipe = canonical_json_sha256(recipe)
    if receipt.get("bundle_sha256") != expected_bundle:
        errors.append("receipt.bundle_sha256 does not match bundle")
    if receipt.get("recipe_sha256") != expected_recipe:
        errors.append("receipt.recipe_sha256 does not match recipe")
    rows = receipt.get("frames")
    if not isinstance(rows, list) or not rows:
        errors.append("receipt.frames must be a non-empty list")
        return errors
    expected_frames = {
        int(row["frame"]): row
        for row in bundle.get("frames", [])
        if isinstance(row, dict) and isinstance(row.get("frame"), int)
    }
    seen: set[int] = set()
    for i, row in enumerate(rows):
        prefix = f"receipt.frames[{i}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        frame = row.get("frame")
        if frame not in expected_frames or frame in seen:
            errors.append(f"{prefix}.frame is unknown or duplicated")
            continue
        seen.add(frame)
        if row.get("source_sha256") != expected_frames[frame].get("sha256"):
            errors.append(f"{prefix}.source_sha256 does not match bundle frame")
        if not _safe_relative_path(row.get("path")):
            errors.append(f"{prefix}.path must be a safe relative path")
        if not _sha(row.get("sha256")):
            errors.append(f"{prefix}.sha256 must be a lowercase sha256")
        if not isinstance(row.get("bytes"), int) or isinstance(row.get("bytes"), bool) or row.get("bytes", 0) <= 0:
            errors.append(f"{prefix}.bytes must be a positive integer")
        if not _safe_relative_path(row.get("preview_path")):
            errors.append(f"{prefix}.preview_path must be a safe relative path")
        if not _sha(row.get("preview_sha256")):
            errors.append(f"{prefix}.preview_sha256 must be a lowercase sha256")
        if row.get("color_stage") not in COLOR_STAGES:
            errors.append(f"{prefix}.color_stage is invalid")
    if seen != set(expected_frames):
        errors.append("receipt.frames must cover every bundle frame exactly")
    return errors


def verify_finishing_receipt_files(receipt: dict[str, Any], root: str | Path) -> list[str]:
    """Verify lossless and preview artifacts bound by a finishing receipt."""
    errors: list[str] = []
    base = Path(root).resolve()
    for i, row in enumerate(receipt.get("frames", []) if isinstance(receipt.get("frames"), list) else []):
        if not isinstance(row, dict):
            continue
        for field, sha_field, bytes_field in (
            ("path", "sha256", "bytes"),
            ("preview_path", "preview_sha256", None),
        ):
            value = row.get(field)
            if not _safe_relative_path(value):
                continue
            target = (base / value).resolve()
            try:
                target.relative_to(base)
            except ValueError:
                errors.append(f"receipt.frames[{i}].{field} escapes output root")
                continue
            if not target.is_file():
                errors.append(f"receipt.frames[{i}] missing output: {value}")
                continue
            if bytes_field and target.stat().st_size != row.get(bytes_field):
                errors.append(f"receipt.frames[{i}] byte size mismatch: {value}")
            expected_sha = row.get(sha_field)
            if _sha(expected_sha) and sha256_file(target) != expected_sha:
                errors.append(f"receipt.frames[{i}] sha256 mismatch: {value}")
    return errors