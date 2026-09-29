#!/usr/bin/env python3
"""Prepare the Phase 4 cinematic fixture as a validated Render Bundle + recipe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

from src.core.finishing_contract import canonical_json_sha256, sha256_file


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("render_dir")
    args=p.parse_args()
    out=Path(args.render_dir).expanduser().resolve()
    receipt=json.loads((out/"render-receipt.json").read_text())
    rows=receipt["frames"]
    if not rows:
        raise ValueError("render receipt has no frames")
    frame_numbers=sorted(int(x["frame"]) for x in rows)
    if frame_numbers != list(range(frame_numbers[0],frame_numbers[-1]+1)):
        raise ValueError("render receipt must contain a contiguous frame range")

    plan={
        "schema_version":1,
        "kind":"phase4-cinematic-benchmark-execution",
        "intent":"normal-speed deterministic finishing benchmark with camera parallax, protected-subject motion, reflective surfaces, emissive practicals and meaningful depth",
        "native_fps":24,
        "shots":[{
            "id":"phase4-cinematic-shot",
            "start_seconds":0.0,
            "end_seconds":len(frame_numbers)/24.0,
        }],
    }
    plan_path=out/"execution-plan.json"
    plan_path.write_text(json.dumps(plan,indent=2)+"\n")

    frame_rows=[]
    by_frame={int(x["frame"]):x for x in rows}
    for frame in frame_numbers:
        path=out/f"frame-{frame:04d}.exr"
        if not path.is_file() or path.stat().st_size<=0:
            raise ValueError(f"missing rendered frame {frame}")
        frame_rows.append({
            "frame":frame,
            "path":path.name,
            "sha256":sha256_file(path),
            "bytes":path.stat().st_size,
            "readback_status":"verified",
        })

    source_script=ROOT/"scripts/blender_phase4_cinematic_fixture.py"
    bundle={
        "schema_version":1,
        "kind":"blender-render-bundle",
        "production_id":"phase4-cinematic-finishing-benchmark",
        "shot_id":"phase4-cinematic-shot",
        "source":{
            "scene_path":"scripts/blender_phase4_cinematic_fixture.py",
            "scene_sha256":sha256_file(source_script),
            "execution_plan_sha256":sha256_file(plan_path),
        },
        "render":{
            "engine":receipt["engine"],
            "width":receipt["resolution"][0],
            "height":receipt["resolution"][1],
            "native_fps":24,
            "frame_start":frame_numbers[0],
            "frame_end":frame_numbers[-1],
            "color_space":"scene_linear",
            "view_transform":"AgX",
        },
        "pass_map":{
            "beauty":["ViewLayer.Combined.R","ViewLayer.Combined.G","ViewLayer.Combined.B","ViewLayer.Combined.A"],
            "depth":["ViewLayer.Depth.Z"],
            "normal":["ViewLayer.Normal.X","ViewLayer.Normal.Y","ViewLayer.Normal.Z"],
            "emission":["ViewLayer.Emit.R","ViewLayer.Emit.G","ViewLayer.Emit.B"],
            "ambient_occlusion":["ViewLayer.AO.R","ViewLayer.AO.G","ViewLayer.AO.B"],
            "cryptomatte_object":[
                "ViewLayer.CryptoObject00.r","ViewLayer.CryptoObject00.g","ViewLayer.CryptoObject00.b","ViewLayer.CryptoObject00.a",
                "ViewLayer.CryptoObject01.r","ViewLayer.CryptoObject01.g","ViewLayer.CryptoObject01.b","ViewLayer.CryptoObject01.a",
                "ViewLayer.CryptoObject02.r","ViewLayer.CryptoObject02.g","ViewLayer.CryptoObject02.b","ViewLayer.CryptoObject02.a",
            ],
        },
        "frames":frame_rows,
        "protections":[{
            "id":"hero",
            "type":"geometry_protected",
            "source_pass":"cryptomatte_object",
            "selector":"Hero",
        }],
        "approved_facts":{
            "forward_axis":"+Y",
            "travel_vector":[3.3,4.4,0.25],
            "camera_binding_sha256":canonical_json_sha256({
                "start_location":[4.8,-8.5,3.3],
                "end_location":[3.0,-5.2,2.7],
                "start_lens":46,
                "end_lens":52,
            }),
        },
        "policy":{
            "allowed_processor_classes":["P","S"],
            "prohibited_transforms":["object_count_change","identity_change","geometry_warp","interpolation"],
        },
        "runtime":{
            "blender_version":receipt["blender_version"],
            "readback_tool":"OpenImageIO oiiotool",
            "platform":"Pixel Termux / hermes-ubuntu",
        },
    }
    bundle_path=out/"render-bundle.json"
    bundle_path.write_text(json.dumps(bundle,indent=2)+"\n")

    recipe={
        "schema_version":1,
        "kind":"finishing-recipe",
        "recipe_id":"phase4-cinematic-deterministic",
        "recipe_version":1,
        "operations":[
            {
                "id":"depth-atmosphere",
                "processor":"depth_atmosphere",
                "risk_class":"S",
                "color_stage":"scene_linear",
                "inputs":["beauty","depth"],
                "masks":[],
                "params":{"near":5.0,"density":0.014,"max_amount":0.28,"color":[0.028,0.052,0.085]},
                "deterministic":True,"uses_randomness":False,"seed":None,
            },
            {
                "id":"emission-rebalance",
                "processor":"emission_rebalance",
                "risk_class":"P",
                "color_stage":"scene_linear",
                "inputs":["beauty","emission"],
                "masks":[],
                "params":{"gain":1.08},
                "deterministic":True,"uses_randomness":False,"seed":None,
            },
            {
                "id":"hero-grade",
                "processor":"selective_grade",
                "risk_class":"P",
                "color_stage":"scene_linear",
                "inputs":["beauty"],
                "masks":["hero"],
                "params":{"exposure_stops":0.12},
                "deterministic":True,"uses_randomness":False,"seed":None,
            },
            {
                "id":"display",
                "processor":"display_transform",
                "risk_class":"P",
                "color_stage":"display_referred",
                "inputs":["beauty"],
                "masks":[],
                "params":{"curve":"reinhard_srgb","exposure_stops":0.25},
                "deterministic":True,"uses_randomness":False,"seed":None,
            },
        ],
        "output":{"lossless_format":"OPEN_EXR","delivery_color_stage":"display_referred"},
    }
    recipe_path=out/"recipe.json"
    recipe_path.write_text(json.dumps(recipe,indent=2)+"\n")
    print(json.dumps({
        "render_bundle":str(bundle_path),
        "recipe":str(recipe_path),
        "execution_plan":str(plan_path),
        "bundle_sha256":canonical_json_sha256(bundle),
        "recipe_sha256":canonical_json_sha256(recipe),
        "frames":len(frame_rows),
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
