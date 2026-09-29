import hashlib
import json
from pathlib import Path

from src.core.finishing_contract import (
    canonical_json_sha256,
    validate_finishing_recipe,
    validate_recipe_against_bundle,
    validate_render_bundle,
    verify_render_bundle_files,
)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_bundle(tmp_path: Path) -> dict:
    frame_dir = tmp_path / "frames"
    frame_dir.mkdir()
    frames = []
    for n in (1, 2, 3):
        payload = f"frame-{n}".encode()
        path = frame_dir / f"frame-{n:04d}.exr"
        path.write_bytes(payload)
        frames.append(
            {
                "frame": n,
                "path": f"frames/frame-{n:04d}.exr",
                "sha256": _sha_bytes(payload),
                "bytes": len(payload),
                "readback_status": "verified",
            }
        )
    return {
        "schema_version": 1,
        "kind": "blender-render-bundle",
        "production_id": "prod",
        "shot_id": "shot-01",
        "source": {
            "scene_path": "source/scene.blend",
            "scene_sha256": "0" * 64,
            "execution_plan_sha256": "1" * 64,
        },
        "render": {
            "engine": "CYCLES",
            "width": 1280,
            "height": 720,
            "native_fps": 24,
            "frame_start": 1,
            "frame_end": 3,
            "color_space": "scene_linear",
            "view_transform": "AgX",
        },
        "pass_map": {
            "beauty": ["ViewLayer.Combined.R"],
            "depth": ["ViewLayer.Depth.Z"],
            "vector": ["ViewLayer.Vector.X", "ViewLayer.Vector.Y"],
            "cryptomatte_object": ["ViewLayer.CryptoObject00.r"],
        },
        "frames": frames,
        "protections": [
            {
                "id": "hero",
                "type": "geometry_protected",
                "source_pass": "cryptomatte_object",
                "selector": "Hero",
            }
        ],
        "approved_facts": {
            "forward_axis": "+X",
            "travel_vector": [1, 0, 0],
            "camera_binding_sha256": "2" * 64,
        },
        "policy": {
            "allowed_processor_classes": ["P", "S"],
            "prohibited_transforms": ["identity_change"],
        },
        "runtime": {
            "blender_version": "4.0.2",
            "readback_tool": "oiiotool",
            "platform": "termux",
        },
    }


def valid_recipe() -> dict:
    return {
        "schema_version": 1,
        "kind": "finishing-recipe",
        "recipe_id": "recipe",
        "recipe_version": 1,
        "operations": [
            {
                "id": "depth",
                "processor": "depth_atmosphere",
                "risk_class": "S",
                "color_stage": "scene_linear",
                "inputs": ["beauty", "depth"],
                "masks": [],
                "params": {},
                "deterministic": True,
                "uses_randomness": False,
                "seed": None,
            },
            {
                "id": "grain",
                "processor": "film_grain",
                "risk_class": "P",
                "color_stage": "display_referred",
                "inputs": ["beauty"],
                "masks": ["hero"],
                "params": {},
                "deterministic": True,
                "uses_randomness": True,
                "seed": 7,
            },
        ],
        "output": {
            "lossless_format": "OPEN_EXR",
            "delivery_color_stage": "display_referred",
        },
    }


def test_valid_bundle_recipe_and_files(tmp_path):
    bundle = valid_bundle(tmp_path)
    recipe = valid_recipe()
    assert validate_render_bundle(bundle) == []
    assert verify_render_bundle_files(bundle, tmp_path) == []
    assert validate_finishing_recipe(recipe) == []
    assert validate_recipe_against_bundle(recipe, bundle) == []
    assert len(canonical_json_sha256(bundle)) == 64


def test_bundle_requires_exact_frame_coverage(tmp_path):
    bundle = valid_bundle(tmp_path)
    bundle["frames"].pop()
    assert "frames must exactly cover render.frame_start..render.frame_end" in validate_render_bundle(bundle)


def test_bundle_rejects_unsafe_path_and_unknown_pass(tmp_path):
    bundle = valid_bundle(tmp_path)
    bundle["source"]["scene_path"] = "../scene.blend"
    bundle["pass_map"]["magic"] = ["ViewLayer.Magic.X"]
    errors = validate_render_bundle(bundle)
    assert "source.scene_path must be a safe relative path" in errors
    assert "pass_map contains unsupported canonical pass: magic" in errors


def test_bundle_file_verification_detects_tamper(tmp_path):
    bundle = valid_bundle(tmp_path)
    (tmp_path / bundle["frames"][1]["path"]).write_bytes(b"tampered")
    errors = verify_render_bundle_files(bundle, tmp_path)
    assert any("byte size mismatch" in x for x in errors)
    assert any("sha256 mismatch" in x for x in errors)


def test_recipe_rejects_scene_linear_after_display():
    recipe = valid_recipe()
    recipe["operations"].append(
        {
            "id": "late-linear",
            "processor": "selective_grade",
            "risk_class": "P",
            "color_stage": "scene_linear",
            "inputs": ["beauty"],
            "masks": [],
            "params": {},
            "deterministic": True,
            "uses_randomness": False,
            "seed": None,
        }
    )
    assert any("scene_linear operation cannot follow display_referred" in x for x in validate_finishing_recipe(recipe))


def test_recipe_requires_seed_for_deterministic_randomness():
    recipe = valid_recipe()
    recipe["operations"][1]["seed"] = None
    assert any("seed is required for deterministic randomness" in x for x in validate_finishing_recipe(recipe))


def test_class_g_requires_justification_and_verification():
    recipe = valid_recipe()
    recipe["operations"][0]["risk_class"] = "G"
    errors = validate_finishing_recipe(recipe)
    assert any("justification is required for Class G" in x for x in errors)
    assert any("verification is required for Class G" in x for x in errors)


def test_pair_rejects_missing_pass_mask_and_disallowed_class(tmp_path):
    bundle = valid_bundle(tmp_path)
    recipe = valid_recipe()
    recipe["operations"][0]["inputs"].append("normal")
    recipe["operations"][1]["masks"] = ["missing"]
    recipe["operations"][0]["risk_class"] = "G"
    recipe["operations"][0]["justification"] = "test"
    recipe["operations"][0]["verification"] = ["geometry"]
    errors = validate_recipe_against_bundle(recipe, bundle)
    assert any("input pass not present" in x for x in errors)
    assert any("mask not present" in x for x in errors)
    assert any("risk class G is not allowed" in x for x in errors)


def test_templates_are_structurally_valid():
    root = Path(__file__).resolve().parents[1]
    bundle = json.loads((root / "templates/finishing/render-bundle-v1.json").read_text())
    recipe = json.loads((root / "templates/finishing/recipe-v1.json").read_text())
    assert validate_render_bundle(bundle) == []
    assert validate_finishing_recipe(recipe) == []
    assert validate_recipe_against_bundle(recipe, bundle) == []
