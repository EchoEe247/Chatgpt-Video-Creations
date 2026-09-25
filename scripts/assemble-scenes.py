#!/usr/bin/env python3
"""Assemble an explicit ordered scene manifest with compatibility checks."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.media import decode_check, probe_media, sha256_file


def _video_signature(info: dict[str, Any]) -> tuple:
    video = next((x for x in info["streams"] if x.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("scene has no video stream")
    return (
        video.get("codec_name"),
        video.get("width"),
        video.get("height"),
        video.get("pixel_format"),
        round(float(video.get("frame_rate") or 0.0), 6),
    )


def _audio_signature(info: dict[str, Any]) -> tuple | None:
    audio = next((x for x in info["streams"] if x.get("codec_type") == "audio"), None)
    if audio is None:
        return None
    return (
        audio.get("codec_name"),
        audio.get("sample_rate"),
        audio.get("channels"),
        audio.get("channel_layout"),
    )


def _load_manifest(path: pathlib.Path) -> list[tuple[str, pathlib.Path, dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("assembly manifest scenes must be a non-empty array")

    resolved: list[tuple[str, pathlib.Path, dict[str, Any]]] = []
    ids: set[str] = set()
    paths: set[pathlib.Path] = set()
    for index, item in enumerate(scenes, 1):
        if not isinstance(item, dict):
            raise ValueError(f"scene {index} must be an object")
        scene_id = str(item.get("id") or "").strip()
        if not scene_id:
            raise ValueError(f"scene {index} is missing id")
        if scene_id in ids:
            raise ValueError(f"duplicate scene id: {scene_id}")
        ids.add(scene_id)

        raw = item.get("path")
        if not isinstance(raw, str) or not raw:
            raise ValueError(f"{scene_id} is missing path")
        scene_path = pathlib.Path(raw).expanduser()
        if not scene_path.is_absolute():
            scene_path = path.parent / scene_path
        scene_path = scene_path.resolve()
        if not scene_path.is_file():
            raise FileNotFoundError(f"{scene_id} file missing: {scene_path}")
        if scene_path in paths:
            raise ValueError(f"duplicate scene file: {scene_path}")
        paths.add(scene_path)
        resolved.append((scene_id, scene_path, item))
    return resolved


def _validate_scenes(
    scenes: list[tuple[str, pathlib.Path, dict[str, Any]]],
    output_path: pathlib.Path,
) -> None:
    input_paths = {scene_path for _, scene_path, _ in scenes}
    if output_path in input_paths:
        raise ValueError("output path must not be one of the scene inputs")

    expected_video = None
    expected_audio = None
    for scene_id, scene_path, spec in scenes:
        info = probe_media(scene_path)
        video = _video_signature(info)
        audio = _audio_signature(info)
        if expected_video is None:
            expected_video = video
            expected_audio = audio
        elif video != expected_video:
            raise ValueError(
                f"incompatible video stream in {scene_id}: {video!r} != {expected_video!r}"
            )
        elif audio != expected_audio:
            raise ValueError(
                f"incompatible audio stream in {scene_id}: {audio!r} != {expected_audio!r}"
            )

        expected_sha = spec.get("sha256")
        if expected_sha and sha256_file(scene_path) != expected_sha:
            raise ValueError(f"{scene_id} SHA-256 does not match manifest")

        expected_duration = spec.get("expected_duration_seconds")
        if expected_duration is not None:
            actual = float(info.get("duration_seconds") or 0.0)
            tolerance = float(spec.get("duration_tolerance_seconds", 0.15))
            if abs(actual - float(expected_duration)) > tolerance:
                raise ValueError(
                    f"{scene_id} duration {actual:.6f}s outside "
                    f"{expected_duration} ± {tolerance}s"
                )


def main(manifest_path: str, output: str) -> int:
    manifest = pathlib.Path(manifest_path).expanduser().resolve()
    output_path = pathlib.Path(output).expanduser().resolve()

    try:
        scenes = _load_manifest(manifest)
        _validate_scenes(scenes, output_path)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("FAIL scene manifest:", exc)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        for _, scene, _ in scenes:
            escaped = str(scene).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")
        list_path = handle.name

    try:
        proc = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path,
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        pathlib.Path(list_path).unlink(missing_ok=True)

    if proc.returncode != 0:
        print("FAIL ffmpeg assembly")
        print((proc.stderr or proc.stdout).strip())
        return proc.returncode or 1

    decoded = decode_check(output_path)
    if not decoded["success"]:
        print("FAIL assembled master decode check")
        print(decoded["errors"])
        return 1

    print(f"PASS assembled {len(scenes)} explicit scenes -> {output_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: assemble-scenes.py <assembly-manifest.json> <output.mp4>")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
