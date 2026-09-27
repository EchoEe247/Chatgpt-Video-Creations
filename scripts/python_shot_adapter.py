#!/usr/bin/env python3
"""Generic shotctl adapter for production-owned Python frame renderers.

The first declared .py source that is not this adapter must expose:
    render_frame(shot, frame_index, output_path, request)
"""
from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path

def main():
    req_path=Path(sys.argv[1]).resolve()
    req=json.loads(req_path.read_text())
    candidates=[Path(p) for p in req["source_paths"] if p.endswith(".py") and Path(p).resolve()!=Path(__file__).resolve()]
    if not candidates: raise SystemExit("no production Python renderer declared in source_paths")
    source=candidates[0].resolve()
    spec=importlib.util.spec_from_file_location("production_frame_renderer",source)
    if spec is None or spec.loader is None: raise SystemExit(f"cannot load renderer: {source}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    fn=getattr(mod,"render_frame",None)
    if not callable(fn): raise SystemExit(f"{source} must define render_frame(shot, frame_index, output_path, request)")
    out=Path(req["output_dir"]); out.mkdir(parents=True,exist_ok=True)
    for frame in req["frames"]:
        target=out/f"{frame:06d}.png"
        fn(req["shot"],int(frame),target,req)
        if not target.is_file(): raise SystemExit(f"renderer omitted frame {frame}")
        print(f"SHOT_FRAME {frame}",flush=True)
if __name__=="__main__": main()
