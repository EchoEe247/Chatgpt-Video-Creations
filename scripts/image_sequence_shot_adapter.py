"""Local image-sequence adapter: reuse ordered rendered frames without rerendering.
Declare every PNG in sources in playback order, followed by this adapter.
The frame count must match fps * duration_seconds; no interpolation is performed.
"""
import json
import shutil
import sys
from pathlib import Path
from PIL import Image
r = json.loads(Path(sys.argv[1]).read_text())
shot = r["shot"]
frames = [Path(p) for p in r["source_paths"] if Path(p).suffix.lower() == ".png"]
if len(frames) != round(shot["fps"] * shot["duration_seconds"]):
    raise ValueError("one declared PNG per output frame is required")
for index in r["frames"]:
    with Image.open(frames[index]) as im:
        if im.size != (shot["width"], shot["height"]):
            raise ValueError("source dimensions differ from shot dimensions")
        im.verify()
    shutil.copyfile(frames[index], Path(r["output_dir"]) / f"{index:06d}.png")
