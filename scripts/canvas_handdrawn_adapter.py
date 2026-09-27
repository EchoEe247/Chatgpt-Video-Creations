#!/usr/bin/env python3
"""Adapter for the vendored Canvas hand-drawn runtime.

Keeps browser discovery, dependency setup, preview and final render invocation
stable for agents on the Pixel/Termux environment.
"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "renderers" / "canvas_handdrawn"
RENDERER = ENGINE / "render.mjs"
TERMUX_CHROME = Path("/data/data/com.termux/files/usr/bin/chromium-browser")
TERMUX_HEADLESS = Path("/data/data/com.termux/files/usr/bin/headless_shell")

def chrome_path() -> str | None:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for p in (TERMUX_CHROME, TERMUX_HEADLESS):
        if p.exists():
            return str(p)
    for name in ("google-chrome","google-chrome-stable","chromium","chromium-browser"):
        p=shutil.which(name)
        if p:
            return p
    return None

def run(argv, cwd=None, env=None):
    return subprocess.run(argv, cwd=cwd or ROOT, env=env, text=True)

def setup(_):
    return run(["npm","ci","--no-audit","--no-fund"],cwd=ENGINE).returncode

def doctor(_):
    missing=[]
    for name in ("node","npm","ffmpeg"):
        p=shutil.which(name)
        print(f"{name}={p or 'MISSING'}")
        if not p: missing.append(name)
    chrome=chrome_path()
    print(f"chrome={chrome or 'MISSING'}")
    if not chrome: missing.append("chrome")
    modules=ENGINE/"node_modules"/"puppeteer-core"
    print(f"puppeteer_core={'ready' if modules.exists() else 'missing (run setup)'}")
    if not modules.exists(): missing.append("puppeteer-core")
    return 1 if missing else 0

def render_cmd(args, preview=False):
    film=(ROOT/args.film).resolve() if not Path(args.film).is_absolute() else Path(args.film)
    if not film.exists():
        print(f"film not found: {film}",file=sys.stderr); return 2
    chrome=chrome_path()
    if not chrome:
        print("No Chromium/Chrome found. Run doctor.",file=sys.stderr); return 2
    if not (ENGINE/"node_modules"/"puppeteer-core").exists():
        print("Renderer dependencies missing. Run setup.",file=sys.stderr); return 2
    out=(ROOT/args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    cmd=["node",str(RENDERER),str(film),"--out",str(out)]
    if args.width: cmd += ["--width",str(args.width)]
    if args.ar: cmd += ["--ar",args.ar]
    if args.look: cmd += ["--look",args.look]
    if preview:
        if args.strip: cmd += ["--strip",args.strip]
        elif args.only: cmd += ["--only",args.only]
        else: cmd += ["--grid",str(args.grid or 18)]
    env=os.environ.copy(); env["CHROME"]=chrome
    print(" ".join(cmd))
    return run(cmd,cwd=ENGINE,env=env).returncode

def parser():
    p=argparse.ArgumentParser(description="Canvas hand-drawn renderer adapter")
    sp=p.add_subparsers(dest="cmd",required=True)
    sp.add_parser("setup")
    sp.add_parser("doctor")
    def common(name):
        x=sp.add_parser(name)
        x.add_argument("film")
        x.add_argument("--out",default=".runtime/canvas-handdrawn")
        x.add_argument("--width",type=int,default=1280)
        x.add_argument("--ar")
        x.add_argument("--look")
        return x
    x=common("preview"); x.add_argument("--grid",type=int,default=18); x.add_argument("--strip"); x.add_argument("--only")
    common("render")
    return p

def main():
    args=parser().parse_args()
    if args.cmd=="setup": return setup(args)
    if args.cmd=="doctor": return doctor(args)
    return render_cmd(args,preview=args.cmd=="preview")

if __name__=="__main__":
    raise SystemExit(main())