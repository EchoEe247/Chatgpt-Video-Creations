#!/usr/bin/env python3
"""Core audio commons and audio-master QA."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.media import analyze_audio,probe_media

def main():
    p=argparse.ArgumentParser(description=__doc__); sp=p.add_subparsers(dest="cmd",required=True)
    sp.add_parser("build-commons")
    st=sp.add_parser("commons-status")
    qa=sp.add_parser("qa"); qa.add_argument("media"); qa.add_argument("--target-lufs",type=float,default=-16); qa.add_argument("--lufs-tolerance",type=float,default=4); qa.add_argument("--true-peak-ceiling",type=float,default=-1.0); qa.add_argument("--max-silence",type=float,default=2.0); qa.add_argument("--intentional-silence",action="append",default=[],metavar="START:END")
    args=p.parse_args()
    if args.cmd=="build-commons":
        return subprocess.call([sys.executable,str(ROOT/"scripts"/"build_audio_commons.py")],cwd=ROOT)
    if args.cmd=="commons-status":
        m=ROOT/"assets"/"audio-commons.json"
        if not m.is_file(): print('{"pass":false,"reason":"manifest missing"}'); return 2
        data=json.loads(m.read_text()); missing=[]; changed=[]
        import hashlib
        for a in data["assets"]:
            fp=ROOT/a["file"]
            if not fp.is_file(): missing.append(a["id"]); continue
            h=hashlib.sha256(fp.read_bytes()).hexdigest()
            if h!=a["sha256"]: changed.append(a["id"])
        ok=not missing and not changed
        print(json.dumps({"pass":ok,"pack_id":data["pack_id"],"assets":len(data["assets"]),"missing":missing,"changed":changed},indent=2)); return 0 if ok else 2
    info=probe_media(args.media)
    if not info["audio_streams"]: print('{"pass":false,"reason":"no audio stream"}'); return 2
    a=analyze_audio(args.media)
    allowed=[]
    for raw in args.intentional_silence:
        try:
            left,right=(float(x) for x in raw.split(":",1))
        except (ValueError,TypeError):
            print(json.dumps({"pass":False,"reason":f"invalid intentional silence interval: {raw}"})); return 2
        if left < 0 or right <= left:
            print(json.dumps({"pass":False,"reason":f"invalid intentional silence interval: {raw}"})); return 2
        allowed.append((left,right))
    def uncovered(segment):
        remaining=[(float(segment["start_seconds"]),float(segment["end_seconds"]))]
        for left,right in allowed:
            nxt=[]
            for start,end in remaining:
                if right <= start or left >= end:
                    nxt.append((start,end)); continue
                if left > start: nxt.append((start,min(left,end)))
                if right < end: nxt.append((max(right,start),end))
            remaining=nxt
        return max((end-start for start,end in remaining),default=0.0)
    silence=max((uncovered(s) for s in a.get("silence_segments",[])),default=0.0)
    a["intentional_silence_intervals"]=[list(x) for x in allowed]
    a["longest_unintended_silence_seconds"]=round(silence,6)
    lufs=a["integrated_lufs"]; peak=a["true_peak_dbfs"]
    checks=[
        {"name":"loudness","pass":abs(lufs-args.target_lufs)<=args.lufs_tolerance,"actual":lufs,"expected":f"{args.target_lufs} ± {args.lufs_tolerance} LU"},
        {"name":"true_peak","pass":peak<=args.true_peak_ceiling,"actual":peak,"expected":f"<= {args.true_peak_ceiling} dBFS"},
        {"name":"silence","pass":silence<=args.max_silence,"actual":round(silence,6),"expected":f"<= {args.max_silence}s outside declared intentional intervals"},
    ]
    result={"pass":all(x["pass"] for x in checks),"checks":checks,"analysis":a}
    print(json.dumps(result,indent=2)); return 0 if result["pass"] else 2

if __name__=="__main__": raise SystemExit(main())