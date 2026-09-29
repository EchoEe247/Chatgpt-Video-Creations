#!/usr/bin/env python3
"""Phase 0 animated 720p multilayer EXR feasibility fixture.

Run inside Blender:
  blender --background --python-exit-code 1 --python scripts/blender_phase0_fixture.py -- --output-dir PATH

The fixture is intentionally small but animated. It emits one multilayer EXR per
requested frame plus a JSON render receipt. Existing non-empty frames are
skipped so interrupted runs are idempotently resumable.
"""
from __future__ import annotations
import argparse, json, resource, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

def parse_args():
    argv=sys.argv
    argv=argv[argv.index("--")+1:] if "--" in argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True)
    p.add_argument("--frames",default="1,2,3")
    p.add_argument("--engine",default="CYCLES")
    return p.parse_args(argv)

def clean_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def material(name,color,metallic=0.0,roughness=0.5,emission=None):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*color,1.0)
    bsdf.inputs["Metallic"].default_value=metallic
    bsdf.inputs["Roughness"].default_value=roughness
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value=(*emission,1.0)
        bsdf.inputs["Emission Strength"].default_value=3.0
    return m

def point_camera(cam,target):
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()

def build_scene(engine):
    clean_scene()
    scene=bpy.context.scene
    scene.render.engine=engine
    scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
    scene.render.fps=24
    scene.render.image_settings.file_format="OPEN_EXR_MULTILAYER"
    scene.render.image_settings.color_depth="16"
    scene.render.image_settings.exr_codec="ZIP"
    scene.render.threads_mode="FIXED"; scene.render.threads=2
    scene.frame_start=1; scene.frame_end=3
    if engine=="CYCLES":
        scene.cycles.samples=1; scene.cycles.use_denoising=False; scene.cycles.preview_samples=1

    world=scene.world or bpy.data.worlds.new("World"); scene.world=world; world.use_nodes=True
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(0.025,0.04,0.08,1); bg.inputs["Strength"].default_value=0.35

    bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,0))
    ground=bpy.context.object; ground.name="Ground"
    ground.data.materials.append(material("GroundMat",(0.055,0.065,0.08),roughness=0.72))

    bpy.ops.mesh.primitive_cube_add(size=2.0,location=(-2.0,0,1.0))
    hero=bpy.context.object; hero.name="Hero"; hero.scale=(1.7,0.8,0.55)
    hero.data.materials.append(material("HeroMat",(0.04,0.18,0.55),metallic=0.65,roughness=0.24))
    hero.keyframe_insert("location",frame=1)
    hero.location.x=0.0; hero.location.y=0.35; hero.keyframe_insert("location",frame=2)
    hero.location.x=2.0; hero.location.y=0.7; hero.keyframe_insert("location",frame=3)
    if hero.animation_data and hero.animation_data.action:
        for fc in hero.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation="LINEAR"

    bpy.ops.mesh.primitive_cube_add(size=1.1,location=(2.8,3.0,0.55))
    practical=bpy.context.object; practical.name="Practical"
    practical.data.materials.append(material("PracticalMat",(0.25,0.12,0.02),roughness=0.5,emission=(1.0,0.22,0.03)))

    bpy.ops.object.light_add(type="AREA",location=(-2.5,-4.0,7.0))
    key=bpy.context.object; key.data.energy=900; key.data.shape="DISK"; key.data.size=5.0
    bpy.ops.object.light_add(type="AREA",location=(4.0,2.0,4.0))
    fill=bpy.context.object; fill.data.energy=450; fill.data.size=3.0

    bpy.ops.object.camera_add(location=(7.5,-10.5,5.7))
    cam=bpy.context.object; cam.name="Camera"; cam.data.lens=48; scene.camera=cam
    point_camera(cam,(0.5,0.3,0.9))

    layer=scene.view_layers[0]
    requested={
        "depth":"use_pass_z","normal":"use_pass_normal","vector":"use_pass_vector",
        "diffuse_direct":"use_pass_diffuse_direct","glossy_direct":"use_pass_glossy_direct",
        "emission":"use_pass_emit","shadow":"use_pass_shadow","mist":"use_pass_mist",
        "ambient_occlusion":"use_pass_ambient_occlusion",
        "cryptomatte_object":"use_pass_cryptomatte_object",
        "cryptomatte_material":"use_pass_cryptomatte_material",
    }
    enabled={}; unsupported={}
    for name,attr in requested.items():
        if not hasattr(layer,attr):
            unsupported[name]="attribute_missing"; continue
        try:
            setattr(layer,attr,True); enabled[name]=bool(getattr(layer,attr))
        except Exception as exc:
            unsupported[name]=repr(exc)
    return scene,enabled,unsupported

def main():
    args=parse_args()
    out=Path(args.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    report_path=out/"render-receipt.json"
    previous={}
    if report_path.is_file():
        try:
            prior=json.loads(report_path.read_text())
            previous={int(r["frame"]):r for r in prior.get("frames",[]) if "frame" in r}
        except Exception:
            previous={}
    frames=[int(x) for x in args.frames.split(",") if x.strip()]
    scene,enabled,unsupported=build_scene(args.engine)
    rows=[]
    for frame in frames:
        path=out/f"frame-{frame:04d}.exr"
        if path.is_file() and path.stat().st_size>0:
            row=dict(previous.get(frame,{}))
            row.update({"frame":frame,"path":str(path),"bytes":path.stat().st_size,"skipped_existing":True,"resume_verified":True})
            rows.append(row)
            print(f"PHASE0_SKIP frame={frame} bytes={path.stat().st_size}",flush=True)
            continue
        scene.frame_set(frame); scene.render.filepath=str(path)
        before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; t0=time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed=time.monotonic()-t0; after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rows.append({
            "frame":frame,"path":str(path),"bytes":path.stat().st_size if path.exists() else 0,
            "render_seconds":round(elapsed,4),"ru_maxrss_before_kib":before,
            "ru_maxrss_after_kib":after,"skipped_existing":False,"resume_verified":False,
        })
        print(f"PHASE0_FRAME frame={frame} seconds={elapsed:.3f} bytes={path.stat().st_size}",flush=True)

    report={
        "schema_version":1,"blender_version":bpy.app.version_string,"engine":scene.render.engine,
        "resolution":[scene.render.resolution_x,scene.render.resolution_y],"fps":scene.render.fps,
        "frames":rows,"enabled_pass_flags":enabled,"unsupported_pass_flags":unsupported,
        "resume_run":bool(previous),
    }
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print("PHASE0_RECEIPT="+str(report_path),flush=True)
    if unsupported or any(r["bytes"]<=0 for r in rows): raise SystemExit(2)

if __name__=="__main__": main()
