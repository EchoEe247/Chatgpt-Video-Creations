#!/usr/bin/env python3
"""Analyze the Phase 0 Blender finishing feasibility fixture.

This tool intentionally depends only on the standard library plus the locally
installed OpenImageIO CLI inside hermes-ubuntu. It reads actual multilayer EXR
metadata and vector pixels; enabled Blender flags alone are not accepted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

DISTRO = "hermes-ubuntu"
VECTOR_CHANNELS = [
    "ViewLayer.Vector.X",
    "ViewLayer.Vector.Y",
    "ViewLayer.Vector.Z",
    "ViewLayer.Vector.W",
]
REQUIRED_PREFIXES = [
    "ViewLayer.Combined.",
    "ViewLayer.Depth.",
    "ViewLayer.Normal.",
    "ViewLayer.Vector.",
    "ViewLayer.Emit.",
]


def run_guest(*argv: str) -> str:
    proc = subprocess.run(
        ["proot-distro", "login", DISTRO, "--", *argv],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or "guest command failed").strip())
    return proc.stdout


def parse_channels(info: str) -> list[str]:
    match = re.search(r"^\s*channel list:\s*(.+)$", info, re.MULTILINE)
    if not match:
        return []
    channels = []
    for item in match.group(1).split(", "):
        name = item.rsplit(" (", 1)[0].strip()
        if name:
            channels.append(name)
    return channels


def parse_stat_line(stats: str, label: str) -> list[float]:
    match = re.search(rf"^\s*Stats {re.escape(label)}:\s*(.+?)\s*\(float\)\s*$", stats, re.MULTILINE)
    if not match:
        return []
    return [float(x) for x in match.group(1).split()]


def vector_nonzero(stats: str, epsilon: float = 1e-6) -> bool:
    values = parse_stat_line(stats, "Min") + parse_stat_line(stats, "Max")
    return bool(values) and any(abs(v) > epsilon for v in values)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("output_dir")
    p.add_argument("--frame", type=int, default=2)
    p.add_argument("--report", default="")
    args = p.parse_args()

    out = Path(args.output_dir).resolve()
    receipt_path = out / "render-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    frame_path = out / f"frame-{args.frame:04d}.exr"
    if not frame_path.is_file():
        raise SystemExit(f"missing fixture frame: {frame_path}")

    info = run_guest("oiiotool", "--info", "-v", str(frame_path))
    channels = parse_channels(info)
    missing_prefixes = [x for x in REQUIRED_PREFIXES if not any(c.startswith(x) for c in channels)]

    tmp = f"/tmp/chatgpt-phase0-vector-{args.frame}.exr"
    try:
        run_guest("oiiotool", str(frame_path), "--ch", ",".join(VECTOR_CHANNELS), "-o", tmp)
        stats = run_guest("oiiotool", "--stats", tmp)
    finally:
        subprocess.run(["proot-distro", "login", DISTRO, "--", "rm", "-f", tmp], capture_output=True)

    rows = receipt.get("frames", [])
    measured = [r for r in rows if isinstance(r.get("render_seconds"), (int, float))]
    sizes = [int(r.get("bytes", 0)) for r in rows]
    peak = max((int(r.get("ru_maxrss_after_kib", 0)) for r in rows), default=0)
    avg_render = sum(float(r["render_seconds"]) for r in measured) / len(measured) if measured else None
    avg_bytes = sum(sizes) / len(sizes) if sizes else 0
    resume_verified = bool(receipt.get("resume_run")) and bool(rows) and all(r.get("skipped_existing") for r in rows)

    min_values = parse_stat_line(stats, "Min")
    max_values = parse_stat_line(stats, "Max")
    checks = {
        "resolution_1280x720": receipt.get("resolution") == [1280, 720],
        "animated_three_frame_fixture": len(rows) >= 3,
        "exr_channel_inventory_readable": len(channels) > 0,
        "required_channel_groups_present": not missing_prefixes,
        "vector_channels_present": all(c in channels for c in VECTOR_CHANNELS),
        "vector_pixels_nonzero": vector_nonzero(stats),
        "all_outputs_nonempty": bool(sizes) and all(x > 0 for x in sizes),
        "resume_verified": resume_verified,
    }
    report = {
        "schema_version": 1,
        "phase": "finishing-phase0",
        "pass": all(checks.values()),
        "checks": checks,
        "fixture": {
            "engine": receipt.get("engine"),
            "blender_version": receipt.get("blender_version"),
            "resolution": receipt.get("resolution"),
            "fps": receipt.get("fps"),
            "frames": len(rows),
        },
        "readback": {
            "tool": "OpenImageIO oiiotool in hermes-ubuntu",
            "channel_count": len(channels),
            "channels": channels,
            "missing_required_prefixes": missing_prefixes,
            "vector_channels": VECTOR_CHANNELS,
            "vector_min": min_values,
            "vector_max": max_values,
            "vector_nonzero": vector_nonzero(stats),
        },
        "budget": {
            "average_render_seconds_per_frame": None if avg_render is None else round(avg_render, 4),
            "average_bytes_per_frame": round(avg_bytes, 1),
            "average_mib_per_frame": round(avg_bytes / (1024 * 1024), 3),
            "three_frame_total_bytes": sum(sizes),
            "peak_ru_maxrss_kib": peak,
            "peak_ru_maxrss_mib": round(peak / 1024, 3),
        },
        "restartability": {
            "resume_run": bool(receipt.get("resume_run")),
            "all_frames_skipped_existing": resume_verified,
        },
    }
    report_path = Path(args.report).resolve() if args.report else out / "phase0-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
