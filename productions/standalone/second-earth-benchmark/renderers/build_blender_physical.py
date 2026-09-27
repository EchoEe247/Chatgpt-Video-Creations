import bpy, math
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'renders';OUT.mkdir(exist_ok=True);SCENES=P/'scenes';SCENES.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=360;sc.render.resolution_percentage=100;sc.render.fps=6;sc.frame_step=4
FRAME_DIR=OUT/'physical-frames';FRAME_DIR.mkdir(exist_ok=True)
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(FRAME_DIR/'frame_')
expected=list(range(1,528+1,4))
done={int(p.stem.split('_')[-1]) for p in FRAME_DIR.glob('frame_*.png') if p.stem.split('_')[-1].isdigit()}
missing=[f for f in expected if f not in done]
sc.frame_start=(missing[0] if missing else 528);sc.frame_end=528
sc.display.shading.light='STUDIO';sc.display.shading.color_type='OBJECT';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
sc.world=bpy.data.worlds.new('World');sc.world.color=(.004,.007,.012)
DARK=(.035,.055,.08,1);METAL=(.12,.18,.22,1);CYAN=(.08,.62,.78,1);GOLD=(.72,.42,.12,1);RED=(.72,.08,.06,1);GREEN=(.08,.55,.25,1);BLACK=(.015,.018,.025,1)
def cube(name,loc,scale,col):
 bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.color=col;return o
def cyl(name,loc,r,depth,col,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=depth,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.color=col;return o
for z in (0,32,64):cube('floor'+str(z),(z,2,-.25),(13,15,.25),DARK)
for side in (-1,1):
 for j in range(7):
  y=-8+j*3;cube('rack',(side*5,y,2.1),(2.2,1,2.1),METAL)
  for k in range(6):cube('led',(side*3,y-.94,.55+k*.58),(.08,.025,.055),CYAN if (k+j)%3 else GOLD)
for j in range(9):cube('over',(0,-10+j*3.2,5.6),(8,.07,.08),METAL)
cube('screen',(32,7,3.1),(7,.18,2.35),CYAN)
for xx in (-5,-2.5,0,2.5,5):cube('screenline',(32+xx,6.78,3.1),(1,.03,.055),GOLD if xx==0 else DARK)
cyl('body',(32,.8,1.35),.52,2.2,BLACK)
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=(32,.8,2.85));bpy.context.object.scale=(.48,.48,.48);bpy.context.object.color=BLACK
cube('breaker_wall',(64,7,3),(7,.4,3.2),METAL)
for row in range(3):
 for col in range(8):
  xx=59.5+col*1.3;zz=1.4+row*1.25;cube('breaker',(xx,6.45,zz),(.33,.18,.45),GREEN if col<5 else RED);cube('lever',(xx,6.12,zz+.05),(.08,.22,.08),GOLD)
cyl('arm',(62.5,1,2),.28,3.4,BLACK,(math.radians(90),0,0));hand=cube('hand',(62.5,2.8,2),(.42,.55,.18),BLACK)
for fr,y in [(361,2.8),(500,5.25),(528,5.45)]:hand.location.y=y;hand.keyframe_insert('location',frame=fr)
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam
def look(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def key(fr,loc,target,lens):
 cam.location=loc;look(cam,target);cam.data.lens=lens;cam.keyframe_insert('location',frame=fr);cam.keyframe_insert('rotation_euler',frame=fr);cam.data.keyframe_insert('lens',frame=fr)
for args in [(1,(-10,-11,3.5),(0,1,2),44),(168,(8,-3.5,4.5),(0,4,2.1),48),(169,(32,-4,3),(32,5.5,3.1),58),(360,(32,-11.5,5.1),(32,1.8,2.7),38),(361,(64,-10.5,3.6),(63,5,2.4),46),(528,(63,-5.4,3),(62.8,5.3,2.1),58)]:key(*args)
bpy.ops.wm.save_as_mainfile(filepath=str(SCENES/'physical-lab.blend'))
if missing:
 bpy.ops.render.render(animation=True)
print('BLENDER_PHYSICAL_READY',len(list(FRAME_DIR.glob('frame_*.png'))),flush=True)