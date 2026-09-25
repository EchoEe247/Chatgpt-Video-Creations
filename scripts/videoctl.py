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
    decode_check,
    extract_frame,
    probe_media,
    validate_master,
)


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
    video = Path(args.path).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    receipt_path = out_dir / "artifact-receipt.json"
    sheet_path = out_dir / "contact-sheet.png"
    receipt_data = artifact_receipt(
        video,
        silence_threshold_db=args.silence_threshold_db,
        silence_min_duration=args.silence_min_duration,
    )
    receipt_path.write_text(json.dumps(receipt_data, indent=2, sort_keys=True) + "\n")
    build_contact_sheet(
        video,
        sheet_path,
        count=args.count,
        columns=args.columns,
        cell_width=args.cell_width,
    )

    boundary_records = []
    if args.scene_plan:
        scene_plan_path = Path(args.scene_plan).expanduser().resolve()
        plan = json.loads(scene_plan_path.read_text(encoding="utf-8"))
        scenes = plan.get("scenes") or []
        boundary_dir = out_dir / "boundaries"
        boundary_dir.mkdir(exist_ok=True)
        for scene in scenes[1:]:
            start = float(scene["start_seconds"])
            number = int(scene.get("scene", len(boundary_records) + 2))
            before_at = max(0.0, start - args.boundary_offset)
            after_at = start + args.boundary_offset
            before = boundary_dir / f"scene_{number:02d}_before.png"
            after = boundary_dir / f"scene_{number:02d}_after.png"
            extract_frame(video, before, time_seconds=before_at, max_width=args.frame_width)
            extract_frame(video, after, time_seconds=after_at, max_width=args.frame_width)
            boundary_records.append(
                {
                    "scene": number,
                    "boundary_seconds": start,
                    "before_seconds": before_at,
                    "before": str(before.relative_to(out_dir)),
                    "after_seconds": after_at,
                    "after": str(after.relative_to(out_dir)),
                }
            )

    manifest = {
        "video": str(video),
        "receipt": receipt_path.name,
        "contact_sheet": sheet_path.name,
        "scene_plan": str(Path(args.scene_plan).expanduser().resolve()) if args.scene_plan else None,
        "boundaries": boundary_records,
    }
    manifest_path = out_dir / "review-pack.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(manifest_path)
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
