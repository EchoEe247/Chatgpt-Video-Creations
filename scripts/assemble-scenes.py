#!/usr/bin/env python3
"""Assemble compatible scene MP4s in lexical order with verification."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.media import decode_check, probe_media


def _video_signature(info: dict) -> tuple:
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


def _audio_signature(info: dict) -> tuple | None:
    audio = next((x for x in info["streams"] if x.get("codec_type") == "audio"), None)
    if audio is None:
        return None
    return (
        audio.get("codec_name"),
        audio.get("sample_rate"),
        audio.get("channels"),
        audio.get("channel_layout"),
    )


def _validate_scene_compatibility(scenes: list[pathlib.Path]) -> None:
    first_info = probe_media(scenes[0])
    expected_video = _video_signature(first_info)
    expected_audio = _audio_signature(first_info)

    for scene in scenes:
        info = probe_media(scene)
        actual_video = _video_signature(info)
        actual_audio = _audio_signature(info)
        if actual_video != expected_video:
            raise ValueError(
                f"incompatible video stream in {scene.name}: "
                f"{actual_video!r} != {expected_video!r}"
            )
        if actual_audio != expected_audio:
            raise ValueError(
                f"incompatible audio stream in {scene.name}: "
                f"{actual_audio!r} != {expected_audio!r}"
            )


def main(scene_dir: str, output: str) -> int:
    scenes = sorted(pathlib.Path(scene_dir).glob("*.mp4"))
    if not scenes:
        print("FAIL no MP4 scenes found")
        return 1

    try:
        _validate_scene_compatibility(scenes)
    except (OSError, ValueError, RuntimeError) as exc:
        print("FAIL scene compatibility:", exc)
        return 1

    output_path = pathlib.Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        for scene in scenes:
            escaped = str(scene.resolve()).replace("'", "'\\''")
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

    print(f"PASS assembled {len(scenes)} compatible scenes -> {output_path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: assemble-scenes.py <scene-dir> <output.mp4>")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
