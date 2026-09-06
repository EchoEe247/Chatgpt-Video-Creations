#!/usr/bin/env python3
"""Assemble compatible scene MP4s in lexical order with FFmpeg concat."""
import pathlib, shutil, subprocess, sys, tempfile

def main(scene_dir: str, output: str) -> int:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("FAIL ffmpeg not found")
        return 1
    scenes = sorted(pathlib.Path(scene_dir).glob("*.mp4"))
    if not scenes:
        print("FAIL no MP4 scenes found")
        return 1
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for scene in scenes:
            f.write("file '%s'\n" % str(scene.resolve()).replace("'", "'\\''"))
        list_path = f.name
    subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", output], check=True)
    print(f"PASS assembled {len(scenes)} scenes -> {output}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: assemble-scenes.py <scene-dir> <output.mp4>")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
