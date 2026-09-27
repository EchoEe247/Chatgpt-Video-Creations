#!/usr/bin/env python3
"""Compile and validate the shared picture/audio event timeline."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.av_timeline import compile_timeline,validate_timeline,validate_bindings

def load(p): return json.loads(Path(p).expanduser().resolve().read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser(description=__doc__); sp=p.add_subparsers(dest="cmd",required=True)
    c=sp.add_parser("compile"); c.add_argument("execution_plan"); c.add_argument("output"); c.add_argument("--events"); c.add_argument("--sample-rate",type=int,default=48000)
    v=sp.add_parser("validate"); v.add_argument("timeline")
    s=sp.add_parser("status"); s.add_argument("timeline")
    e=sp.add_parser("event"); e.add_argument("timeline"); e.add_argument("event_id")
    a=p.parse_args()
    if a.cmd=="compile":
        try: out=compile_timeline(Path(a.execution_plan).resolve(),Path(a.events).resolve() if a.events else None,sample_rate=a.sample_rate)
        except (OSError,ValueError,json.JSONDecodeError,KeyError) as exc:
            print(f"FAIL {exc}",file=sys.stderr); return 2
        path=Path(a.output).resolve(); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps({"pass":True,"output":str(path),"summary":out["summary"]},indent=2)); return 0
    data=load(a.timeline)
    errors=validate_timeline(data)+validate_bindings(data)
    if errors:
        print(json.dumps({"pass":False,"errors":errors},indent=2)); return 2
    if a.cmd=="validate": print("PASS"); return 0
    if a.cmd=="status":
        print(json.dumps({"pass":True,"title":data["title"],"runtime_seconds":data["runtime_seconds"],"fps":data["fps"],"sample_rate":data["sample_rate"],"summary":data["summary"]},indent=2)); return 0
    hit=next((x for x in data["events"] if x["id"]==a.event_id),None)
    if not hit: print(f"FAIL unknown event {a.event_id}",file=sys.stderr); return 2
    print(json.dumps(hit,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
