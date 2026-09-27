import bpy, math, os
from mathutils import Vector
from pathlib import Path

P=Path(__file__).resolve().parents[1]
ROOT=P.parents[2]
OUT=P/'renders'; OUT.mkdir(exist_ok=True)
SCENES=P/'scenes'; SCENES.mkdir(exist_ok=True)
FRAME_DIR=OUT/'probe-v2-frames'; FRAME_DIR.mkdir(exist_ok=True)
REVIEW=P/'review'; REVIEW.mkdir(exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.eevee.taa_render_samples=8
sc.render.resolution_x=640
sc.render.resolution_y=360
sc.render.resolution_percentage=100
sc.render.fps=4
sc.frame_step=6
sc.render.image_settings.file_format='PNG'
sc.render.filepath=str(FRAME_DIR/'frame_')
sc.world=bpy.data.worlds.new('World')
sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value=(0.002,0.006,0.012,1)
bg.inputs['Strength'].default_value=.08

def mat(name,base,metal=.0,rough=.45,emission=None,strength=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*base,1)
    b.inputs['Metallic'].default_value=metal
    b.inputs['Roughness'].default_value=rough
    if emission is not None:
        b.inputs['Emission Color'].default_value=(*emission,1)
        b.inputs['Emission Strength'].default_value=strength
    return m

M_DARK=mat('dark',(0.012,.025,.04),.55,.35)
M_METAL=mat('metal',(.10,.17,.23),.8,.24)
M_SHIP=mat('ship',(.08,.28,.38),.65,.28,(.05,.42,.62),.85)
M_CYAN=mat('cyan',(.03,.28,.34),.25,.3,(.04,.85,1),3.2)
M_GOLD=mat('gold',(.36,.18,.03),.25,.35,(1,.48,.07),3.4)
M_BLUE=mat('planet',(.018,.12,.22),.2,.58,(.01,.08,.16),.22)
M_WHITE=mat('white',(.55,.70,.78),.55,.2,(.2,.4,.5),.35)

def cube(name,loc,scale,material,bev=.06):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        mod=o.modifiers.new('edge','BEVEL'); mod.width=bev; mod.segments=2
    o.data.materials.append(material)
    return o

def add_area(loc,energy,size,color):
    bpy.ops.object.light_add(type='AREA',location=loc)
    l=bpy.context.object;l.data.energy=energy;l.data.size=size;l.data.color=color
    return l

def look(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def key_cam(frame,loc,target,lens):
    cam.location=loc;look(cam,target);cam.data.lens=lens
    cam.keyframe_insert('location',frame=frame)
    cam.keyframe_insert('rotation_euler',frame=frame)
    cam.data.keyframe_insert('lens',frame=frame)

def import_probe(name,loc,scale=35):
    asset=ROOT/'external-assets/quaternius/ultimate_space_kit/Spaceship.glb'
    before=set(sc.objects)
    bpy.ops.import_scene.gltf(filepath=str(asset))
    meshes=[o for o in sc.objects if o not in before and o.type=='MESH']
    if not meshes: raise RuntimeError('spaceship mesh import failed')
    ship=meshes[0]
    ship.name=name
    ship.parent=None
    ship.scale=(scale,scale,scale)
    ship.location=loc
    ship.data.materials.clear();ship.data.materials.append(M_SHIP)
    return ship

# --- SHOT 10 / launch-bay zone around x=0 ---
probeA=import_probe('probe_launch',(0,-3.5,2.6),38)
probeA.rotation_euler=(0,0,math.radians(4))
cube('launch_floor',(0,2,-.22),(13,15,.22),M_DARK,0)
for side in (-1,1):
    for j in range(6):
        y=-8+j*3.1
        cube(f'gantry_{side}_{j}',(side*5.3,y,3.1),(.22,.22,3.1),M_METAL,.025)
        cube(f'cross_{side}_{j}',(0,y,5.85),(5.5,.10,.10),M_METAL,.02)
        cube(f'warning_{side}_{j}',(side*5.05,y-.16,3.5),(.08,.06,.12),M_GOLD,.01)
for k in range(8):
    cube(f'floorlight_{k}',(-3.6+k*1.03,1.8,.02),(.09,.16,.025),M_CYAN,.01)
for fr,loc,rz in [(1,(0,-3.5,2.6),4),(84,(0,-.6,2.8),1),(168,(0,4.6,3.15),-4)]:
    probeA.location=loc;probeA.rotation_euler=(0,0,math.radians(rz))
    probeA.keyframe_insert('location',frame=fr);probeA.keyframe_insert('rotation_euler',frame=fr)
add_area((-4,-2,7),1300,7,(.28,.68,1))
add_area((5,4,5),950,6,(1,.28,.08))

# --- SHOT 11 / launch-to-orbit zone around x=40 ---
probeB=import_probe('probe_orbit',(35,-3,5.0),36)
probeB.rotation_euler=(math.radians(-8),math.radians(8),math.radians(24))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=(43,14,-8),radius=12)
planet=bpy.context.object;planet.name='planet';planet.data.materials.append(M_BLUE)
for k in range(7):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=9.0+k*.48,minor_radius=.045,
        location=(43,14,-8),
        rotation=(math.radians(66+k*1.5),0,math.radians(k*10))
    )
    bpy.context.object.data.materials.append(M_CYAN if k%2 else M_WHITE)
# engine/data trail as fixed luminous breadcrumbs
for k in range(22):
    cube(f'trail_{k}',(34-k*.28,-3-k*.16,4.75-k*.03),(.045,.045,.045),M_CYAN,.0)
for fr,loc,rot in [
    (169,(35,-3,5),( -8,8,24)),
    (250,(39,2,7),( -3,12,18)),
    (320,(43,7,9),( 3,18,10)),
    (360,(46,10,10.5),( 7,23,3)),
]:
    probeB.location=loc
    probeB.rotation_euler=tuple(math.radians(v) for v in rot)
    probeB.keyframe_insert('location',frame=fr);probeB.keyframe_insert('rotation_euler',frame=fr)
add_area((37,-1,12),1800,9,(.3,.72,1))
add_area((49,9,7),1100,7,(1,.38,.10))

# --- SHOT 20 / station + boundary zone around x=80 ---
probeC=import_probe('probe_station',(74,-4,4.3),30)
probeC.rotation_euler=(math.radians(-3),math.radians(12),math.radians(18))
# planet limb below station for scale
bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=20,location=(82,18,-11),radius=13)
planet2=bpy.context.object;planet2.name='planet_station';planet2.data.materials.append(M_BLUE)
for radius in (2.8,4.0,5.2):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,minor_radius=.14,
        location=(82,5.5,4.2),rotation=(math.radians(90),0,0)
    )
    bpy.context.object.data.materials.append(M_METAL)
for k in range(16):
    a=k*math.tau/16
    cube(f'station_light_{k}',(82+5.2*math.cos(a),5.5,4.2+5.2*math.sin(a)),(.10,.10,.10),M_GOLD,.0)
# data boundary as spaced luminous columns, readable but not a wall
for k in range(-10,11):
    cube(f'boundary_{k}',(90,5.5,4.2+k*.48),(.035,5.5,.018),M_CYAN,.0)
# small service craft silhouettes
for i in range(4):
    cube(f'service_{i}',(79+i*1.3,1.2+i*.8,2.0+i*.45),(.42,.16,.11),M_WHITE,.04)
for fr,loc,rot in [
    (361,(74,-4,4.3),(-3,12,18)),
    (430,(77,-1,4.8),(0,16,12)),
    (490,(80,1.5,5.2),(2,19,6)),
    (528,(83,3.2,5.5),(4,22,0)),
]:
    probeC.location=loc
    probeC.rotation_euler=tuple(math.radians(v) for v in rot)
    probeC.keyframe_insert('location',frame=fr);probeC.keyframe_insert('rotation_euler',frame=fr)
add_area((76,-1,12),1600,8,(.3,.72,1))
add_area((88,8,7),950,7,(1,.42,.12))

bpy.ops.object.camera_add()
cam=bpy.context.object
sc.camera=cam
for args in [
    (1,(-9,-11,5.1),(0,.5,2.7),47),
    (84,(1,-8,4.2),(0,1.2,2.8),50),
    (168,(8,-3,5.7),(0,3.5,3.0),55),
    (169,(29,-8,7.2),(37,1,5.6),48),
    (250,(34,-4,8.8),(40,4,7.0),44),
    (320,(31,1,13),(43,8,6.5),52),
    (360,(30,4,14),(45,10,7.0),58),
    (361,(69,-11,7.5),(78,3,4.4),46),
    (440,(73,-9,9.0),(79.5,4.5,4.6),48),
    (528,(77,-8,11.0),(81.5,5.5,4.8),52),
]:
    key_cam(*args)

bpy.ops.wm.save_as_mainfile(filepath=str(SCENES/'probe-world-v2.blend'))

if os.environ.get('SECOND_EARTH_PROBE_PREVIEW')=='1':
    sc.frame_set(264)
    sc.render.filepath=str(REVIEW/'probe-v2-preview.png')
    bpy.ops.render.render(write_still=True)
    print('PROBE_V2_PREVIEW',sc.render.filepath,flush=True)
else:
    expected=list(range(1,529,6))
    done={int(f.stem.split('_')[-1]) for f in FRAME_DIR.glob('frame_*.png') if f.stem.split('_')[-1].isdigit()}
    missing=[f for f in expected if f not in done]
    if missing:
        sc.frame_start=missing[0]
        sc.frame_end=528
        bpy.ops.render.render(animation=True)
    print('BLENDER_PROBE_V2_READY',len(list(FRAME_DIR.glob('frame_*.png'))),flush=True)