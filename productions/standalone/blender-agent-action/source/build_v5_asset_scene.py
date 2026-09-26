#!/usr/bin/env python3
"""Build the asset-backed V5 action comparison scene.

V5 intentionally keeps the same 4 s / 24 fps story beats as V4 while replacing
the scratch proxy character and box corridor with CC0 Quaternius production
assets. Third-party payloads are local-only; provenance is stored beside this
source package.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

FPS = 24
END_FRAME = 96
WIDTH = 512
HEIGHT = 288

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "productions/standalone/blender-agent-action/scene/agent-action-v5.blend"
SPACE = ROOT / "external-assets/quaternius/ultimate_space_kit"
MEGA = ROOT / "external-assets/quaternius/modular_scifi_megakitstandard/Modular SciFi MegaKit[Standard]/glTF"


def clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def imported_root(path: Path, name: str, *, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before]
    new_set = set(new)
    top = [o for o in new if o.parent not in new_set]
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    for o in top:
        world = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = world
    root.location = loc
    root.rotation_euler = rot
    root.scale = (scale, scale, scale)
    return root, new


def emissive_material(name: str, color, strength=8.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Emission Color"].default_value = (*color, 1)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def pulse(obj, keys):
    for frame, value in keys:
        obj.scale = (value, value, value)
        obj.keyframe_insert(data_path="scale", frame=frame)


def add_sphere(name, radius, loc, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def add_area(name, loc, energy, color, size=3.0):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.color = color
    light.data.shape = "RECTANGLE"
    light.data.size = size
    light.data.size_y = size * 0.55
    light.rotation_euler = (0, 0, 0)
    return light


def add_point(name, loc, energy, color, radius=1.5):
    bpy.ops.object.light_add(type="POINT", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.color = color
    light.data.shadow_soft_size = radius
    return light


def look_at(obj, target_obj):
    c = obj.constraints.new("TRACK_TO")
    c.target = target_obj
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return c


def empty(name, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.2
    if parent:
        obj.parent = parent
    return obj


def set_linear(obj, data_path="location"):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"


def action_by_contains(needle: str):
    matches = [a for a in bpy.data.actions if needle in a.name]
    if not matches:
        raise RuntimeError(f"missing action containing {needle!r}")
    return matches[0]


def add_nla_strip(track, name, action, start: float, end: float):
    strip = track.strips.new(name, start, action)
    a0, a1 = action.frame_range
    strip.action_frame_start = a0
    strip.action_frame_end = a1
    natural = max(1.0, a1 - a0)
    target = max(1.0, end - start)
    if "Run_Gun" in name and "Shoot" not in name:
        strip.repeat = target / natural
    else:
        strip.scale = target / natural
    strip.blend_type = "REPLACE"
    strip.extrapolation = "NOTHING"
    return strip


def flatten_for_workbench(hero_objs, enemy_objs):
    """Keep imported geometry/rigs but remove texture payload from the fast proof."""
    for material in list(bpy.data.materials):
        if material.use_nodes and material.node_tree:
            bsdf = material.node_tree.nodes.get("Principled BSDF")
            if bsdf and "Base Color" in bsdf.inputs:
                base = bsdf.inputs["Base Color"].default_value
                material.diffuse_color = tuple(base)
        material.use_nodes = False

        n = material.name.lower()
        if "light" in n or "screen" in n:
            material.diffuse_color = (0.05, 0.58, 0.95, 1.0)
        elif "black" in n:
            material.diffuse_color = (0.025, 0.035, 0.055, 1.0)
        elif "trim_03" in n or "padded" in n:
            material.diffuse_color = (0.07, 0.10, 0.15, 1.0)
        elif "trim_02" in n:
            material.diffuse_color = (0.17, 0.23, 0.31, 1.0)
        elif "trim_01" in n:
            material.diffuse_color = (0.30, 0.36, 0.44, 1.0)
        elif "decal" in n:
            material.diffuse_color = (0.58, 0.72, 0.86, 1.0)

    for obj in hero_objs:
        if obj.type != "MESH":
            continue
        for i, material in enumerate(list(obj.data.materials)):
            m = material.copy()
            m.use_nodes = False
            if "pistol" in obj.name.lower():
                m.diffuse_color = (0.055, 0.075, 0.105, 1.0)
            elif "icosphere" in obj.name.lower():
                m.diffuse_color = (0.03, 0.60, 0.90, 1.0)
            else:
                m.diffuse_color = (0.19, 0.30, 0.43, 1.0)
            obj.data.materials[i] = m

    for obj in enemy_objs:
        if obj.type != "MESH":
            continue
        for i, material in enumerate(list(obj.data.materials)):
            m = material.copy()
            m.use_nodes = False
            if "icosphere" in obj.name.lower():
                m.diffuse_color = (1.0, 0.30, 0.04, 1.0)
            else:
                m.diffuse_color = (0.44, 0.10, 0.075, 1.0)
            obj.data.materials[i] = m

    for image_data in list(bpy.data.images):
        bpy.data.images.remove(image_data)


clear_scene()
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = END_FRAME
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.display.shading.light = "STUDIO"
scene.display.shading.studio_light = "studio.sl"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.curvature_ridge_factor = 1.6
scene.display.shading.curvature_valley_factor = 1.1
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.008, 0.015, 0.03)
scene.view_settings.look = "AgX - Medium High Contrast"

scene.world = bpy.data.worlds.new("V5World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.006, 0.012, 0.025, 1.0)
bg.inputs["Strength"].default_value = 0.12

# --- Modular environment -------------------------------------------------
# Four 4 m bays make a compact corridor with the same forward action axis as V4.
for y in (-6.0, -2.0, 2.0, 6.0):
    imported_root(MEGA / "Platforms/Platform_Metal.gltf", f"Floor_{y:+.0f}", loc=(0, y, 0.0))
    imported_root(MEGA / "Walls/WallAstra_Straight_Flat.gltf", f"WallL_{y:+.0f}", loc=(-0.25, y, 0.0))
    imported_root(
        MEGA / "Walls/WallAstra_Straight_Flat.gltf",
        f"WallR_{y:+.0f}",
        loc=(0.25, y, 0.0),
        rot=(0, 0, math.pi),
    )

# Far doorway and structural dressing.
imported_root(MEGA / "Platforms/Door_Frame_A.gltf", "FarDoorFrame", loc=(0, 7.45, 0), scale=0.62)
left_door, _ = imported_root(MEGA / "Platforms/Door_DarkMetal.gltf", "FarDoorL", loc=(-0.05, 7.45, 0), scale=0.62)
right_door, _ = imported_root(MEGA / "Platforms/Door_DarkMetal.gltf", "FarDoorR", loc=(0.05, 7.45, 0), rot=(0, 0, math.pi), scale=0.62)

for y in (-5.8, 0.2, 5.8):
    imported_root(MEGA / "Columns/Column_Pipes.gltf", f"PipesL_{y:+.0f}", loc=(-1.65, y, 0), scale=0.58)
for loc in [(-1.35, -0.2, 0.5), (1.25, 3.4, 0.5), (-1.30, 4.5, 0.5)]:
    imported_root(MEGA / "Props/Prop_Crate3.gltf", "Crate", loc=loc, scale=0.75)
imported_root(MEGA / "Props/Prop_Computer.gltf", "Terminal", loc=(1.55, 1.8, 0), rot=(0, 0, math.pi / 2), scale=0.92)

# Ceiling rhythm: modelled light housings plus real area lights.
for i, y in enumerate((-5.5, -2.5, 0.5, 3.5, 6.4)):
    imported_root(MEGA / "Props/Prop_Light_Wide.gltf", f"Fixture_{i}", loc=(0, y, 2.88), rot=(0, math.pi / 2, 0), scale=1.15)
    area = add_area(f"CeilingLight_{i}", (0, y, 2.72), 360.0, (0.25, 0.56, 1.0), 2.2)
    area.rotation_euler = (0, 0, 0)

# Warm depth light behind the target; cool side lights give armor separation.
add_point("BackRed", (0, 6.4, 2.05), 420.0, (1.0, 0.08, 0.025), 1.1)
add_point("SideBlue", (-1.75, -0.7, 1.55), 300.0, (0.08, 0.35, 1.0), 1.4)

# --- Hero character ------------------------------------------------------
hero, hero_objs = imported_root(SPACE / "Astronaut.glb", "HeroRoot", loc=(0.0, -6.55, 0.55), scale=0.55)
armatures = [o for o in hero_objs if o.type == "ARMATURE"]
if len(armatures) != 1:
    raise RuntimeError(f"expected one hero armature, got {len(armatures)}")
hero_arm = armatures[0]
hero_arm.name = "HeroArmature"
for obj in list(hero_objs):
    if obj.type == "MESH" and "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)
        hero_objs.remove(obj)

# Action strips use the model's own authored clips. Root travel is separate so
# the run cycle stays reusable and predictable.
hero_arm.animation_data_create()
hero_arm.animation_data.action = None
track = hero_arm.animation_data.nla_tracks.new()
track.name = "HeroAction"
add_nla_strip(track, "Run_Gun", action_by_contains("Run_Gun_CharacterArmature"), 1, 48)
add_nla_strip(track, "Idle_Gun_Prepare", action_by_contains("Idle_Gun_CharacterArmature"), 48, 61)
add_nla_strip(track, "Run_Gun_Shoot", action_by_contains("Run_Gun_Shoot_CharacterArmature"), 61, 73)
add_nla_strip(track, "Idle_Gun_Hold", action_by_contains("Idle_Gun_CharacterArmature"), 73, 96)

for frame, loc in (
    (1, (0.10, -6.55, 0.55)),
    (14, (-0.12, -4.95, 0.55)),
    (28, (0.08, -3.10, 0.55)),
    (42, (-0.04, -1.35, 0.55)),
    (52, (0.00, -0.45, 0.55)),
    (60, (0.00, -0.10, 0.55)),
    (96, (0.00, -0.10, 0.55)),
):
    hero.location = loc
    hero.keyframe_insert(data_path="location", frame=frame)
set_linear(hero)

hero_focus = empty("HeroFocus", (0, 0.2, 1.35), parent=hero)
hero_head_focus = empty("HeroHeadFocus", (0, 0.15, 1.65), parent=hero)

# --- Enemy ---------------------------------------------------------------
enemy, enemy_objs = imported_root(SPACE / "Enemy Flying.glb", "EnemyRoot", loc=(0.20, 5.75, 1.65), rot=(0, 0, math.pi), scale=0.72)
for obj in list(enemy_objs):
    if obj.type == "MESH" and "icosphere" in obj.name.lower():
        bpy.data.objects.remove(obj, do_unlink=True)
        enemy_objs.remove(obj)
enemy_arms = [o for o in enemy_objs if o.type == "ARMATURE"]
if enemy_arms:
    enemy_arm = enemy_arms[0]
    enemy_arm.name = "EnemyArmature"
    enemy_arm.animation_data_create()
    enemy_arm.animation_data.action = None
    etrack = enemy_arm.animation_data.nla_tracks.new()
    etrack.name = "EnemyAction"
    idle = action_by_contains("Flying_Idle_CharacterArmature")
    hit = action_by_contains("HitReact_CharacterArmature")
    # Ensure we choose enemy actions if names collide with hero.
    enemy_actions = [a for a in bpy.data.actions if a.name.startswith("CharacterArmature") and ("Flying_Idle" in a.name or "HitReact" in a.name)]
    idle = next((a for a in enemy_actions if "Flying_Idle" in a.name), idle)
    hit = next((a for a in enemy_actions if "HitReact" in a.name), hit)
    add_nla_strip(etrack, "Flying_Idle", idle, 1, 68)
    add_nla_strip(etrack, "HitReact", hit, 68, 79)

for frame, loc, rot in (
    (1, (0.20, 5.75, 1.65), (0, 0, math.pi)),
    (67, (0.20, 5.75, 1.65), (0, 0, math.pi)),
    (76, (0.60, 5.92, 1.35), (0.25, -0.18, 3.35)),
    (90, (0.92, 6.08, 0.42), (0.90, -0.45, 3.85)),
    (96, (0.92, 6.08, 0.36), (1.05, -0.45, 3.95)),
):
    enemy.location = loc
    enemy.rotation_euler = rot
    enemy.keyframe_insert(data_path="location", frame=frame)
    enemy.keyframe_insert(data_path="rotation_euler", frame=frame)

enemy_focus = empty("EnemyFocus", (0.20, 5.75, 1.50))
for frame, loc in (
    (72, (0.20, 5.75, 1.50)),
    (84, (0.58, 5.98, 0.92)),
    (96, (0.90, 6.08, 0.52)),
):
    enemy_focus.location = loc
    enemy_focus.keyframe_insert(data_path="location", frame=frame)

# --- Effects -------------------------------------------------------------
flash_mat = emissive_material("PulseEmission", (1.0, 0.18, 0.025), 18.0)
impact_mat = emissive_material("ImpactEmission", (0.14, 0.68, 1.0), 22.0)

# Bind the muzzle effect to the actual imported pistol geometry instead of a
# guessed hero-space coordinate. The pistol is rigidly parented to the animated
# hand bone, so its evaluated world transform gives us the barrel tip at each
# shot frame. The long local-Z end of this mesh points downrange.
pistol = next(
    (o for o in hero_objs if o.type == "MESH" and "pistol" in o.name.lower()),
    None,
)
if pistol is None:
    raise RuntimeError("Astronaut asset is missing the expected pistol mesh")


def pistol_tip_world(frame: int) -> Vector:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    corners = [Vector(c) for c in pistol.bound_box]
    center_x = sum(v.x for v in corners) / len(corners)
    center_y = sum(v.y for v in corners) / len(corners)
    tip_local = Vector((center_x, center_y, min(v.z for v in corners)))
    center_local = sum(corners, Vector()) / len(corners)
    tip_world = pistol.matrix_world @ tip_local
    center_world = pistol.matrix_world @ center_local
    direction = (tip_world - center_world).normalized()
    return tip_world + direction * 0.10


flash = add_sphere("MuzzleFlash", 0.16, (0, 0, 0), flash_mat)
pulse(flash, [(1, 0.001), (61, 0.001), (62, 1.0), (63, 0.001), (67, 0.001), (68, 0.90), (69, 0.001), (96, 0.001)])
for frame in (61, 62, 63, 67, 68, 69):
    flash.location = pistol_tip_world(frame)
    flash.keyframe_insert(data_path="location", frame=frame)

muzzle_light = add_point("MuzzleLight", (0, 0, 0), 0, (1.0, 0.15, 0.02), 0.28)
for frame in (61, 62, 63, 67, 68, 69):
    muzzle_light.location = pistol_tip_world(frame)
    muzzle_light.keyframe_insert(data_path="location", frame=frame)
for frame, power in ((1, 0), (61, 0), (62, 720), (63, 0), (67, 0), (68, 650), (69, 0), (96, 0)):
    muzzle_light.data.energy = power
    muzzle_light.data.keyframe_insert(data_path="energy", frame=frame)

impact = add_sphere("ImpactBurst", 0.35, (0.20, 5.75, 1.72), impact_mat)
pulse(impact, [(1, 0.001), (67, 0.001), (68, 0.25), (70, 1.4), (74, 0.001), (96, 0.001)])
impact_light = add_point("ImpactLight", (0.20, 5.75, 1.72), 0, (0.1, 0.5, 1.0), 0.55)
for frame, power in ((1, 0), (67, 0), (68, 300), (70, 1100), (73, 150), (75, 0), (96, 0)):
    impact_light.data.energy = power
    impact_light.data.keyframe_insert(data_path="energy", frame=frame)

# --- Cameras -------------------------------------------------------------
def camera(name, loc, lens, target):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = lens
    look_at(cam, target)
    return cam

cam_run = camera("Cam_Run", (1.55, -8.00, 2.35), 28, hero_focus)
for f, loc in ((1, (1.55, -8.00, 2.35)), (22, (1.50, -6.25, 2.25)), (42, (1.45, -4.15, 2.08))):
    cam_run.location = loc
    cam_run.keyframe_insert(data_path="location", frame=f)

cam_fire = camera("Cam_Fire", (1.60, -2.45, 2.02), 34, hero_head_focus)
for f, loc in ((43, (1.60, -2.45, 2.02)), (58, (1.55, -2.00, 1.98)), (71, (1.45, -1.55, 1.92))):
    cam_fire.location = loc
    cam_fire.keyframe_insert(data_path="location", frame=f)

cam_impact = camera("Cam_Impact", (0.75, 1.40, 2.20), 28, enemy_focus)
for f, loc in ((72, (0.75, 1.40, 2.20)), (84, (0.60, 1.75, 2.00)), (96, (0.45, 2.05, 1.82))):
    cam_impact.location = loc
    cam_impact.keyframe_insert(data_path="location", frame=f)

scene.camera = cam_run
for name, frame, cam in (("RUN", 1, cam_run), ("FIRE", 43, cam_fire), ("IMPACT", 72, cam_impact)):
    marker = scene.timeline_markers.new(name, frame=frame)
    marker.camera = cam

# Workbench is the device-fast comparison renderer. Imported production geometry,
# native character animation, camera direction and effects remain unchanged.
scene.use_nodes = False

flatten_for_workbench(hero_objs, enemy_objs)

# glTF imports may create a hidden helper collection and can switch the scene
# renderer. Reassert the actual delivery settings after every import.
for collection in bpy.data.collections:
    collection.hide_render = False
    collection.hide_viewport = False
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.display.render_aa = "FXAA"

scene["v5_asset_scene"] = {
    "fps": FPS,
    "frames": END_FRAME,
    "comparison": "same 4-second action target as V4",
    "hero": "Quaternius Ultimate Space Kit Astronaut",
    "environment": "Quaternius Modular SciFi MegaKit Standard",
    "hero_actions": "Run_Gun -> Idle_Gun -> Run_Gun_Shoot -> Idle_Gun",
    "target": "Quaternius Ultimate Space Kit Enemy Flying",
}

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print(f"V5_SCENE_READY {OUT} objects={len(scene.objects)} actions={len(bpy.data.actions)} engine={scene.render.engine} res={scene.render.resolution_x}x{scene.render.resolution_y} aa={scene.display.render_aa}")