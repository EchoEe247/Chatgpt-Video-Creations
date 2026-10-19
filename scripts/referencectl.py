#!/usr/bin/env python3
"""Reference recreation evidence for the canonical Chatgpt-Video-Creations studio.

This supplements shotctl and productionctl instead of bypassing their review gates.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.reference_alignment import make_lock,verify_lock,compare,ReferenceAlignmentError


def output(path, data):
    serialized=json.dumps(data,indent=2,allow_nan=False)+"\n"
    if path:
        p=Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(serialized,encoding="utf-8")
        print(str(p))
    else:
        print(serialized,end="")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    lock=sub.add_parser("lock",help="Bind uploaded reference, verified creative crop and source/target timeline")
    lock.add_argument("--reference",required=True)
    lock.add_argument("--crop",required=True,help="W:H:X:Y pixels, even if entire frame")
    lock.add_argument("--crop-verified",action="store_true",help="Confirms direct source-frame crop inspection")
    lock.add_argument("--shots",required=True,help="JSON list of authored source/target shot intervals")
    lock.add_argument("--width",required=True,type=int)
    lock.add_argument("--height",required=True,type=int)
    lock.add_argument("--fps",required=True)
    lock.add_argument("--duration",required=True,type=float)
    lock.add_argument("--aspect-override-reason")
    lock.add_argument("--audio-override-reason")
    lock.add_argument("--out",required=True)
    verify=sub.add_parser("verify",help="Refuse stale/changed source and invalid timeline")
    verify.add_argument("--lock",required=True)
    check=sub.add_parser("compare",help="Check encoded recreation against source-aligned shot map")
    check.add_argument("--lock",required=True)
    check.add_argument("--candidate",required=True)
    check.add_argument("--board",help="Side-by-side shot frame comparison JPEG/PNG")
    check.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="lock":
            shots=json.loads(Path(args.shots).read_text())
            data=make_lock(args.reference,args.crop,shots,width=args.width,
                 height=args.height,fps=args.fps,duration_seconds=args.duration,
                 crop_verified=args.crop_verified,
                 aspect_override_reason=args.aspect_override_reason,
                 audio_override_reason=args.audio_override_reason)
            output(args.out,data)
        else:
            data=json.loads(Path(args.lock).read_text())
            if args.command=="verify":
                verify_lock(data)
                output(None,{"status":"source_lock_valid","reference_sha256":data["reference"]["sha256"],
                             "shots":len(data["shots"])})
            else:
                report=compare(data,args.candidate,board=args.board)
                output(args.out,report)
        return 0
    except (ReferenceAlignmentError,ValueError,KeyError,TypeError,OSError,TimeoutError) as exc:
        print(json.dumps({"status":"failed","error":str(exc)}),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
