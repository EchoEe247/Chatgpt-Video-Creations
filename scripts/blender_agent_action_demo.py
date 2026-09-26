import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


FPS = 12
END_FRAME = 83
WIDTH = 512
HEIGHT = 288


def args_after_dash():
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


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
    if bevel > 0:
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
    if parent is not None:
        b.parent = edit_bones[parent]
    return b


def fcurve(action, data_path, index, keys, interpolation="BEZIER"):
    fc = action.fcurves.new(data_path=data_path, index=index)
    for frame, value in keys:
        kp = fc.keyframe_points.insert(frame, value)
        kp.interpolation = interpolation
    return fc


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
scene.world.color = (0.018, 0.024, 0.040)
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(frame_dir / "frame_")
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = END_FRAME
scene.frame_step = 2
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "studio.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.7
scene.display.shading.curvature_valley_factor = 1.2
scene.display.shading.show_specular_highlight = True
scene.view_settings.look = "AgX - Medium High Contrast"

dark = mat("CorridorDark", (0.10, 0.13, 0.18))
panel = mat("Panel", (0.20, 0.25, 0.32))
accent = mat("Accent", (0.10, 0.72, 1.0))
armor = mat("Armor", (0.24, 0.28, 0.34))
armor2 = mat("ArmorLight", (0.46, 0.52, 0.58))
visor = mat("Visor", (0.08, 0.78, 1.0))
weapon_mat = mat("Weapon", (0.10, 0.12, 0.15))
muzzle_mat = mat("Muzzle", (1.0, 0.31, 0.04))
crate_mat = mat("Crate", (0.32, 0.22, 0.11))

# Corridor shell.
cube("Floor", (0, 0, -0.12), (4.8, 8.5, 0.12), dark)
cube("WallL", (-4.3, 0, 2.2), (0.12, 8.5, 2.3), dark)
cube("WallR", (4.3, 0, 2.2), (0.12, 8.5, 2.3), dark)
cube("Ceiling", (0, 0, 4.55), (4.4, 8.5, 0.10), dark)

for y in (-7, -4, -1, 2, 5, 8):
    cube(f"ArchL_{y}", (-3.8, y, 2.1), (0.23, 0.12, 2.0), panel, 0.05)
    cube(f"ArchR_{y}", (3.8, y, 2.1), (0.23, 0.12, 2.0), panel, 0.05)
    cube(f"ArchTop_{y}", (0, y, 4.0), (3.8, 0.12, 0.18), panel, 0.05)
    cube(f"LightL_{y}", (-3.55, y + 0.04, 3.35), (0.055, 0.18, 0.35), accent, 0.02)
    cube(f"LightR_{y}", (3.55, y + 0.04, 3.35), (0.055, 0.18, 0.35), accent, 0.02)

for x, y, z, sx, sy, sz in (
    (-3.25, 4.2, 0.55, 0.65, 0.70, 0.55),
    (-2.9, 5.0, 0.35, 0.45, 0.50, 0.35),
    (3.1, 6.3, 0.45, 0.60, 0.55, 0.45),
):
    cube("Crate", (x, y, z), (sx, sy, sz), crate_mat, 0.08)

# Agent rig.
arm_data = bpy.data.armatures.new("AgentRigData")
arm = bpy.data.objects.new("AgentRig", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones

add_bone(eb, "root", (0, 0, 0.85), (0, 0, 1.45))
add_bone(eb, "spine", (0, 0, 1.45), (0, 0, 2.45), "root")
add_bone(eb, "head", (0, 0, 2.45), (0, 0, 3.0), "spine")
add_bone(eb, "upper_arm.L", (0.05, 0, 2.30), (0.78, 0, 2.18), "spine")
add_bone(eb, "forearm.L", (0.78, 0, 2.18), (1.42, 0, 2.02), "upper_arm.L")
add_bone(eb, "hand.L", (1.42, 0, 2.02), (1.70, 0, 1.98), "forearm.L")
add_bone(eb, "upper_arm.R", (-0.05, 0, 2.30), (-0.78, 0, 2.18), "spine")
add_bone(eb, "forearm.R", (-0.78, 0, 2.18), (-1.42, 0, 2.02), "upper_arm.R")
add_bone(eb, "hand.R", (-1.42, 0, 2.02), (-1.70, 0, 1.98), "forearm.R")
add_bone(eb, "thigh.L", (0.25, 0, 1.10), (0.28, 0, 0.40), "root")
add_bone(eb, "shin.L", (0.28, 0, 0.40), (0.28, 0, -0.35), "thigh.L")
add_bone(eb, "thigh.R", (-0.25, 0, 1.10), (-0.28, 0, 0.40), "root")
add_bone(eb, "shin.R", (-0.28, 0, 0.40), (-0.28, 0, -0.35), "thigh.R")

bpy.ops.object.mode_set(mode="POSE")
for pb in arm.pose.bones:
    pb.rotation_mode = "XYZ"

# Static aim posture on right arm; NLA drives the rest.
arm.pose.bones["upper_arm.R"].rotation_euler = (0.15, -0.35, -0.55)
arm.pose.bones["forearm.R"].rotation_euler = (0.0, 0.0, -0.95)
arm.pose.bones["hand.R"].rotation_euler = (0.0, 0.0, 0.10)

bpy.ops.object.mode_set(mode="OBJECT")

# Visible body.
torso = cube("Torso", (0, 0, 1.85), (0.48, 0.28, 0.70), armor, 0.08)
bone_parent_keep_world(torso, arm, "spine")
chest = cube("ChestPlate", (0, -0.27, 2.05), (0.43, 0.07, 0.35), armor2, 0.05)
bone_parent_keep_world(chest, arm, "spine")
helmet = sphere("Helmet", (0, 0, 2.76), 0.40, armor2)
bone_parent_keep_world(helmet, arm, "head")
visor_obj = cube("Visor", (0, -0.34, 2.80), (0.27, 0.055, 0.09), visor, 0.03)
bone_parent_keep_world(visor_obj, arm, "head")
hips = cube("Hips", (0, 0, 1.17), (0.42, 0.25, 0.22), armor, 0.06)
bone_parent_keep_world(hips, arm, "root")

for side, sign in (("L", 1.0), ("R", -1.0)):
    upper = cube(f"UpperArm.{side}", (0.42 * sign, 0, 2.22), (0.33, 0.13, 0.13), armor, 0.05)
    bone_parent_keep_world(upper, arm, f"upper_arm.{side}")
    lower = cube(f"Forearm.{side}", (1.08 * sign, 0, 2.08), (0.28, 0.11, 0.11), armor2, 0.04)
    bone_parent_keep_world(lower, arm, f"forearm.{side}")
    hand = sphere(f"Hand.{side}", (1.58 * sign, 0, 2.00), 0.13, armor)
    bone_parent_keep_world(hand, arm, f"hand.{side}")
    thigh = cube(f"Thigh.{side}", (0.26 * sign, 0, 0.78), (0.16, 0.19, 0.35), armor, 0.05)
    bone_parent_keep_world(thigh, arm, f"thigh.{side}")
    shin = cube(f"Shin.{side}", (0.28 * sign, 0, 0.03), (0.15, 0.17, 0.37), armor2, 0.04)
    bone_parent_keep_world(shin, arm, f"shin.{side}")

# Weapon parented to right hand. Left arm follows a foregrip target using IK.
gun = cube("PulseCarbine", (-1.87, -0.38, 1.98), (0.15, 0.55, 0.12), weapon_mat, 0.035)
gun.rotation_euler = (math.radians(90), 0, 0)
bone_parent_keep_world(gun, arm, "hand.R")
barrel = cube("CarbineBarrel", (-1.87, -0.95, 1.98), (0.07, 0.28, 0.07), weapon_mat, 0.02)
barrel.rotation_euler = (math.radians(90), 0, 0)
barrel.parent = gun

bpy.ops.object.empty_add(type="SPHERE", radius=0.08, location=(-1.35, -0.35, 2.02))
foregrip = bpy.context.object
foregrip.name = "LeftHand_Foregrip"
foregrip.parent = gun

left_forearm = arm.pose.bones["forearm.L"]
ik = left_forearm.constraints.new("IK")
ik.name = "LeftHand_Weapon_IK"
ik.target = foregrip
ik.chain_count = 2

# Muzzle flash and tracer.
flash = sphere("MuzzleFlash", (-1.87, -1.32, 1.98), 0.16, muzzle_mat)
flash.parent = gun
for frame, scale in ((1, 0.001), (55, 0.001), (56, 1.0), (58, 0.001), (84, 0.001)):
    flash.scale = (scale, scale, scale)
    flash.keyframe_insert(data_path="scale", frame=frame)

tracer = cube("Tracer", (-1.87, -1.75, 1.98), (0.035, 0.40, 0.035), muzzle_mat, 0.01)
tracer.scale = (0.001, 0.001, 0.001)
tracer.keyframe_insert(data_path="scale", frame=55)
tracer.location = (-1.87, -1.75, 1.98)
tracer.scale = (1, 1, 1)
tracer.keyframe_insert(data_path="scale", frame=56)
tracer.keyframe_insert(data_path="location", frame=56)
tracer.location = (-1.87, -6.8, 1.98)
tracer.keyframe_insert(data_path="location", frame=60)
tracer.scale = (0.001, 0.001, 0.001)
tracer.keyframe_insert(data_path="scale", frame=61)

# One NLA action drives traversal + gait + body sway.
action = bpy.data.actions.new("Agent_Run_Aim")
fcurve(action, "location", 1, [(1, -6.2), (32, -1.8), (56, 1.1), (84, 4.3)], "LINEAR")
fcurve(action, "location", 2, [(1, 0.0), (18, 0.09), (36, 0.0), (54, 0.08), (72, 0.0), (84, 0.03)])
fcurve(action, 'pose.bones["spine"].rotation_euler', 2, [(1,-0.05),(18,0.06),(36,-0.05),(54,0.04),(72,-0.03),(84,0.0)])

walk_keys = [(1,0.65),(8,-0.65),(15,0.65),(22,-0.65),(29,0.65),(36,-0.65),(43,0.55),(50,-0.45),(57,0.28),(64,-0.22),(71,0.14),(78,-0.08),(84,0.0)]
fcurve(action, 'pose.bones["thigh.L"].rotation_euler', 0, walk_keys)
fcurve(action, 'pose.bones["thigh.R"].rotation_euler', 0, [(f,-v) for f,v in walk_keys])
fcurve(action, 'pose.bones["shin.L"].rotation_euler', 0, [(f,max(0.0,-v)*0.85) for f,v in walk_keys])
fcurve(action, 'pose.bones["shin.R"].rotation_euler', 0, [(f,max(0.0,v)*0.85) for f,v in walk_keys])
fcurve(action, 'pose.bones["upper_arm.L"].rotation_euler', 2, [(1,0.20),(24,-0.10),(42,-0.35),(56,-0.42),(84,-0.35)])

arm.animation_data_create()
track = arm.animation_data.nla_tracks.new()
track.name = "Base_Run_Aim"
strip = track.strips.new("RunAim", 1, action)
strip.frame_end = END_FRAME
arm.animation_data.action = None

# Camera target follows the agent through a Child Of relationship.
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 1.58))
focus = bpy.context.object
focus.name = "CameraFocus"
focus.parent = arm

bpy.ops.object.camera_add(location=(3.90, -8.8, 3.4))
camera = bpy.context.object
camera.name = "Camera"
scene.camera = camera
camera.data.lens = 22
track_to = camera.constraints.new("TRACK_TO")
track_to.target = focus
track_to.track_axis = "TRACK_NEGATIVE_Z"
track_to.up_axis = "UP_Y"

for frame, loc, lens in (
    (1, (3.90, -8.8, 3.4), 22),
    (32, (3.85, -3.5, 3.0), 23),
    (56, (3.80, 0.0, 2.7), 24),
    (84, (3.72, 3.6, 2.5), 26),
):
    camera.location = loc
    camera.data.lens = lens
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.data.keyframe_insert(data_path="lens", frame=frame)

# Subtle opponent target at end of corridor.
target = cube("TargetDrone", (-1.85, 6.9, 1.8), (0.42, 0.24, 0.28), panel, 0.08)
sphere("TargetCore", (-1.85, 6.62, 1.8), 0.15, muzzle_mat)

# Metadata proving the intended animation primitives exist.
scene["agent_demo"] = {
    "fps": FPS,
    "end_frame": END_FRAME,
    "ik_constraint": ik.name,
    "nla_track": track.name,
    "nla_strip": strip.name,
    "weapon": gun.name,
}

bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
print(f"AGENT_ACTION_DEMO_SCENE blend={output_blend} frames={END_FRAME} fps={FPS} ik={ik.name} nla={track.name}")
