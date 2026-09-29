#!/usr/bin/env python3
"""Phase 4 native-24fps cinematic finishing fixture.

A compact sci-fi corridor with camera parallax, a moving protected subject,
metal/reflection cues, emissive practicals and meaningful depth. Designed to be
representative enough for A/B/C finishing review while remaining feasible on
the Pixel/PRoot Blender runtime.
"""
from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    argv=sys.argv
    argv=argv[argv.index("--")+1:] if "--" in argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True)
    p.add_argument("--start",type=int,default=1)
    p.add_argument("--end",type=int,default=48)
    return p.parse_args(argv)


def mat(name,base,metallic=0.0,roughness=.45,emission=None,strength=0.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*base,1)
    b.inputs["Metallic"].default_value=metallic
    b.inputs["Roughness"].default_value=roughness
    if emission is not None:
        b.inputs["Emission Color"].default_value=(*emission,1)
        b.inputs["Emission Strength"].default_value=strength
    return m


def cube(name,loc,scale,material):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material); return o


def area(name,loc,energy,size,color,rot=(0,0,0)):
    bpy.ops.object.light_add(type="AREA",location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.energy=energy; o.data.shape="DISK"; o.data.size=size; o.data.color=color
    return o


def look(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.render.engine="CYCLES"
    sc.cycles.samples=1
    sc.cycles.use_denoising=False
    sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
    sc.render.fps=24
    sc.render.image_settings.file_format="OPEN_EXR_MULTILAYER"
    sc.render.image_settings.color_depth="16"; sc.render.image_settings.exr_codec="ZIP"
    sc.render.film_transparent=False
    sc.frame_start=1; sc.frame_end=48

    floor=mat("Floor",(0.018,0.028,0.045),metallic=.78,roughness=.2)
    wall=mat("Wall",(0.045,0.07,0.10),metallic=.45,roughness=.34)
    dark=mat("Dark",(0.008,0.012,0.02),metallic=.25,roughness=.48)
    hero_mat=mat("Hero",(0.26,0.065,0.028),metallic=.72,roughness=.22)
    cyan=mat("CyanPractical",(0.015,0.12,0.18),metallic=.15,roughness=.3,emission=(0.02,.65,1.0),strength=5.5)
    amber=mat("AmberPractical",(.22,.07,.01),metallic=.1,roughness=.3,emission=(1.0,.20,.025),strength=4.5)

    cube("Floor",(0,3,-.18),(7,10,.18),floor)
    cube("BackWall",(0,12,3.1),(7,.25,3.3),wall)
    cube("Ceiling",(0,3,6.2),(7,10,.18),dark)
    for x in (-5.8,5.8):
        cube(f"SideWall{x}",(x,3,3),(0.2,10,3.0),wall)
    for y in (-3,2,7):
        cube(f"ColumnL{y}",(-4.5,y,2.6),(.5,.45,2.6),dark)
        cube(f"ColumnR{y}",(4.5,y,2.6),(.5,.45,2.6),dark)
    for y in (-1,4,9):
        cube(f"CeilingStrip{y}",(0,y,5.7),(3.5,.12,.08),cyan if y!=4 else amber)
    cube("Portal",(0,11.65,2.8),(2.8,.08,1.8),cyan)
    cube("ForegroundSlab",(-3.3,-1.2,1.8),(.55,.65,1.8),dark)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(-1.7,2.0,1.25))
    hero=bpy.context.object; hero.name="Hero"; hero.scale=(.72,.72,.48); hero.data.materials.append(hero_mat)
    hero.keyframe_insert("location",frame=1)
    hero.location=(1.6,6.4,1.5); hero.keyframe_insert("location",frame=48)
    if hero.animation_data and hero.animation_data.action:
        for fc in hero.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation="BEZIER"

    area("Key",(-3,-2,5.2),900,4.5,(.25,.55,1.0))
    area("Warm",(3,5.5,4.6),650,3.0,(1.0,.20,.06),rot=(0.35,0,2.8))
    area("Back",(0,10,5.0),800,3.5,(.10,.45,1.0),rot=(0.5,0,3.14))

    world=bpy.data.worlds.new("World"); sc.world=world; world.use_nodes=True
    bg=world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value=(.002,.004,.012,1); bg.inputs["Strength"].default_value=.08

    bpy.ops.object.camera_add(location=(4.8,-8.5,3.3))
    cam=bpy.context.object; cam.name="Camera"; cam.data.lens=46; sc.camera=cam
    look(cam,(0,3.5,1.5)); cam.keyframe_insert("location",frame=1); cam.keyframe_insert("rotation_euler",frame=1); cam.data.keyframe_insert("lens",frame=1)
    cam.location=(3.0,-5.2,2.7); look(cam,(.5,5.5,1.4)); cam.data.lens=52
    cam.keyframe_insert("location",frame=48); cam.keyframe_insert("rotation_euler",frame=48); cam.data.keyframe_insert("lens",frame=48)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation="BEZIER"

    layer=sc.view_layers[0]
    req={"depth":"use_pass_z","normal":"use_pass_normal","emission":"use_pass_emit","ambient_occlusion":"use_pass_ambient_occlusion","cryptomatte_object":"use_pass_cryptomatte_object"}
    enabled={}; unsupported={}
    for name,attr in req.items():
        if not hasattr(layer,attr): unsupported[name]="attribute_missing"; continue
        try: setattr(layer,attr,True); enabled[name]=bool(getattr(layer,attr))
        except Exception as exc: unsupported[name]=repr(exc)
    return sc,enabled,unsupported


def main():
    a=parse_args(); out=Path(a.output_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    if a.start<1 or a.end>48 or a.end<a.start: raise SystemExit("frame range must be within 1..48")
    sc,enabled,unsupported=build_scene()
    prior_path=out/"render-receipt.json"; prior={}
    if prior_path.is_file():
        try: prior=json.loads(prior_path.read_text())
        except Exception: prior={}
    prior_rows={int(x["frame"]):x for x in prior.get("frames",[]) if "frame" in x}
    rows=[]
    for frame in range(a.start,a.end+1):
        path=out/f"frame-{frame:04d}.exr"
        if path.is_file() and path.stat().st_size>0:
            row=dict(prior_rows.get(frame,{})); row.update({"frame":frame,"path":str(path),"bytes":path.stat().st_size,"skipped_existing":True})
            rows.append(row); print(f"P4_SKIP frame={frame}",flush=True); continue
        sc.frame_set(frame); sc.render.filepath=str(path)
        before=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss; t0=time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed=time.monotonic()-t0; after=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rows.append({"frame":frame,"path":str(path),"bytes":path.stat().st_size,"render_seconds":round(elapsed,4),"ru_maxrss_before_kib":before,"ru_maxrss_after_kib":after,"skipped_existing":False})
        print(f"P4_FRAME frame={frame} seconds={elapsed:.3f} bytes={path.stat().st_size}",flush=True)
    receipt={"schema_version":1,"kind":"phase4-cinematic-fixture","blender_version":bpy.app.version_string,"engine":sc.render.engine,"resolution":[1280,720],"fps":24,"frame_start":a.start,"frame_end":a.end,"enabled_pass_flags":enabled,"unsupported_pass_flags":unsupported,"frames":rows}
    prior_path.write_text(json.dumps(receipt,indent=2)+"\n")
    print("P4_RECEIPT="+str(prior_path),flush=True)
    return 0 if not unsupported and all(x["bytes"]>0 for x in rows) else 2


if __name__=="__main__": raise SystemExit(main())