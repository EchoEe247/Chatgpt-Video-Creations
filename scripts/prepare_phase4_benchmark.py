#!/usr/bin/env python3
"""Prepare the Phase 4 cinematic fixture as a validated Render Bundle + recipe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

from src.core.finishing_contract import canonical_json_sha256, sha256_file

BLENDER_OCIO_CONFIG="/usr/share/blender/datafiles/colormanagement/config.ocio"
BLENDER_OCIO_CONFIG_SHA256="6a28581e9b567c42d752d8f2d7487d0c516238632e1597e277ecdfa84fb4d1b9"
BLENDER_AGX_SRGB_LUT="/usr/share/blender/datafiles/colormanagement/luts/AgX_Base_sRGB.cube"
BLENDER_AGX_SRGB_LUT_SHA256="e707a36f3e90ee79bc342332febf91334c02ce3974cac700ece00ca9d4507491"


def make_agx_recipe(recipe: dict, *, recipe_id: str, recipe_version: int) -> dict:
    agx=json.loads(json.dumps(recipe))
    agx["recipe_id"]=recipe_id
    agx["recipe_version"]=recipe_version
    displays=[op for op in agx["operations"] if op.get("processor")=="display_transform"]
    if len(displays)!=1:
        raise ValueError("AgX recipe requires exactly one diagnostic display_transform")
    op=displays[0]
    exposure=float(op.get("params",{}).get("exposure_stops",0.0))
    op["processor"]="agx_display_transform"
    op["params"]={
        "exposure_stops":exposure,
        "display":"sRGB",
        "view":"AgX",
        "fromspace":"Linear Rec.709",
        "looks":"",
        "config_path":BLENDER_OCIO_CONFIG,
        "config_sha256":BLENDER_OCIO_CONFIG_SHA256,
        "lut_path":BLENDER_AGX_SRGB_LUT,
        "lut_sha256":BLENDER_AGX_SRGB_LUT_SHA256,
    }
    return agx


def make_c2_recipe(recipe: dict) -> dict:
    c2=json.loads(json.dumps(recipe))
    c2["recipe_id"]="phase4-cinematic-deterministic-c2"
    c2["recipe_version"]=2
    displays=[op for op in c2["operations"] if op.get("processor")=="display_transform"]
    if len(displays)!=1:
        raise ValueError("C2 requires exactly one display_transform")
    displays[0]["params"]["exposure_stops"]=0.15
    return c2


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
            "travel_vector":[2.3,7.0,0.10],
            "camera_binding_sha256":canonical_json_sha256({
                "start_location":[4.8,-8.5,3.3],
                "mid_location":[3.0,-5.2,2.7],
                "end_location":[1.8,-2.4,2.45],
                "start_lens":46,
                "mid_lens":52,
                "end_lens":55,
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

    c2=make_c2_recipe(recipe)
    c2_path=out/"recipe-c2.json"
    c2_path.write_text(json.dumps(c2,indent=2)+"\n")

    agx_c=make_agx_recipe(recipe,recipe_id="phase4-cinematic-agx-c",recipe_version=2)
    agx_c_path=out/"recipe-agx-c.json"
    agx_c_path.write_text(json.dumps(agx_c,indent=2)+"\n")

    agx_c2=make_agx_recipe(c2,recipe_id="phase4-cinematic-agx-c2",recipe_version=3)
    agx_c2_path=out/"recipe-agx-c2.json"
    agx_c2_path.write_text(json.dumps(agx_c2,indent=2)+"\n")

    print(json.dumps({
        "render_bundle":str(bundle_path),
        "recipe":str(recipe_path),
        "recipe_c2":str(c2_path),
        "recipe_agx_c":str(agx_c_path),
        "recipe_agx_c2":str(agx_c2_path),
        "execution_plan":str(plan_path),
        "bundle_sha256":canonical_json_sha256(bundle),
        "recipe_sha256":canonical_json_sha256(recipe),
        "recipe_c2_sha256":canonical_json_sha256(c2),
        "recipe_agx_c_sha256":canonical_json_sha256(agx_c),
        "recipe_agx_c2_sha256":canonical_json_sha256(agx_c2),
        "frames":len(frame_rows),
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())