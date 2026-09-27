#!/usr/bin/env python3
"""Inspect standardized renderer adapters available to shotctl."""
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CHROME=Path("/data/data/com.termux/files/usr/bin/chromium-browser")
LANES={
  "python":{
    "entrypoint":"python {repo}/scripts/python_shot_adapter.py {request}",
    "purpose":"Production-owned deterministic Python/Pillow/NumPy frame renderer",
    "fallback_lanes":[]
  },
  "canvas_handdrawn":{
    "entrypoint":"python {repo}/scripts/browser_shot_adapter.py {request}",
    "purpose":"Canvas2D/illustrative browser frame renderer",
    "fallback_lanes":["python"]
  },
  "threejs":{
    "entrypoint":"python {repo}/scripts/browser_shot_adapter.py {request}",
    "purpose":"Three.js/WebGL browser frame renderer",
    "fallback_lanes":["blender","canvas_handdrawn"]
  },
  "blender":{
    "entrypoint":"python {repo}/scripts/blender_termux_adapter.py {request}",
    "purpose":"Blender scene sampling through hermes-ubuntu",
    "fallback_lanes":["python"]
  },
  "ffmpeg":{
    "entrypoint":"python {repo}/scripts/ffmpeg_shot_adapter.py {request}",
    "purpose":"Existing-media sampling/compositing lane",
    "fallback_lanes":["python"]
  }
}

def webgl_probe() -> tuple[bool,str]:
    if not CHROME.exists():
        return False,"Chromium missing"
    html=ROOT/"examples"/"renderer-adapters"/"webgl_demo.html"
    if not html.is_file():
        return False,"WebGL smoke source missing"
    base=ROOT/".runtime"/"renderer-doctor"
    out=base/"webgl"; out.mkdir(parents=True,exist_ok=True)
    req={
      "schema_version":1,
      "shot":{
        "id":"webgl-doctor","intent":"runtime probe","criteria":["frame_exists"],
        "motion_criteria":[],"width":64,"height":64,"fps":24,"duration_seconds":1,
        "source_offset_seconds":0,"settings":{}
      },
      "frames":[0],"source_paths":[str(html)],"output_dir":str(out),
      "spec_dir":str(base),"fingerprint":"webgl-doctor","selected_visual_mode":"default"
    }
    request=base/"webgl-request.json"
    request.write_text(json.dumps(req),encoding="utf-8")
    try:
        p=subprocess.run(
            [sys.executable,str(ROOT/"scripts"/"browser_shot_adapter.py"),str(request)],
            cwd=ROOT,capture_output=True,text=True,timeout=20
        )
    except subprocess.TimeoutExpired:
        return False,"WebGL probe timed out"
    if p.returncode==0 and (out/"000000.png").is_file():
        return True,"headless WebGL frame rendered"
    detail=(p.stderr or p.stdout or "WebGL frame unavailable").strip().splitlines()
    useful=next((line.strip() for line in detail if "WebGL unavailable" in line),None)
    return False,(useful or (detail[-1] if detail else "WebGL frame unavailable"))

def blender_ready() -> tuple[bool,str]:
    if not shutil.which("proot-distro"):
        return False,"proot-distro missing"
    try:
        p=subprocess.run(
            ["proot-distro","login","hermes-ubuntu","--","blender","--version"],
            cwd=ROOT,capture_output=True,text=True,timeout=20
        )
    except subprocess.TimeoutExpired:
        return False,"Blender version probe timed out"
    first=(p.stdout or p.stderr or "").strip().splitlines()
    return p.returncode==0,(first[0] if first else "Blender unavailable")

def doctor() -> int:
    python_ok=bool(shutil.which("python"))
    ffmpeg_ok=bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    browser_ok=CHROME.exists() and (ROOT/"src/renderers/canvas_handdrawn/node_modules/puppeteer-core").exists()
    blender_ok,blender_detail=blender_ready()
    webgl_ok,webgl_detail=webgl_probe() if browser_ok else (False,"browser runtime unavailable")
    ready={
      "python":python_ok,
      "canvas_handdrawn":browser_ok,
      "threejs":webgl_ok,
      "blender":blender_ok,
      "ffmpeg":ffmpeg_ok
    }
    required=("python","canvas_handdrawn","blender","ffmpeg")
    result={
      "pass":all(ready[k] for k in required),
      "ready":ready,
      "degraded_lanes":[k for k,v in ready.items() if not v],
      "details":{"blender":blender_detail,"threejs":webgl_detail},
      "lanes":{k:{**v,"runtime_ready":ready[k]} for k,v in LANES.items()}
    }
    print(json.dumps(result,indent=2))
    return 0 if result["pass"] else 2

def main():
    cmd=sys.argv[1] if len(sys.argv)>1 else "doctor"
    if cmd=="list":
        print(json.dumps(LANES,indent=2)); return 0
    if cmd=="doctor":
        return doctor()
    raise SystemExit("usage: rendererctl.py [doctor|list]")

if __name__=="__main__":
    raise SystemExit(main())