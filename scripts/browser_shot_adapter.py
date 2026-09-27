#!/usr/bin/env python3
"""shotctl browser adapter for deterministic Canvas/WebGL/Three.js HTML shots."""
from __future__ import annotations
import os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ENGINE=ROOT/"src"/"renderers"/"canvas_handdrawn"
NODE=ENGINE/"request-render.mjs"
def chrome():
    for p in (os.environ.get("CHROME"),"/data/data/com.termux/files/usr/bin/chromium-browser","/data/data/com.termux/files/usr/bin/headless_shell",shutil.which("chromium"),shutil.which("google-chrome")):
        if p and Path(p).exists(): return str(p)
    return None
def main():
    if len(sys.argv)!=2: raise SystemExit("usage: browser_shot_adapter.py REQUEST.json")
    ch=chrome()
    if not ch: raise SystemExit("Chromium/Chrome not found")
    if not (ENGINE/"node_modules"/"puppeteer-core").exists(): raise SystemExit("puppeteer-core missing; run canvas_handdrawn_adapter.py setup")
    env=os.environ.copy(); env["CHROME"]=ch
    raise SystemExit(subprocess.call(["node",str(NODE),str(Path(sys.argv[1]).resolve())],cwd=ENGINE,env=env))
if __name__=="__main__": main()
