#!/usr/bin/env python3
"""Deterministic pass-aware finishing worker for hermes-ubuntu.

This guest-side worker intentionally depends on Ubuntu's python3-openimageio
and NumPy. The host-side finishingctl validates the Render Bundle and recipe
before dispatching it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import OpenImageIO as oiio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.core.finishing_math import (
    depth_atmosphere_rgb,
    emission_rebalance_rgb,
    reinhard_srgb_rgb,
    selective_exposure_rgb,
)


@dataclass(frozen=True)
class DecodedFrame:
    channel_names: tuple[str, ...]
    pixels: np.ndarray
    attributes: dict[str, object]


def read_frame(path: Path) -> DecodedFrame:
    """Decode one multilayer EXR exactly once through ImageInput."""
    source = oiio.ImageInput.open(str(path))
    if source is None:
        raise ValueError(f"could not open EXR: {path}")
    try:
        spec = source.spec()
        pixels = source.read_image(oiio.FLOAT)
        if pixels is None:
            raise ValueError(f"could not decode EXR: {path}")
        attrs = {attr.name: attr.value for attr in spec.extra_attribs}
        names = tuple(spec.channelnames)
    finally:
        source.close()
    arr = np.asarray(pixels, dtype=np.float32)
    if arr.ndim == 4:
        arr = arr[0]
    return DecodedFrame(channel_names=names, pixels=arr, attributes=attrs)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def channels(src: DecodedFrame, names: list[str]) -> np.ndarray:
    all_names = list(src.channel_names)
    missing = [name for name in names if name not in all_names]
    if missing:
        raise ValueError(f"missing EXR channels: {missing}")
    order = [all_names.index(name) for name in names]
    return src.pixels[..., order]


def cryptomatte_id(hex_hash: str) -> np.float32:
    return np.float32(struct.unpack("!f", struct.pack("!I", int(hex_hash, 16)))[0])


def cryptomatte_mask(src: DecodedFrame, channel_names: list[str], selector: str) -> np.ndarray:
    manifest = None
    prefix = None
    for name, value in src.attributes.items():
        if name.endswith("/name") and value == "ViewLayer.CryptoObject":
            prefix = name.rsplit("/", 1)[0]
            break
    if prefix:
        raw_manifest = src.attributes.get(prefix + "/manifest")
        if raw_manifest:
            manifest = json.loads(raw_manifest)
    if not manifest or selector not in manifest:
        raise ValueError(f"cryptomatte selector not present: {selector}")
    target = cryptomatte_id(manifest[selector])
    data = channels(src, channel_names)
    if data.shape[-1] % 2:
        raise ValueError("cryptomatte channel list must contain id/coverage pairs")
    mask = np.zeros(data.shape[:2], dtype=np.float32)
    for i in range(0, data.shape[-1], 2):
        ids = data[..., i]
        coverage = data[..., i + 1]
        mask += np.where(ids == target, coverage, 0.0).astype(np.float32)
    return np.clip(mask, 0.0, 1.0)


def write_exr(path: Path, rgba: np.ndarray, color_space: str) -> None:
    h, w, c = rgba.shape
    if c != 4:
        raise ValueError("finished array must be RGBA")
    spec = oiio.ImageSpec(w, h, 4, oiio.TypeDesc.TypeFloat)
    spec.channelnames = ("R", "G", "B", "A")
    spec.attribute("oiio:ColorSpace", color_space)
    spec.attribute("DateTime", "1970:01:01 00:00:00")
    spec.attribute("Software", "Chatgpt-Video-Creations deterministic finishing v1")
    buf = oiio.ImageBuf(spec)
    roi = oiio.ROI(0, w, 0, h, 0, 1, 0, 4)
    if not buf.set_pixels(roi, np.ascontiguousarray(rgba.astype(np.float32))):
        raise RuntimeError("OpenImageIO set_pixels failed")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not buf.write(str(path), oiio.HALF):
        raise RuntimeError("OpenImageIO EXR write failed: " + buf.geterror())


def write_png(path: Path, rgba: np.ndarray) -> None:
    arr = np.clip(rgba, 0.0, 1.0)
    h, w, c = arr.shape
    spec = oiio.ImageSpec(w, h, c, oiio.TypeDesc.TypeFloat)
    spec.channelnames = ("R", "G", "B", "A")
    spec.attribute("oiio:ColorSpace", "sRGB")
    buf = oiio.ImageBuf(spec)
    if not buf.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, c), np.ascontiguousarray(arr)):
        raise RuntimeError("OpenImageIO set_pixels failed for PNG")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not buf.write(str(path), oiio.UINT8):
        raise RuntimeError("OpenImageIO PNG write failed: " + buf.geterror())


def apply_operation(rgba, src, bundle, op, masks):
    rgb = rgba[..., :3]
    processor = op["processor"]
    p = op.get("params") or {}

    if processor == "depth_atmosphere":
        depth = channels(src, bundle["pass_map"]["depth"])[..., 0]
        rgb[:] = depth_atmosphere_rgb(
            rgb,
            depth,
            near=float(p.get("near", 0.0)),
            density=float(p.get("density", 0.03)),
            max_amount=float(p.get("max_amount", 0.72)),
            color=p.get("color", [0.08, 0.12, 0.18]),
        )
    elif processor == "emission_rebalance":
        emission = channels(src, bundle["pass_map"]["emission"])[..., :3]
        rgb[:] = emission_rebalance_rgb(rgb, emission, gain=float(p.get("gain", 1.0)))
    elif processor == "selective_grade":
        if not op.get("masks"):
            raise ValueError("selective_grade requires a mask")
        rgb[:] = selective_exposure_rgb(
            rgb,
            masks[op["masks"][0]],
            exposure_stops=float(p.get("exposure_stops", 0.0)),
        )
    elif processor == "display_transform":
        if p.get("curve", "reinhard_srgb") != "reinhard_srgb":
            raise ValueError("display_transform curve must be reinhard_srgb")
        rgb[:] = reinhard_srgb_rgb(rgb, exposure_stops=float(p.get("exposure_stops", 0.0)))
    else:
        raise ValueError(f"unsupported deterministic processor: {processor}")
    return rgba

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", required=True)
    p.add_argument("--recipe", required=True)
    p.add_argument("--bundle-root", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    bundle = json.loads(Path(args.bundle).read_text())
    recipe = json.loads(Path(args.recipe).read_text())
    bundle_hash = canonical_sha(bundle)
    recipe_hash = canonical_sha(recipe)
    root = Path(args.bundle_root).resolve()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    prior_path = out / "finishing-receipt.json"
    prior = {}
    if prior_path.is_file():
        try:
            prior = json.loads(prior_path.read_text())
        except Exception:
            prior = {}
    prior_frames = {int(x["frame"]): x for x in prior.get("frames", []) if "frame" in x}

    results = []
    for row in bundle["frames"]:
        frame = int(row["frame"])
        source_path = (root / row["path"]).resolve()
        output_path = out / f"frame-{frame:04d}.exr"
        preview_path = out / f"frame-{frame:04d}.png"
        prior_row = prior_frames.get(frame)
        if (
            prior.get("bundle_sha256") == bundle_hash
            and prior.get("recipe_sha256") == recipe_hash
            and prior_row
            and output_path.is_file()
            and preview_path.is_file()
            and sha256_file(output_path) == prior_row.get("sha256")
            and sha256_file(preview_path) == prior_row.get("preview_sha256")
        ):
            results.append({**prior_row, "skipped_existing": True})
            print(f"FINISH_SKIP frame={frame}", flush=True)
            continue

        if sha256_file(source_path) != row["sha256"]:
            raise ValueError(f"source frame sha mismatch: {row['path']}")
        src = read_frame(source_path)
        beauty = channels(src, bundle["pass_map"]["beauty"])
        if beauty.shape[-1] == 3:
            alpha = np.ones((*beauty.shape[:2], 1), dtype=np.float32)
            rgba = np.concatenate((beauty, alpha), axis=-1)
        else:
            rgba = beauty[..., :4].copy()

        masks = {}
        protection_by_id = {x["id"]: x for x in bundle.get("protections", [])}
        for op in recipe["operations"]:
            for mask_id in op.get("masks", []):
                if mask_id in masks:
                    continue
                protection = protection_by_id[mask_id]
                if protection["source_pass"] == "cryptomatte_object":
                    masks[mask_id] = cryptomatte_mask(
                        src,
                        bundle["pass_map"]["cryptomatte_object"],
                        protection["selector"],
                    )
                else:
                    raise ValueError(f"unsupported mask source pass: {protection['source_pass']}")

        started = time.monotonic()
        current_stage = "scene_linear"
        for op in recipe["operations"]:
            rgba = apply_operation(rgba, src, bundle, op, masks)
            current_stage = op["color_stage"]
        elapsed = time.monotonic() - started
        write_exr(output_path, rgba, "sRGB" if current_stage == "display_referred" else "Linear")
        preview = rgba.copy()
        if current_stage == "scene_linear":
            x = np.maximum(preview[..., :3], 0.0)
            x = x / (1.0 + x)
            preview[..., :3] = np.where(
                x <= 0.0031308,
                x * 12.92,
                1.055 * np.power(x, 1.0 / 2.4) - 0.055,
            )
        write_png(preview_path, preview)
        result = {
            "frame": frame,
            "source_sha256": row["sha256"],
            "path": output_path.name,
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
            "preview_path": preview_path.name,
            "preview_sha256": sha256_file(preview_path),
            "process_seconds": round(elapsed, 4),
            "color_stage": current_stage,
            "skipped_existing": False,
        }
        results.append(result)
        print(f"FINISH_FRAME frame={frame} seconds={elapsed:.3f}", flush=True)

    receipt = {
        "schema_version": 1,
        "kind": "finishing-receipt",
        "bundle_sha256": bundle_hash,
        "recipe_sha256": recipe_hash,
        "worker": "OpenImageIO-python deterministic MVP",
        "openimageio_version": oiio.VERSION_STRING,
        "numpy_version": np.__version__,
        "frames": results,
    }
    prior_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print("FINISH_RECEIPT=" + str(prior_path), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())