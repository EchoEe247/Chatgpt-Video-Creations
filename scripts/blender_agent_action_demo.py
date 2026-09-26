import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
END_FRAME = 96
WIDTH = 640
HEIGHT = 360


def args_after_dash():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def mat(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    return m


def cube(name, location, scale, material=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def sphere(name, location, radius, material=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def cylinder(name, location, radius, depth, material=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def cylinder_between(name, a, b, radius, material=None):
    a = Vector(a)
    b = Vector(b)
    direction = b - a
    obj = cylinder(name, (a + b) * 0.5, radius, direction.length, material)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def bone_parent_keep_world(obj, armature, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


def add_bone(edit_bones, name, head, tail, parent=None):
    b = edit_bones.new(name)
    b.head = head
    b.tail = tail
    if parent:
        b.parent = edit_bones[parent]
    return b


def fcurve(action, data_path, index, keys, interpolation="BEZIER"):
    fc = action.fcurves.new(data_path=data_path, index=index)
    for frame, value in keys:
        kp = fc.keyframe_points.insert(frame, value)
        kp.interpolation = interpolation
    return fc


def pulse_scale(obj, frames):
    for frame, value in frames:
        obj.scale = (value, value, value)
        obj.keyframe_insert(data_path="scale", frame=frame)


def look_constraint(camera, target):
    con = camera.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"


args = args_after_dash()
if len(args) < 2:
    raise SystemExit("usage: blender_agent_action_demo.py -- OUTPUT_BLEND FRAME_DIR")

output_blend = Path(args[0]).resolve()
frame_dir = Path(args[1]).resolve()
output_blend.parent.mkdir(parents=True, exist_ok=True)
frame_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.world = bpy.data.worlds.new("DemoWorld")
scene.world.color = (0.012, 0.018, 0.030)
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(frame_dir / "frame_")
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = END_FRAME
scene.frame_step = 1
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "studio.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.8
scene.display.shading.curvature_valley_factor = 1.25
scene.display.shading.show_specular_highlight = True
scene.view_settings.look = "AgX - Medium High Contrast"

dark = mat("CorridorDark", (0.085, 0.11, 0.16))
panel = mat("Panel", (0.23, 0.28, 0.36))
accent = mat("Accent", (0.05, 0.62, 1.00))
warning = mat("Warning", (1.00, 0.28, 0.03))
armor = mat("Armor", (0.32, 0.37, 0.45))
armor2 = mat("ArmorLight", (0.58, 0.64, 0.72))
visor = mat("Visor", (0.03, 0.78, 1.00))
weapon_mat = mat("Weapon", (0.12, 0.14, 0.18))
crate_mat = mat("Crate", (0.28, 0.19, 0.09))
drone_mat = mat("Drone", (0.18, 0.22, 0.27))

# Corridor shell and strong perspective anchors.
cube("Floor", (0, 0, -0.12), (4.8, 9.2, 0.12), dark)
cube("WallL", (-4.3, 0, 2.2), (0.12, 9.2, 2.3), dark)
cube("WallR", (4.3, 0, 2.2), (0.12, 9.2, 2.3), dark)
cube("Ceiling", (0, 0, 4.55), (4.4, 9.2, 0.10), dark)

for y in (-8, -5, -2, 1, 4, 7):
    cube(f"ArchL_{y}", (-3.8, y, 2.1), (0.22, 0.11, 2.0), panel, 0.05)
    cube(f"ArchR_{y}", (3.8, y, 2.1), (0.22, 0.11, 2.0), panel, 0.05)
    cube(f"ArchTop_{y}", (0, y, 4.0), (3.8, 0.11, 0.18), panel, 0.05)
    cube(f"LightL_{y}", (-3.55, y + 0.03, 3.35), (0.06, 0.20, 0.35), accent, 0.02)
    cube(f"LightR_{y}", (3.55, y + 0.03, 3.35), (0.06, 0.20, 0.35), accent, 0.02)

# Floor markings make speed and foot contact easier to read.
for y in range(-8, 9, 2):
    cube(f"FloorMark_{y}", (0, y, 0.015), (0.12, 0.62, 0.02), panel, 0.01)

for x, y, z, sx, sy, sz in (
    (-3.25, 2.4, 0.55, 0.65, 0.70, 0.55),
    (-2.9, 3.2, 0.35, 0.45, 0.50, 0.35),
    (3.1, 5.4, 0.45, 0.60, 0.55, 0.45),
):
    cube("Crate", (x, y, z), (sx, sy, sz), crate_mat, 0.08)

# Humanoid armature.
arm_data = bpy.data.armatures.new("AgentRigData")
arm = bpy.data.objects.new("AgentRig", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones

add_bone(eb, "root", (0, 0, 0.86), (0, 0, 1.42))
add_bone(eb, "spine", (0, 0, 1.42), (0, 0, 2.46), "root")
add_bone(eb, "head", (0, 0, 2.46), (0, 0, 3.04), "spine")
add_bone(eb, "upper_arm.L", (0.07, 0, 2.28), (0.78, 0, 2.17), "spine")
add_bone(eb, "forearm.L", (0.78, 0, 2.17), (1.40, 0, 2.03), "upper_arm.L")
add_bone(eb, "hand.L", (1.40, 0, 2.03), (1.68, 0, 2.00), "forearm.L")
add_bone(eb, "upper_arm.R", (-0.07, 0, 2.28), (-0.78, 0, 2.17), "spine")
add_bone(eb, "forearm.R", (-0.78, 0, 2.17), (-1.40, 0, 2.03), "upper_arm.R")
add_bone(eb, "hand.R", (-1.40, 0, 2.03), (-1.68, 0, 2.00), "forearm.R")
add_bone(eb, "thigh.L", (0.25, 0, 1.10), (0.28, 0, 0.42), "root")
add_bone(eb, "shin.L", (0.28, 0, 0.42), (0.28, 0, -0.33), "thigh.L")
add_bone(eb, "thigh.R", (-0.25, 0, 1.10), (-0.28, 0, 0.42), "root")
add_bone(eb, "shin.R", (-0.28, 0, 0.42), (-0.28, 0, -0.33), "thigh.R")

bpy.ops.object.mode_set(mode="POSE")
for pb in arm.pose.bones:
    pb.rotation_mode = "XYZ"
bpy.ops.object.mode_set(mode="OBJECT")

# Visible body, front faces +Y.
torso = cube("Torso", (0, 0, 1.85), (0.50, 0.29, 0.70), armor, 0.08)
bone_parent_keep_world(torso, arm, "spine")
chest = cube("ChestPlate", (0, 0.29, 2.05), (0.44, 0.07, 0.36), armor2, 0.05)
bone_parent_keep_world(chest, arm, "spine")
helmet = sphere("Helmet", (0, 0, 2.78), 0.40, armor2)
bone_parent_keep_world(helmet, arm, "head")
visor_obj = cube("Visor", (0, 0.35, 2.81), (0.28, 0.055, 0.10), visor, 0.03)
bone_parent_keep_world(visor_obj, arm, "head")
hips = cube("Hips", (0, 0, 1.18), (0.43, 0.25, 0.22), armor, 0.06)
bone_parent_keep_world(hips, arm, "root")

# Legs remain articulated by the armature.
for side, sign in (("L", 1.0), ("R", -1.0)):
    thigh = cylinder(f"Thigh.{side}", (0.26 * sign, 0, 0.78), 0.18, 0.67, armor)
    bone_parent_keep_world(thigh, arm, f"thigh.{side}")
    shin = cylinder(f"Shin.{side}", (0.28 * sign, 0, 0.03), 0.16, 0.70, armor2)
    bone_parent_keep_world(shin, arm, f"shin.{side}")
    foot = cube(f"Foot.{side}", (0.28 * sign, 0.16, -0.34), (0.17, 0.30, 0.10), armor, 0.04)
    bone_parent_keep_world(foot, arm, f"shin.{side}")

# Upper body is deliberately coherent: arms, hands and rifle stay attached to
# the torso instead of using the old underconstrained hand/IK blockout.
arm_points = {
    "R": ((-0.45,0.10,2.24), (-0.62,0.46,2.08), (-0.26,0.82,1.98)),
    "L": ((0.45,0.10,2.24), (0.62,0.48,2.10), (0.10,0.94,1.98)),
}
for side,(shoulder,elbow,hand_pos) in arm_points.items():
    upper = cylinder_between(f"UpperArm.{side}", shoulder, elbow, 0.14, armor)
    lower = cylinder_between(f"Forearm.{side}", elbow, hand_pos, 0.12, armor2)
    elbow_obj = sphere(f"Elbow.{side}", elbow, 0.13, armor)
    hand = sphere(f"Hand.{side}", hand_pos, 0.14, armor)
    for obj in (upper, lower, elbow_obj, hand):
        bone_parent_keep_world(obj, arm, "spine")

gun = cube("PulseCarbine", (0.0, 0.98, 1.98), (0.12, 0.72, 0.10), weapon_mat, 0.035)
barrel = cube("CarbineBarrel", (0.0, 1.68, 1.98), (0.060, 0.30, 0.060), weapon_mat, 0.02)
stock = cube("CarbineStock", (0.0, 0.30, 1.98), (0.17, 0.19, 0.14), weapon_mat, 0.03)
sight = cube("CarbineSight", (0.0, 1.05, 2.12), (0.06, 0.13, 0.06), accent, 0.02)
for obj in (gun, barrel, stock, sight):
    bone_parent_keep_world(obj, arm, "spine")

# Muzzle and tracer effects align with the rifle and target.
flash = sphere("MuzzleFlash", (0.0, 2.02, 1.98), 0.20, warning)
bone_parent_keep_world(flash, arm, "spine")
pulse_scale(flash, [(1, 0.001), (61, 0.001), (62, 1.0), (63, 0.001), (67, 0.001), (68, 0.85), (69, 0.001), (97, 0.001)])

tracer1 = cube("TracerA", (0.0, 4.20, 1.98), (0.035, 2.20, 0.035), warning, 0.01)
pulse_scale(tracer1, [(1, 0.001), (61, 0.001), (62, 1.0), (63, 0.001), (97, 0.001)])
tracer2 = cube("TracerB", (0.06, 4.20, 2.03), (0.030, 2.20, 0.030), warning, 0.01)
pulse_scale(tracer2, [(1, 0.001), (67, 0.001), (68, 1.0), (69, 0.001), (97, 0.001)])

# Target drone. It visibly reacts to the hit instead of remaining static.
drone = cube("TargetDrone", (-0.35, 6.65, 1.95), (0.52, 0.30, 0.30), drone_mat, 0.09)
core = sphere("TargetCore", (-0.35, 6.32, 1.95), 0.17, warning)
for obj in (drone, core):
    obj.keyframe_insert(data_path="location", frame=1)
    obj.keyframe_insert(data_path="location", frame=68)
drone.location = (0.75, 6.95, 0.70)
drone.rotation_euler = (0.8, -0.4, 1.1)
drone.keyframe_insert(data_path="location", frame=86)
drone.keyframe_insert(data_path="rotation_euler", frame=86)
core.location = (0.70, 6.65, 0.75)
core.keyframe_insert(data_path="location", frame=86)
pulse_scale(core, [(1, 1.0), (68, 1.0), (70, 1.8), (74, 0.65), (86, 0.18), (97, 0.18)])

impact = sphere("ImpactBurst", (-0.35, 6.32, 1.95), 0.34, warning)
pulse_scale(impact, [(1, 0.001), (67, 0.001), (68, 0.25), (70, 1.35), (74, 0.001), (97, 0.001)])

# One coherent action: sprint -> brake/plant -> raise weapon -> two shots -> target drops.
action = bpy.data.actions.new("Agent_Sprint_Plant_Fire")

# Whole-body travel with deceleration and lateral weight shift.
fcurve(action, "location", 0, [(1, 0.15), (12, -0.10), (24, 0.12), (36, -0.08), (48, 0.05), (60, 0.0), (96, 0.0)])
fcurve(action, "location", 1, [(1, -6.4), (18, -4.2), (36, -1.8), (48, -0.35), (56, 0.45), (62, 0.75), (96, 0.82)], "BEZIER")
fcurve(action, "location", 2, [(1, 0.00), (6, 0.10), (12, 0.00), (18, 0.11), (24, 0.00), (30, 0.10), (36, 0.00), (42, 0.08), (48, 0.0), (56, -0.05), (62, 0.0), (96, 0.0)])

# Gait resolves into a planted stance.
walk_l = [(1,0.72),(7,-0.68),(13,0.72),(19,-0.68),(25,0.68),(31,-0.62),(37,0.58),(43,-0.50),(49,0.32),(55,-0.18),(60,0.04),(66,0.0),(96,0.0)]
fcurve(action, 'pose.bones["thigh.L"].rotation_euler', 0, walk_l)
fcurve(action, 'pose.bones["thigh.R"].rotation_euler', 0, [(f,-v) for f,v in walk_l])
fcurve(action, 'pose.bones["shin.L"].rotation_euler', 0, [(f,max(0.0,-v)*0.95) for f,v in walk_l])
fcurve(action, 'pose.bones["shin.R"].rotation_euler', 0, [(f,max(0.0,v)*0.95) for f,v in walk_l])

# Torso/hips visibly participate in locomotion and recoil.
fcurve(action, 'pose.bones["root"].rotation_euler', 0, [(1,0.16),(24,0.12),(42,0.08),(50,-0.10),(58,-0.16),(62,-0.10),(64,0.03),(68,-0.08),(70,0.03),(96,0.0)])
fcurve(action, 'pose.bones["root"].rotation_euler', 1, [(1,0.05),(18,-0.05),(36,0.04),(48,-0.04),(60,0.0),(96,0.0)])
fcurve(action, 'pose.bones["spine"].rotation_euler', 0, [(1,-0.10),(18,-0.08),(36,-0.08),(48,0.04),(56,0.10),(62,0.15),(64,0.02),(68,0.10),(70,0.02),(96,0.03)])
fcurve(action, 'pose.bones["spine"].rotation_euler', 1, [(1,0.02),(12,-0.04),(24,0.05),(36,-0.04),(48,0.04),(60,0.0),(96,0.0)])
fcurve(action, 'pose.bones["spine"].rotation_euler', 2, [(1,-0.06),(12,0.08),(24,-0.07),(36,0.07),(48,-0.04),(56,0.02),(96,0.0)])
fcurve(action, 'pose.bones["head"].rotation_euler', 2, [(1,0.08),(24,-0.08),(44,0.04),(56,0.0),(96,0.0)])

# Weapon transitions from low-ready to a deliberate firing posture.

arm.animation_data_create()
track = arm.animation_data.nla_tracks.new()
track.name = "Action"
strip = track.strips.new("SprintPlantFire", 1, action)
strip.frame_end = END_FRAME
arm.animation_data.action = None

# Focus objects for three meaningful camera beats.
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0.5, 1.60))
agent_focus = bpy.context.object
agent_focus.name = "AgentFocus"
agent_focus.parent = arm

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0.35, 1.85))
aim_focus = bpy.context.object
aim_focus.name = "AimFocus"
aim_focus.parent = arm

bpy.ops.object.empty_add(type="PLAIN_AXES", location=(-0.35, 6.65, 1.85))
impact_focus = bpy.context.object
impact_focus.name = "ImpactFocus"

# Shot 1: wide 3/4 tracking sprint.
bpy.ops.object.camera_add(location=(3.15, -7.0, 3.0))
cam_wide = bpy.context.object
cam_wide.name = "Cam_WideRun"
cam_wide.data.lens = 26
look_constraint(cam_wide, agent_focus)
for f, loc in ((1,(3.15,-7.0,3.0)),(24,(3.05,-4.8,2.9)),(42,(3.0,-2.4,2.75))):
    cam_wide.location = loc
    cam_wide.keyframe_insert(data_path="location", frame=f)

# Shot 2: closer over-shoulder/side view for the plant and firing.
bpy.ops.object.camera_add(location=(3.45, -1.2, 2.7))
cam_aim = bpy.context.object
cam_aim.name = "Cam_Aim"
cam_aim.data.lens = 28
look_constraint(cam_aim, agent_focus)
for f, loc in ((43,(3.45,-1.2,2.7)),(58,(3.35,-0.65,2.65)),(71,(3.25,-0.2,2.58))):
    cam_aim.location = loc
    cam_aim.keyframe_insert(data_path="location", frame=f)

# Shot 3: target impact angle, held long enough to read the consequence.
bpy.ops.object.camera_add(location=(2.75, 4.3, 2.45))
cam_impact = bpy.context.object
cam_impact.name = "Cam_Impact"
cam_impact.data.lens = 42
look_constraint(cam_impact, drone)

scene.camera = cam_wide
for name, frame, cam in (("WIDE",1,cam_wide),("AIM",43,cam_aim),("IMPACT",72,cam_impact)):
    marker = scene.timeline_markers.new(name, frame=frame)
    marker.camera = cam

scene["agent_demo"] = {
    "fps": FPS,
    "end_frame": END_FRAME,
    "story_beats": "sprint -> plant -> fire -> impact",
    "ik_constraint": "none",
    "nla_track": track.name,
    "cameras": "WIDE@1 AIM@43 IMPACT@72",
}

bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
print(f"AGENT_ACTION_DEMO_V2 blend={output_blend} frames={END_FRAME} fps={FPS} ik=none nla={track.name}")
