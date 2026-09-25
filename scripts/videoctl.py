#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.media import (
    analyze_audio,
    artifact_receipt,
    build_contact_sheet,
    compare_video,
    decode_check,
    extract_frame,
    probe_media,
    validate_master,
)
from src.core.review_pack import build_review_pack


def _dump(data, output: str | None = None) -> None:
    text = json.dumps(data, indent=2, sort_keys=True)
    if output:
        out = Path(output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(out)
    else:
        print(text)


def _version(binary: str) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    proc = subprocess.run(
        [path, "-version"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return (proc.stdout or proc.stderr).splitlines()[0] if proc.returncode == 0 else None


def doctor(_args) -> int:
    data = {
        "python": sys.version.split()[0],
        "ffmpeg": _version("ffmpeg"),
        "ffprobe": _version("ffprobe"),
        "ffmpeg_path": shutil.which("ffmpeg"),
        "ffprobe_path": shutil.which("ffprobe"),
    }
    data["ready"] = bool(data["ffmpeg"] and data["ffprobe"])
    _dump(data)
    return 0 if data["ready"] else 1


def probe(args) -> int:
    _dump(probe_media(args.path), args.output)
    return 0


def decode(args) -> int:
    data = decode_check(args.path)
    _dump(data, args.output)
    return 0 if data["success"] else 1


def audio(args) -> int:
    data = analyze_audio(
        args.path,
        silence_threshold_db=args.silence_threshold_db,
        silence_min_duration=args.silence_min_duration,
    )
    _dump(data, args.output)
    return 0


def frame(args) -> int:
    out = extract_frame(
        args.path,
        args.output,
        time_seconds=args.at,
        max_width=args.max_width,
    )
    print(out)
    return 0


def contact_sheet(args) -> int:
    out = build_contact_sheet(
        args.path,
        args.output,
        count=args.count,
        columns=args.columns,
        cell_width=args.cell_width,
    )
    print(out)
    return 0


def compare(args) -> int:
    data = compare_video(
        args.reference,
        args.candidate,
        sample_fps=args.sample_fps,
        max_duration_seconds=args.max_duration_seconds,
    )
    _dump(data, args.output)
    return 0 if data.get("comparable") else 1


def receipt(args) -> int:
    data = artifact_receipt(
        args.path,
        include_audio=not args.no_audio,
        silence_threshold_db=args.silence_threshold_db,
        silence_min_duration=args.silence_min_duration,
    )
    _dump(data, args.output)
    return 0


def qa(args) -> int:
    data = validate_master(
        args.path,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration_seconds=args.duration,
        duration_tolerance=args.duration_tolerance,
        audio_required=not args.no_require_audio,
        silence_threshold_db=args.silence_threshold_db,
        silence_min_duration=args.silence_min_duration,
        max_silence_seconds=args.max_silence_seconds,
    )
    _dump(data, args.output)
    return 0 if data["pass"] else 1


def review_pack(args) -> int:
    result = build_review_pack(
        args.path,
        args.output_dir,
        scene_plan=args.scene_plan,
        count=args.count,
        columns=args.columns,
        cell_width=args.cell_width,
        frame_width=args.frame_width,
        boundary_offset=args.boundary_offset,
        silence_threshold_db=args.silence_threshold_db,
        silence_min_duration=args.silence_min_duration,
    )
    print(result["manifest_path"])
    return 0

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproducible media inspection and QA for Chatgpt-Video-Creations."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Check required local media binaries.")
    p.set_defaults(func=doctor)

    p = sub.add_parser("probe", help="Inspect container/video/audio metadata.")
    p.add_argument("path")
    p.add_argument("--output")
    p.set_defaults(func=probe)

    p = sub.add_parser("decode", help="Decode-check a media file.")
    p.add_argument("path")
    p.add_argument("--output")
    p.set_defaults(func=decode)

    p = sub.add_parser("audio", help="Measure loudness and silence intervals.")
    p.add_argument("path")
    p.add_argument("--silence-threshold-db", type=float, default=-55.0)
    p.add_argument("--silence-min-duration", type=float, default=0.5)
    p.add_argument("--output")
    p.set_defaults(func=audio)

    p = sub.add_parser("frame", help="Extract one review frame.")
    p.add_argument("path")
    p.add_argument("output")
    p.add_argument("--at", type=float, default=0.0)
    p.add_argument("--max-width", type=int, default=1280)
    p.set_defaults(func=frame)

    p = sub.add_parser("contact-sheet", help="Create a timestamped review contact sheet.")
    p.add_argument("path")
    p.add_argument("output")
    p.add_argument("--count", type=int, default=12)
    p.add_argument("--columns", type=int, default=4)
    p.add_argument("--cell-width", type=int, default=320)
    p.set_defaults(func=contact_sheet)

    p = sub.add_parser("compare", help="Compare candidate video pixels against a reference baseline.")
    p.add_argument("reference")
    p.add_argument("candidate")
    p.add_argument("--sample-fps", type=float, default=6.0)
    p.add_argument("--max-duration-seconds", type=float, default=60.0)
    p.add_argument("--output")
    p.set_defaults(func=compare)

    p = sub.add_parser("receipt", help="Create an exact artifact QA receipt.")
    p.add_argument("path")
    p.add_argument("--output")
    p.add_argument("--no-audio", action="store_true")
    p.add_argument("--silence-threshold-db", type=float, default=-55.0)
    p.add_argument("--silence-min-duration", type=float, default=0.5)
    p.set_defaults(func=receipt)

    p = sub.add_parser("qa", help="Apply technical delivery gates to a master.")
    p.add_argument("path")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fps", type=float)
    p.add_argument("--duration", type=float)
    p.add_argument("--duration-tolerance", type=float, default=0.15)
    p.add_argument("--no-require-audio", action="store_true")
    p.add_argument("--silence-threshold-db", type=float, default=-55.0)
    p.add_argument("--silence-min-duration", type=float, default=0.5)
    p.add_argument("--max-silence-seconds", type=float)
    p.add_argument("--output")
    p.set_defaults(func=qa)

    p = sub.add_parser(
        "review-pack",
        help="Build a receipt, contact sheet, and optional scene-boundary frame pack.",
    )
    p.add_argument("path")
    p.add_argument("output_dir")
    p.add_argument("--scene-plan")
    p.add_argument("--count", type=int, default=16)
    p.add_argument("--columns", type=int, default=4)
    p.add_argument("--cell-width", type=int, default=320)
    p.add_argument("--frame-width", type=int, default=960)
    p.add_argument("--boundary-offset", type=float, default=0.15)
    p.add_argument("--silence-threshold-db", type=float, default=-55.0)
    p.add_argument("--silence-min-duration", type=float, default=0.5)
    p.set_defaults(func=review_pack)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())