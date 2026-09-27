#!/usr/bin/env python3
"""Generic shotctl adapter that samples frames from a declared source video."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
EXT={".mp4",".mov",".mkv",".webm",".avi",".m4v"}
def main():
    if len(sys.argv)!=2: raise SystemExit("usage: ffmpeg_shot_adapter.py REQUEST.json")
    req=json.loads(Path(sys.argv[1]).read_text())
    src=next((Path(p) for p in req["source_paths"] if Path(p).suffix.lower() in EXT),None)
    if src is None: raise SystemExit("no media source declared")
    out=Path(req["output_dir"]); out.mkdir(parents=True,exist_ok=True)
    shot=req["shot"]; offset=float(shot.get("source_offset_seconds",0))
    for frame in req["frames"]:
        t=offset+int(frame)/float(shot["fps"])
        target=out/f"{int(frame):06d}.png"
        cmd=["ffmpeg","-y","-v","error","-ss",f"{t:.9f}","-i",str(src),"-frames:v","1","-vf",f"scale={shot['width']}:{shot['height']}:flags=lanczos",str(target)]
        if subprocess.call(cmd)!=0 or not target.is_file(): raise SystemExit(f"ffmpeg failed frame {frame}")
        print(f"SHOT_FRAME {frame}",flush=True)
if __name__=="__main__": main()
