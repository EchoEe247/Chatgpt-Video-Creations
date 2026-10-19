#!/usr/bin/env python3
"""Render native Earshot bank effects using a compiled studio A/V timeline."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.core.native_earshot import compile_effects,write_wav


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline",required=True)
    parser.add_argument("--cues",required=True,help="JSON list of {event_id,sound_id,align,gain_db,seed?}")
    parser.add_argument("--out",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args(argv)
    try:
        timeline=json.loads(Path(args.timeline).read_text())
        cues=json.loads(Path(args.cues).read_text())
        mix,receipt=compile_effects(timeline,cues)
        wav=write_wav(args.out,mix)
        report=Path(args.report)
        report.parent.mkdir(parents=True,exist_ok=True)
        receipt["rendered_wav"]=str(wav.resolve())
        report.write_text(json.dumps(receipt,indent=2)+"\n")
        print(json.dumps({"status":"unmastered_effects_rendered",
                          "wav":str(wav),"receipt":str(report),"cues":len(receipt["cues"])}))
        return 0
    except (OSError,ValueError,RuntimeError,TypeError,KeyError) as error:
        print(json.dumps({"status":"failed","error":str(error)}),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
