#!/usr/bin/env python3
"""Creative QA signal/evidence builder for final video review."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.creative_qa import build_creative_qa,validate_assistant_review,validate_report_evidence

def main():
    p=argparse.ArgumentParser(description=__doc__); sp=p.add_subparsers(dest="cmd",required=True)
    a=sp.add_parser("analyze"); a.add_argument("media"); a.add_argument("execution_plan"); a.add_argument("output_dir"); a.add_argument("--layout"); a.add_argument("--review-clip-limit",type=int,default=12)
    b=sp.add_parser("validate-bundle"); b.add_argument("report")
    v=sp.add_parser("validate-review"); v.add_argument("report"); v.add_argument("review")
    args=p.parse_args()
    if args.cmd=="analyze":
        try: result=build_creative_qa(args.media,args.execution_plan,args.output_dir,args.layout,review_clip_limit=args.review_clip_limit)
        except Exception as exc:
            print(f"FAIL {exc}",file=sys.stderr); return 2
        print(json.dumps({"pass":True,"report":str(Path(args.output_dir).resolve()/"creative-qa.json"),"summary":result["summary"],"warnings":result["warnings"]},indent=2))
        return 0
    if args.cmd=="validate-bundle":
        result=validate_report_evidence(args.report)
        print(json.dumps(result,indent=2)); return 0 if result["pass"] else 2
    result=validate_assistant_review(args.report,args.review)
    print(json.dumps(result,indent=2))
    if not result["valid"]: return 2
    return 0 if result["pass"] else 1

if __name__=="__main__": raise SystemExit(main())