#!/usr/bin/env python3
"""Fast PNG-only benchmark preview worker using the same finishing math as production."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from scripts.finishing_worker import (
    apply_operation,
    channels,
    cryptomatte_mask,
    read_frame,
    write_png,
)


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle",required=True)
    p.add_argument("--recipe",required=True)
    p.add_argument("--bundle-root",required=True)
    p.add_argument("--output-dir",required=True)
    args=p.parse_args()

    bundle=json.loads(Path(args.bundle).read_text())
    recipe=json.loads(Path(args.recipe).read_text())
    root=Path(args.bundle_root).resolve()
    out=Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    protection_by_id={x["id"]:x for x in bundle.get("protections",[])}

    rows=[]
    for row in bundle["frames"]:
        frame=int(row["frame"])
        source=(root/row["path"]).resolve()
        target=out/f"frame-{frame:04d}.png"
        t0=time.monotonic()
        src=read_frame(source)
        beauty=channels(src,bundle["pass_map"]["beauty"])
        if beauty.shape[-1]==3:
            rgba=np.concatenate((beauty,np.ones((*beauty.shape[:2],1),dtype=np.float32)),axis=-1)
        else:
            rgba=beauty[...,:4].copy()

        masks={}
        for op in recipe["operations"]:
            for mask_id in op.get("masks",[]):
                if mask_id in masks: continue
                protection=protection_by_id[mask_id]
                if protection["source_pass"]!="cryptomatte_object":
                    raise ValueError(f"unsupported benchmark mask source: {protection['source_pass']}")
                masks[mask_id]=cryptomatte_mask(src,bundle["pass_map"]["cryptomatte_object"],protection["selector"])

        stage="scene_linear"
        for op in recipe["operations"]:
            rgba=apply_operation(rgba,src,bundle,op,masks)
            stage=op["color_stage"]
        if stage=="scene_linear":
            x=np.maximum(rgba[...,:3],0.0); x=x/(1.0+x)
            rgba[...,:3]=np.where(x<=0.0031308,x*12.92,1.055*np.power(x,1.0/2.4)-0.055)
        write_png(target,rgba)
        rows.append({
            "frame":frame,
            "path":target.name,
            "sha256":sha256_file(target),
            "process_seconds":round(time.monotonic()-t0,4),
        })
        print(f"BENCH_PREVIEW frame={frame} seconds={rows[-1]['process_seconds']}",flush=True)

    receipt={"schema_version":1,"kind":"finishing-benchmark-preview","frames":rows}
    (out/"benchmark-preview-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
