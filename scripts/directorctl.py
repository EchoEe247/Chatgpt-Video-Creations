#!/usr/bin/env python3
"""Validate director briefs and compile deterministic production execution plans."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.director_execution import compile_plan, validate_director_brief, validate_execution_plan, validate_source_bindings

def load(path):
    return json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sp=p.add_subparsers(dest="cmd",required=True)
    v=sp.add_parser("validate-brief"); v.add_argument("brief")
    c=sp.add_parser("compile"); c.add_argument("brief"); c.add_argument("output"); c.add_argument("--catalog",default=str(ROOT/"assets/catalog.json")); c.add_argument("--width",type=int,default=1280); c.add_argument("--height",type=int,default=720); c.add_argument("--fps",type=int,default=24); c.add_argument("--max-default-shot",type=float,default=8)
    x=sp.add_parser("validate-plan"); x.add_argument("plan")
    s=sp.add_parser("status"); s.add_argument("plan")
    args=p.parse_args()
    if args.cmd=="validate-brief":
        errors=validate_director_brief(load(args.brief))
    elif args.cmd=="validate-plan":
        data=load(args.plan); errors=validate_execution_plan(data)+validate_source_bindings(data)
    elif args.cmd=="compile":
        try:
            plan=compile_plan(Path(args.brief).resolve(),Path(args.catalog).resolve(),width=args.width,height=args.height,fps=args.fps,max_default_shot=args.max_default_shot)
        except (ValueError,OSError,json.JSONDecodeError) as e:
            print(f"FAIL {e}",file=sys.stderr); return 2
        out=Path(args.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"pass":True,"output":str(out),"summary":plan["summary"],"warnings":plan["warnings"]},indent=2))
        return 0
    else:
        plan=load(args.plan)
        errors=validate_execution_plan(plan)
        if errors:
            print(json.dumps({"pass":False,"errors":errors},indent=2)); return 2
        pending=sum(1 for s in plan["shots"] if s["state"]=="PLANNED")
        blocked=[s["id"] for s in plan["shots"] if not s["renderer"]["adapter_ready"] or any(not a["resolved"] for a in s["assets"])]
        blocked_requirements=[r["id"] for r in plan.get("asset_strategy",{}).get("requirements",[]) if not r.get("resolved",False)]
        print(json.dumps({"pass":True,"execution_ready":plan["summary"].get("execution_ready",not blocked and not blocked_requirements),"title":plan["title"],"runtime_seconds":plan["runtime_seconds"],"shots":len(plan["shots"]),"planned":pending,"blocked_shots":blocked,"blocked_asset_requirements":blocked_requirements,"renderer_lanes":plan["summary"]["renderer_lanes"],"warnings":plan["warnings"]},indent=2))
        return 0
    if errors:
        print("FAIL\n- "+"\n- ".join(errors),file=sys.stderr); return 2
    print("PASS"); return 0

if __name__=="__main__":
    raise SystemExit(main())