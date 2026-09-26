from __future__ import annotations
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: render_missing_frames.py BLEND FRAME_DIR")

blend=Path(sys.argv[1]).resolve()
frame_dir=Path(sys.argv[2]).resolve()
frame_dir.mkdir(parents=True, exist_ok=True)
fatal=("terminated with signal","Error: script failed","Fatal Python error")
missing=[f for f in range(1,84,2) if not (frame_dir/f"frame_{f:04d}.png").is_file()]
print("missing",missing,flush=True)

for frame in missing:
    out=frame_dir/f"frame_{frame:04d}.png"
    expr=(
        "import bpy;"
        "s=bpy.context.scene;"
        "s.render.engine='BLENDER_WORKBENCH';"
        "s.render.resolution_x=512;"
        "s.render.resolution_y=288;"
        "s.render.resolution_percentage=100;"
        "s.render.image_settings.file_format='PNG';"
        f"s.frame_set({frame});"
        f"s.render.filepath={str(out)!r};"
        "bpy.ops.render.render(write_still=True)"
    )
    ok=False
    for attempt in range(1,4):
        if out.exists():
            out.unlink()
        cmd=[
            "proot-distro","login","hermes-ubuntu","--",
            "blender","--background",str(blend),
            "--python-exit-code","1","--python-expr",expr,
        ]
        proc=subprocess.run(cmd,capture_output=True,text=True)
        bad=proc.returncode!=0 or any(x in (proc.stderr or "") for x in fatal)
        ok=(not bad) and out.is_file() and out.stat().st_size>0
        print(f"frame {frame} attempt {attempt} rc={proc.returncode} ok={ok}",flush=True)
        if ok:
            break
        if proc.stderr:
            print(proc.stderr[-1200:],file=sys.stderr,flush=True)
    if not ok:
        raise SystemExit(f"failed frame {frame} after 3 attempts")
print("REMAINING_FRAMES_COMPLETE",flush=True)
