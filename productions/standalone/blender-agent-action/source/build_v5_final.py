#!/usr/bin/env python3
"""Assemble and verify the V5 asset-backed action comparison."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROD = ROOT / "productions/standalone/blender-agent-action"
FRAMES = PROD / "frames-v5"
AUDIO = PROD / "audio/agent-action-v4.wav"
FINAL = PROD / "final/agent-action-v5.mp4"
RECEIPT = PROD / "final/agent-action-v5-build.json"

frames = sorted(FRAMES.glob("frame_*.png"))
expected = [FRAMES / f"frame_{i:04d}.png" for i in range(1, 97)]
missing = [str(p) for p in expected if not p.exists()]
if missing:
    raise SystemExit(f"missing {len(missing)} V5 frames; first={missing[:5]}")
if not AUDIO.exists():
    raise SystemExit(f"missing audio: {AUDIO}")

FINAL.parent.mkdir(parents=True, exist_ok=True)
cmd = [
    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
    "-framerate", "24", "-start_number", "1",
    "-i", str(FRAMES / "frame_%04d.png"),
    "-i", str(AUDIO),
    "-t", "4.0",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k",
    "-movflags", "+faststart",
    str(FINAL),
]
subprocess.run(cmd, check=True)
subprocess.run(
    ["ffmpeg", "-v", "error", "-i", str(FINAL), "-f", "null", "-"],
    check=True,
)
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries",
     "format=duration,size:stream=index,codec_name,codec_type,width,height,r_frame_rate",
     "-of", "json", str(FINAL)],
    check=True, capture_output=True, text=True,
)
sha = hashlib.sha256(FINAL.read_bytes()).hexdigest()
receipt = {
    "version": "v5",
    "visual_source": "CC0 Quaternius asset-backed Blender scene",
    "comparison_target": "same 4-second timing/audio as V4",
    "frames": 96,
    "fps": 24,
    "audio_source": "audio/agent-action-v4.wav",
    "sha256": sha,
    "ffprobe": json.loads(probe.stdout),
    "strict_decode": "pass",
}
RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
