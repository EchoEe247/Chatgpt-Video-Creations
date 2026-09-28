#!/usr/bin/env python3
"""Blender-side smoke proof for the local multilayer EXR/AOV path."""
from __future__ import annotations
import argparse, json, os, sys
import bpy
from mathutils import Vector

def args():
    argv=sys.argv
    argv=argv[argv.index("--")+1:] if "--" in argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="//multipass-smoke.exr")
    p.add_argument("--report",default="//multipass-smoke.json")
    return p.parse_args(argv)

def main():
    a=args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    for candidate in ("BLENDER_EEVEE","BLENDER_EEVEE_NEXT","CYCLES"):
        try:
            scene.render.engine=candidate
            break
        except Exception:
            continue
    scene.render.resolution_x=96
    scene.render.resolution_y=64
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth="16"
    scene.render.filepath=bpy.path.abspath(a.output)

    bpy.ops.mesh.primitive_plane_add(size=8, location=(0,0,0))
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,1))
    cube=bpy.context.object
    mat=bpy.data.materials.new("Hero")
    mat.diffuse_color=(0.08,0.25,0.8,1)
    cube.data.materials.append(mat)
    bpy.ops.object.light_add(type="AREA", location=(3,-3,5))
    bpy.context.object.data.energy=900
    bpy.context.object.data.size=5
    bpy.ops.object.camera_add(location=(6,-7,5))
    cam=bpy.context.object
    scene.camera=cam
    cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat("-Z","Y").to_euler()

    layer=scene.view_layers[0]
    requested={
        "depth":"use_pass_z",
        "normal":"use_pass_normal",
        "vector":"use_pass_vector",
        "diffuse_direct":"use_pass_diffuse_direct",
        "diffuse_indirect":"use_pass_diffuse_indirect",
        "glossy_direct":"use_pass_glossy_direct",
        "glossy_indirect":"use_pass_glossy_indirect",
        "emission":"use_pass_emit",
        "shadow":"use_pass_shadow",
        "mist":"use_pass_mist",
        "ambient_occlusion":"use_pass_ambient_occlusion",
        "object_index":"use_pass_object_index",
        "material_index":"use_pass_material_index",
        "cryptomatte_object":"use_pass_cryptomatte_object",
        "cryptomatte_material":"use_pass_cryptomatte_material",
    }
    enabled={}
    unsupported={}
    for name,attr in requested.items():
        if not hasattr(layer,attr):
            unsupported[name]="attribute_missing"
            continue
        try:
            setattr(layer,attr,True)
            enabled[name]=bool(getattr(layer,attr))
        except Exception as exc:
            unsupported[name]=str(exc)

    bpy.ops.render.render(write_still=True)
    out=bpy.path.abspath(a.output)
    report=bpy.path.abspath(a.report)
    data={
        "blender_version":bpy.app.version_string,
        "engine":scene.render.engine,
        "format":scene.render.image_settings.file_format,
        "enabled":enabled,
        "unsupported":unsupported,
        "output":out,
        "output_exists":os.path.exists(out),
        "output_bytes":os.path.getsize(out) if os.path.exists(out) else 0,
    }
    os.makedirs(os.path.dirname(report),exist_ok=True)
    with open(report,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)
    print(json.dumps(data,indent=2))
    if not data["output_exists"] or data["output_bytes"]<=0 or unsupported:
        raise SystemExit(2)

if __name__=="__main__":
    main()