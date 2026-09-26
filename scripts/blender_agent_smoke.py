import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def argv_after_dash():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def add_box(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def add_uv_sphere(name, location, radius):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def bone_parent_keep_world(obj, armature, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


args = argv_after_dash()
if len(args) < 2:
    raise SystemExit("usage: blender_agent_smoke.py -- OUTPUT_BLEND OUTPUT_PNG")

output_blend = Path(args[0]).resolve()
output_png = Path(args[1]).resolve()
output_blend.parent.mkdir(parents=True, exist_ok=True)
output_png.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.world = bpy.data.worlds.new("AgentWorld")
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output_png)
scene.render.film_transparent = False
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.image_settings.color_mode = "RGBA"
scene.render.resolution_percentage = 100
scene.world.color = (0.025, 0.035, 0.055)
scene.frame_start = 1
scene.frame_end = 48
scene.render.fps = 24

# Ground.
bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0))
ground = bpy.context.object
ground.name = "Ground"

# Camera.
bpy.ops.object.camera_add(location=(7.2, -9.5, 5.2))
camera = bpy.context.object
camera.name = "Camera"
scene.camera = camera

def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

point_at(camera, (0.2, 0, 1.7))

# Lights.
bpy.ops.object.light_add(type="AREA", location=(2.5, -3.5, 6.5))
key = bpy.context.object
key.data.energy = 900
key.data.shape = "DISK"
key.data.size = 5.0
point_at(key, (0, 0, 1.5))

bpy.ops.object.light_add(type="AREA", location=(-4.0, 2.0, 3.0))
fill = bpy.context.object
fill.data.energy = 500
fill.data.size = 4.0
point_at(fill, (0, 0, 1.4))

# Minimal humanoid armature for deterministic agent-side animation tests.
arm_data = bpy.data.armatures.new("AgentRigData")
arm = bpy.data.objects.new("AgentRig", arm_data)
bpy.context.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")

bones = {}
def make_bone(name, head, tail, parent=None):
    bone = arm_data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    if parent:
        bone.parent = bones[parent]
    bones[name] = bone

make_bone("root", (0, 0, 0.9), (0, 0, 1.8))
make_bone("spine", (0, 0, 1.8), (0, 0, 2.7), "root")
make_bone("upper_arm.L", (0, 0, 2.45), (0.9, 0, 2.35), "spine")
make_bone("forearm.L", (0.9, 0, 2.35), (1.7, 0, 2.15), "upper_arm.L")
make_bone("hand.L", (1.7, 0, 2.15), (2.0, 0, 2.10), "forearm.L")
make_bone("upper_arm.R", (0, 0, 2.45), (-0.9, 0, 2.35), "spine")
make_bone("forearm.R", (-0.9, 0, 2.35), (-1.7, 0, 2.15), "upper_arm.R")
make_bone("hand.R", (-1.7, 0, 2.15), (-2.0, 0, 2.10), "forearm.R")
bpy.ops.object.mode_set(mode="POSE")

for pose_bone in arm.pose.bones:
    pose_bone.rotation_mode = "XYZ"

# IK target drives the left arm; this is the same class of primitive used for
# keeping hands attached to weapons/props in production.
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.empty_add(type="SPHERE", radius=0.14, location=(1.85, -0.25, 2.1))
ik_target = bpy.context.object
ik_target.name = "IK_Target_LeftHand"

left_forearm = arm.pose.bones["forearm.L"]
ik = left_forearm.constraints.new("IK")
ik.name = "Agent_LeftHand_IK"
ik.target = ik_target
ik.chain_count = 2

for frame, location in (
    (1, (1.8, -0.25, 2.1)),
    (24, (1.25, -0.65, 2.75)),
    (48, (1.9, 0.15, 2.25)),
):
    ik_target.location = location
    ik_target.keyframe_insert(data_path="location", frame=frame)

# NLA-controlled body motion.
arm.animation_data_create()
sway = bpy.data.actions.new("Agent_Body_Sway")
fcurve = sway.fcurves.new(data_path='pose.bones["root"].rotation_euler', index=2)
for frame, value in ((1, -0.06), (12, 0.07), (24, -0.03), (36, 0.06), (48, -0.06)):
    fcurve.keyframe_points.insert(frame, value)
track = arm.animation_data.nla_tracks.new()
track.name = "Agent_BaseMotion"
strip = track.strips.new("BodySway", 1, sway)
strip.frame_end = 48
arm.animation_data.action = None

# Simple visible proxy pieces parented to bones.
torso = add_box("Torso", (0, 0, 2.0), (0.48, 0.30, 0.70))
bone_parent_keep_world(torso, arm, "spine")
head = add_uv_sphere("Head", (0, 0, 3.02), 0.36)
bone_parent_keep_world(head, arm, "spine")
hips = add_box("Hips", (0, 0, 1.15), (0.42, 0.28, 0.25))
bone_parent_keep_world(hips, arm, "root")

for side, sign in (("L", 1.0), ("R", -1.0)):
    upper = add_box(f"UpperArm.{side}", (0.48 * sign, 0, 2.42), (0.43, 0.13, 0.13))
    bone_parent_keep_world(upper, arm, f"upper_arm.{side}")
    lower = add_box(f"Forearm.{side}", (1.28 * sign, 0, 2.25), (0.36, 0.11, 0.11))
    bone_parent_keep_world(lower, arm, f"forearm.{side}")
    hand = add_uv_sphere(f"Hand.{side}", (1.88 * sign, 0, 2.12), 0.15)
    bone_parent_keep_world(hand, arm, f"hand.{side}")

# Legs are static proxy geometry for the smoke frame; locomotion assets can
# replace these once free animation files are imported.
add_box("LeftLeg", (0.25, 0, 0.65), (0.18, 0.22, 0.65))
add_box("RightLeg", (-0.25, 0, 0.65), (0.18, 0.22, 0.65))

# Verify bundled Rigify availability without requiring it for this smoke rig.
rigify_available = False
rigify_enabled = False
try:
    import importlib.util
    rigify_available = importlib.util.find_spec("rigify") is not None
    if rigify_available:
        bpy.ops.preferences.addon_enable(module="rigify")
        rigify_enabled = "rigify" in bpy.context.preferences.addons
except Exception:
    rigify_enabled = False

scene.frame_set(24)
bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))
bpy.ops.render.render(write_still=True)

result = {
    "blend": str(output_blend),
    "preview": str(output_png),
    "frame": scene.frame_current,
    "ik_constraint": ik.name,
    "nla_tracks": len(arm.animation_data.nla_tracks),
    "nla_strips": sum(len(track.strips) for track in arm.animation_data.nla_tracks),
    "rigify_available": rigify_available,
    "rigify_enabled": rigify_enabled,
    "objects": len(bpy.data.objects),
}
print("HERMES_BLENDER_SMOKE=" + json.dumps(result, sort_keys=True))
