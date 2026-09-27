#!/usr/bin/env python3
from pathlib import Path
import json,subprocess

P=Path(__file__).resolve().parent
R=P/"renders";OUT=R/"finished";OUT.mkdir(parents=True,exist_ok=True)
for stale in OUT.glob("shot-*.mp4"):
    stale.unlink()
plan=json.loads((P/"source/execution-plan.json").read_text())
cfg=json.loads((P/"source/transition-finish.json").read_text())
shots={s["id"]:s for s in plan["shots"]}
incoming={};outgoing={}
for tr in cfg["transitions"]:
    outgoing[tr["from"]]=tr
    incoming[tr["to"]]=tr

def probe(path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],capture_output=True,text=True)
    return float(p.stdout.strip()) if p.returncode==0 and p.stdout.strip() else None

def run(cmd):
    subprocess.run(cmd,check=True)

touched=sorted(set(incoming)|set(outgoing))
for sid in touched:
    src=R/f"{sid}.mp4";dst=OUT/f"{sid}.mp4"
    dur=float(shots[sid]["duration_seconds"])
    filters=["scale=1280:720:flags=lanczos","format=yuv420p"]
    if sid in incoming:
        tr=incoming[sid];d=float(tr["duration_seconds"])
        filters.append(f"fade=t=in:st=0:d={d}:color={tr['color']}")
    if sid in outgoing:
        tr=outgoing[sid];d=float(tr["duration_seconds"]);st=max(0,dur-d)
        filters.append(f"fade=t=out:st={st}:d={d}:color={tr['color']}")
    run(["ffmpeg","-y","-v","error","-i",str(src),"-an","-vf",",".join(filters),
         "-c:v","libx264","-preset","veryfast","-crf","18","-r","24","-pix_fmt","yuv420p",str(dst)])
    actual=probe(dst)
    if actual is None or abs(actual-dur)>.08:
        raise RuntimeError(f"{sid}: finished duration {actual} != {dur}")
    print("FINISHED",sid,"in" if sid in incoming else "-","out" if sid in outgoing else "-",flush=True)
print("TRANSITION_FINISH_READY",len(touched),flush=True)
