import bpy, math
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];OUT=P/'renders';OUT.mkdir(exist_ok=True);SCENES=P/'scenes';SCENES.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=360;sc.render.resolution_percentage=100;sc.render.fps=6;sc.frame_step=4
FRAME_DIR=OUT/'probe-frames';FRAME_DIR.mkdir(exist_ok=True)
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(FRAME_DIR/'frame_')
expected=list(range(1,552+1,4))
done={int(p.stem.split('_')[-1]) for p in FRAME_DIR.glob('frame_*.png') if p.stem.split('_')[-1].isdigit()}
missing=[f for f in expected if f not in done]
sc.frame_start=(missing[0] if missing else 528);sc.frame_end=528
sc.display.shading.light='STUDIO';sc.display.shading.color_type='OBJECT';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
sc.world=bpy.data.worlds.new('World');sc.world.color=(.003,.006,.012)
METAL=(.18,.23,.27,1);DARK=(.03,.05,.07,1);CYAN=(.06,.58,.72,1);GOLD=(.72,.43,.11,1);BLUE=(.035,.18,.27,1);WHITE=(.72,.82,.86,1)
def cube(name,loc,scale,col):
 bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.color=col;return o
# Simple authored probe body plus local asset import as visible hull detail if stable.
cube('probeA',(0,-2,2.4),(1.5,.55,.35),WHITE);cube('probeA_nose',(1.8,-2,2.4),(.45,.4,.28),CYAN)
probeA=bpy.data.objects['probeA']
probeB=cube('probeB',(36,-2,4),(1.5,.55,.35),WHITE);cube('probeB_nose',(37.8,-2,4),(.45,.4,.28),CYAN)
probeC=cube('probeC',(74,-3,3),(1.5,.55,.35),WHITE);cube('probeC_nose',(75.8,-3,3),(.45,.4,.28),CYAN)
# launch bay
cube('floor',(0,2,-.25),(14,15,.25),DARK)
for side in (-1,1):
 for j in range(6):
  cube('gantry',(side*5,-8+j*3,3),(.25,.25,3),METAL);cube('beam',(0,-8+j*3,5.7),(5.2,.12,.12),METAL)
for fr,y in [(1,-2),(168,4)]:probeA.location.y=y;probeA.keyframe_insert('location',frame=fr)
# orbit planet
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(40,10,-13),radius=14);planet=bpy.context.object;planet.color=BLUE
for k in range(6):
 bpy.ops.mesh.primitive_torus_add(major_radius=10+k*.55,minor_radius=.035,location=(40,10,-13),rotation=(math.radians(68+k*2),0,math.radians(k*11)));bpy.context.object.color=CYAN if k%2 else WHITE
for fr,loc in [(169,(36,-2,4)),(360,(45,7,10))]:probeB.location=loc;probeB.keyframe_insert('location',frame=fr)
# station/boundary
for r in (3,4.2,5.4):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=.18,location=(80,5,4),rotation=(math.radians(90),0,0));bpy.context.object.color=METAL
for k in range(12):
 a=k*math.tau/12;cube('stationlight',(80+5.4*math.cos(a),5,4+5.4*math.sin(a)),(.12,.12,.12),GOLD)
for k in range(-9,10):cube('boundary',(89,5,k*.55+4),(.035,6,.035),CYAN)
for fr,loc in [(361,(74,-3,3)),(528,(83,3,5))]:probeC.location=loc;probeC.keyframe_insert('location',frame=fr)
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam
def look(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def key(fr,loc,target,lens):
 cam.location=loc;look(cam,target);cam.data.lens=lens;cam.keyframe_insert('location',frame=fr);cam.keyframe_insert('rotation_euler',frame=fr);cam.data.keyframe_insert('lens',frame=fr)
for args in [(1,(-10,-9,3.5),(0,1,2.8),46),(168,(8,-3,5),(0,4,2.8),52),(169,(31,-7,5),(38,2,4),48),(280,(37,-3,5.5),(41,5,5),40),(360,(27,1,13),(43,7,5),55),(361,(72,-9,3),(80,4,4),45),(528,(82,-9,12),(81,5,4),52)]:key(*args)
bpy.ops.wm.save_as_mainfile(filepath=str(SCENES/'probe-world.blend'))
if missing:
 bpy.ops.render.render(animation=True)
print('BLENDER_PROBE_READY',len(list(FRAME_DIR.glob('frame_*.png'))),flush=True)