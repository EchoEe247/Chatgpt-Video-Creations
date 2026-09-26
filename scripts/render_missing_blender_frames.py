from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def parse_args():
    ap = argparse.ArgumentParser(
        description="Render missing Blender frames in isolated processes with retries."
    )
    ap.add_argument("blend")
    ap.add_argument("frame_dir")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=83)
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--height", type=int, default=288)
    ap.add_argument("--attempts", type=int, default=3)
    args = ap.parse_args()
    if args.start < 1 or args.end < args.start:
        ap.error("require 1 <= start <= end")
    if args.step < 1:
        ap.error("--step must be >= 1")
    if args.width < 2 or args.height < 2:
        ap.error("resolution must be >= 2x2")
    if args.attempts < 1:
        ap.error("--attempts must be >= 1")
    return args


def main():
    args = parse_args()
    blend = Path(args.blend).resolve()
    frame_dir = Path(args.frame_dir).resolve()
    if not blend.is_file():
        raise SystemExit(f"missing blend: {blend}")
    frame_dir.mkdir(parents=True, exist_ok=True)

    fatal = ("terminated with signal", "Error: script failed", "Fatal Python error")
    requested = list(range(args.start, args.end + 1, args.step))
    missing = [f for f in requested if not (frame_dir / f"frame_{f:04d}.png").is_file()]
    print(
        f"requested={len(requested)} missing={len(missing)} "
        f"range={args.start}:{args.end}:{args.step}",
        flush=True,
    )

    for frame in missing:
        out = frame_dir / f"frame_{frame:04d}.png"
        expr = (
            "import bpy;"
            "s=bpy.context.scene;"
            "s.render.engine='BLENDER_WORKBENCH';"
            f"s.render.resolution_x={args.width};"
            f"s.render.resolution_y={args.height};"
            "s.render.resolution_percentage=100;"
            "s.render.image_settings.file_format='PNG';"
            f"s.frame_set({frame});"
            f"s.render.filepath={str(out)!r};"
            "bpy.ops.render.render(write_still=True)"
        )
        ok = False
        for attempt in range(1, args.attempts + 1):
            if out.exists():
                out.unlink()
            cmd = [
                "proot-distro", "login", "hermes-ubuntu", "--",
                "blender", "--background", str(blend),
                "--python-exit-code", "1", "--python-expr", expr,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            bad = proc.returncode != 0 or any(x in combined for x in fatal)
            ok = (not bad) and out.is_file() and out.stat().st_size > 0
            print(f"frame {frame} attempt {attempt} rc={proc.returncode} ok={ok}", flush=True)
            if ok:
                break
            if proc.stderr:
                print(proc.stderr[-1200:], flush=True)
        if not ok:
            raise SystemExit(f"failed frame {frame} after {args.attempts} attempts")

    print(
        f"MISSING_FRAMES_COMPLETE requested={len(requested)} rendered={len(missing)} "
        f"reused={len(requested)-len(missing)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
