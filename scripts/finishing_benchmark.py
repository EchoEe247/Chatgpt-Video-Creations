#!/usr/bin/env python3
"""Build a three-arm local finishing benchmark.

A = Blender beauty with only the recipe's display transform.
B = A plus conventional deterministic FFmpeg post.
C = the full pass-aware finishing recipe.

The harness reports deltas but never declares a visual winner. When an execution
plan is supplied, it reuses creativeqactl compare for the decisive B->C review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.finishing_contract import canonical_json_sha256, validate_finishing_recipe


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(
        argv,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def require_ok(proc: subprocess.CompletedProcess, label: str) -> None:
    if proc.returncode:
        detail = (proc.stderr or proc.stdout or f"{label} failed")[-5000:]
        raise RuntimeError(f"{label}: {detail}")


def baseline_recipe(recipe: dict) -> dict:
    display = [
        op for op in recipe.get("operations", [])
        if isinstance(op, dict) and op.get("processor") == "display_transform"
    ]
    if len(display) != 1:
        raise ValueError("benchmark requires exactly one display_transform operation")
    op = dict(display[0])
    op["id"] = "baseline-display"
    return {
        "schema_version": 1,
        "kind": "finishing-recipe",
        "recipe_id": f"{recipe['recipe_id']}-beauty-baseline",
        "recipe_version": 1,
        "operations": [op],
        "output": dict(recipe["output"]),
    }


def png_delta(left: Path, right: Path) -> dict:
    a = np.asarray(Image.open(left).convert("RGB"), dtype=np.float32)
    b = np.asarray(Image.open(right).convert("RGB"), dtype=np.float32)
    if a.shape != b.shape:
        raise ValueError(f"benchmark image geometry mismatch: {left.name} vs {right.name}")
    d = np.abs(a - b) / 255.0
    return {
        "mean": round(float(d.mean()), 6),
        "p95": round(float(np.percentile(d, 95)), 6),
        "max": round(float(d.max()), 6),
    }


def encode_sequence(sequence: Path, output: Path, fps: float, frame_count: int) -> None:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")
    duration = frame_count / fps
    proc = run([
        "ffmpeg", "-y", "-v", "error",
        "-framerate", str(fps),
        "-i", str(sequence),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-t", f"{duration:.9f}",
        str(output),
    ])
    require_ok(proc, f"encode {output.name}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle")
    p.add_argument("recipe")
    p.add_argument("output_dir")
    p.add_argument("--root", default="")
    p.add_argument("--execution-plan")
    p.add_argument("--review-fps", type=float, default=0.0)
    p.add_argument("--timeout", type=int, default=600)
    args = p.parse_args()

    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required")
    bundle_path = Path(args.bundle).expanduser().resolve()
    recipe_path = Path(args.recipe).expanduser().resolve()
    bundle = json.loads(bundle_path.read_text())
    recipe = json.loads(recipe_path.read_text())
    recipe_errors = validate_finishing_recipe(recipe)
    if recipe_errors:
        raise SystemExit("invalid recipe: " + "; ".join(recipe_errors))
    bundle_root = Path(args.root).expanduser().resolve() if args.root else bundle_path.parent
    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    base_recipe = baseline_recipe(recipe)
    base_recipe_path = out / "arm-a-recipe.json"
    base_recipe_path.write_text(json.dumps(base_recipe, indent=2) + "\n")

    arm_a = out / "arm-a-beauty"
    arm_b = out / "arm-b-conventional"
    arm_c = out / "arm-c-pass-aware"
    arm_b.mkdir(parents=True, exist_ok=True)

    benchmark_worker = ROOT / "scripts" / "finishing_benchmark_worker.py"
    for target, selected_recipe, label in (
        (arm_a, base_recipe_path, "arm A"),
        (arm_c, recipe_path, "arm C"),
    ):
        proc = run(
            [
                "proot-distro", "login", "hermes-ubuntu", "--",
                "python3", str(benchmark_worker),
                "--bundle", str(bundle_path),
                "--recipe", str(selected_recipe),
                "--bundle-root", str(bundle_root),
                "--output-dir", str(target),
            ],
            timeout=args.timeout,
        )
        require_ok(proc, label)

    frame_numbers = [int(row["frame"]) for row in bundle["frames"]]
    for frame in frame_numbers:
        source = arm_a / f"frame-{frame:04d}.png"
        target = arm_b / f"frame-{frame:04d}.png"
        proc = run([
            "ffmpeg", "-y", "-v", "error", "-i", str(source),
            "-vf",
            "curves=all='0/0 0.25/0.22 0.5/0.54 0.75/0.82 1/1',eq=saturation=1.04:contrast=1.03,vignette=PI/16",
            "-frames:v", "1", str(target),
        ])
        require_ok(proc, f"conventional post frame {frame}")

    review_fps = float(args.review_fps or bundle["render"]["native_fps"])
    if review_fps <= 0:
        raise ValueError("review fps must be positive")
    media = {}
    for key, directory in (
        ("A", arm_a),
        ("B", arm_b),
        ("C", arm_c),
    ):
        output = out / f"arm-{key.lower()}.mp4"
        encode_sequence(directory / "frame-%04d.png", output, review_fps, len(frame_numbers))
        media[key] = {
            "path": output.name,
            "sha256": sha256_file(output),
        }

    triptych = out / "abc-triptych.mp4"
    proc = run([
        "ffmpeg", "-y", "-v", "error",
        "-i", str(out / "arm-a.mp4"),
        "-i", str(out / "arm-b.mp4"),
        "-i", str(out / "arm-c.mp4"),
        "-filter_complex",
        "[0:v]scale=426:240,drawtext=text='A BEAUTY':x=12:y=12:fontsize=18:fontcolor=white[a];"
        "[1:v]scale=426:240,drawtext=text='B CONVENTIONAL':x=12:y=12:fontsize=18:fontcolor=white[b];"
        "[2:v]scale=426:240,drawtext=text='C PASS-AWARE':x=12:y=12:fontsize=18:fontcolor=white[c];"
        "[a][b][c]hstack=inputs=3[v]",
        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", str(triptych),
    ])
    require_ok(proc, "triptych encode")

    per_frame = []
    for frame in frame_numbers:
        a = arm_a / f"frame-{frame:04d}.png"
        b = arm_b / f"frame-{frame:04d}.png"
        c = arm_c / f"frame-{frame:04d}.png"
        per_frame.append({
            "frame": frame,
            "a_to_b": png_delta(a, b),
            "b_to_c": png_delta(b, c),
            "a_to_c": png_delta(a, c),
        })

    decisive_compare = None
    if args.execution_plan:
        execution = Path(args.execution_plan).expanduser().resolve()
        compare_dir = out / "b-vs-c-existing-compare"
        proc = run([
            sys.executable, "scripts/creativeqactl.py", "compare",
            str(out / "arm-b.mp4"), str(out / "arm-c.mp4"),
            str(execution), str(compare_dir),
        ])
        require_ok(proc, "existing creative B->C compare")
        decisive_compare = {
            "path": str((compare_dir / "iteration-compare.json").relative_to(out)),
            "sha256": sha256_file(compare_dir / "iteration-compare.json"),
        }

    result = {
        "schema_version": 1,
        "kind": "three-arm-finishing-benchmark",
        "bundle_sha256": canonical_json_sha256(bundle),
        "pass_aware_recipe_sha256": canonical_json_sha256(recipe),
        "beauty_baseline_recipe_sha256": canonical_json_sha256(base_recipe),
        "review_fps": review_fps,
        "arm_definition": {
            "A": "Blender beauty plus only the shared display transform",
            "B": "A plus deterministic conventional FFmpeg curves/contrast/saturation/vignette",
            "C": "full pass-aware finishing recipe",
        },
        "media": media,
        "triptych": {"path": triptych.name, "sha256": sha256_file(triptych)},
        "per_frame_pixel_delta": per_frame,
        "decisive_pair": "B_to_C",
        "existing_creative_compare": decisive_compare,
        "quality_verdict": None,
        "quality_verdict_rule": "No automatic winner. Review B vs C at normal speed using existing creative/experience QA.",
    }
    receipt = out / "benchmark-receipt.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "pass": True,
        "receipt": str(receipt),
        "triptych": str(triptych),
        "decisive_pair": "B_to_C",
        "existing_creative_compare": decisive_compare,
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(2)