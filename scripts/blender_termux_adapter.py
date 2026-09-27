#!/usr/bin/env python3
"""Termux wrapper that gives shotctl one stable Blender renderer command."""
from __future__ import annotations
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INNER=ROOT/"scripts"/"blender_shot_adapter.py"
def main():
    if len(sys.argv)!=2: raise SystemExit("usage: blender_termux_adapter.py REQUEST.json")
    if not shutil.which("proot-distro"): raise SystemExit("proot-distro missing")
    req=Path(sys.argv[1]).resolve()
    data=json.loads(req.read_text())
    if not any(str(p).endswith(".blend") for p in data.get("source_paths",[])): raise SystemExit("no .blend source declared")
    cmd=["proot-distro","login","hermes-ubuntu","--","blender","--background","--python-exit-code","1","--python",str(INNER),"--",str(req)]
    raise SystemExit(subprocess.call(cmd,cwd=ROOT))
if __name__=="__main__": main()
