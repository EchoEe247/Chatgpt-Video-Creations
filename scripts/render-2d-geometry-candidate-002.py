#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.geometry import Camera2D, Point, SetGeometry
from src.animation_2d.layout import CharacterRigLayout, place_character, place_portal

W, H, FPS, DUR = 1280, 720, 24, 8.0
N = int(FPS * DUR)
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "2d_geometry_candidate_002.mp4"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except Exception:
        return ImageFont.load_default()


with open(ROOT / "candidates/2d-geometry-002/set.json") as handle:
    SET = SetGeometry.from_mapping(json.load(handle))

assert SET.canvas and SET.canvas.width == W and SET.canvas.height == H
RIG = CharacterRigLayout(foot_anchor_px=Point(110, 326))


def clamp01(value):
    return max(0.0, min(1.0, value))


def smooth(value):
    value = clamp01(value)
    return value * value * (3 - 2 * value)


def lerp(a, b, t):
    return a + (b - a) * t


def camera_at(t):
    if t < 2.2:
        u = smooth(t / 2.2); a = (0, 0, 1.0); b = (30, 25, 1.06)
    elif t < 4.6:
        u = smooth((t - 2.2) / 2.4); a = (30, 25, 1.06); b = (120, 100, 1.18)
    elif t < 6.2:
        u = smooth((t - 4.6) / 1.6); a = (120, 100, 1.18); b = (150, 125, 1.22)
    else:
        u = smooth((t - 6.2) / 1.8); a = (150, 125, 1.22); b = (0, 0, 1.0)
    return Camera2D(
        origin=Point(lerp(a[0], b[0], u), lerp(a[1], b[1], u)),
        scale=lerp(a[2], b[2], u),
    )


def proj(camera, x, y):
    point = camera.point_to_screen(Point(x, y))
    return point.x, point.y


def line_world(draw, camera, points, fill, width=1):
    draw.line([proj(camera, *point) for point in points], fill=fill, width=max(1, int(width * camera.scale)))


def rect_world(draw, camera, box, fill, outline=None, width=1):
    x0, y0 = proj(camera, box[0], box[1])
    x1, y1 = proj(camera, box[2], box[3])
    draw.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=max(1, int(width * camera.scale)))


def circle(draw, cx, cy, radius, fill=None, outline=None, width=1):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill, outline=outline, width=max(1, int(width)))


def make_card_sprite(title, lines, size):
    width, height = size
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=15, fill=(226, 222, 204, 255), outline=(17, 20, 25, 255), width=3)
    draw.text((18, 14), title, font=font(26, True), fill=(43, 47, 56, 255))
    y = 54
    for line in lines:
        draw.text((18, y), line, font=font(15), fill=(53, 56, 64, 255))
        y += 27
    return image


CARD_RULES = make_card_sprite(
    "LAB RULES",
    ["1. One geometry source", "2. Feet use contact anchors", "3. Effects inherit sources"],
    (283, 154),
)
CARD_CHECK = make_card_sprite(
    "CANDIDATE CHECK",
    ["✓ shared floor anchors", "✓ shared portal center", "✓ shared camera transform"],
    (295, 154),
)


def paste_world_sprite(canvas, camera, sprite, world_box):
    x0, y0 = proj(camera, world_box[0], world_box[1])
    x1, y1 = proj(camera, world_box[2], world_box[3])
    sx0, sx1 = sorted((x0, x1)); sy0, sy1 = sorted((y0, y1))
    target_w = max(1, int(round(sx1 - sx0)))
    target_h = max(1, int(round(sy1 - sy0)))
    resized = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
    canvas.alpha_composite(resized, (int(round(sx0)), int(round(sy0))))


def make_character(kind, t):
    image = Image.new("RGBA", (220, 340), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if kind == "vex":
        skin = (235, 201, 165, 255); coat = (33, 106, 118, 255); shirt = (187, 68, 126, 255)
        hair = (147, 76, 187, 255); pants = (70, 66, 82, 255); phase = 0.0
    else:
        skin = (241, 171, 107, 255); coat = (177, 65, 48, 255); shirt = (213, 202, 172, 255)
        hair = (92, 54, 36, 255); pants = (47, 79, 111, 255); phase = 0.7

    draw.polygon([(78, 233), (104, 233), (101, 309), (73, 309)], fill=pants, outline=(20, 22, 28, 255))
    draw.polygon([(116, 233), (142, 233), (147, 309), (119, 309)], fill=pants, outline=(20, 22, 28, 255))
    draw.rounded_rectangle((62, 305, 105, 326), radius=7, fill=(237, 239, 237, 255), outline=(18, 20, 23, 255), width=2)
    draw.rounded_rectangle((116, 305, 159, 326), radius=7, fill=(237, 239, 237, 255), outline=(18, 20, 23, 255), width=2)
    draw.rounded_rectangle((55, 150, 165, 240), radius=22, fill=coat, outline=(23, 23, 29, 255), width=3)
    draw.rounded_rectangle((87, 160, 133, 226), radius=7, fill=shirt, outline=(25, 25, 30, 255), width=2)

    swing = math.sin(t * 2.5 + phase) * 8
    if kind == "vex":
        swing += 6 * math.sin(t * 1.2)
    for side in (-1, 1):
        shoulder = (58 if side < 0 else 162, 169)
        ex = shoulder[0] + side * (24 + swing * side)
        ey = 213 + abs(swing) * 0.4
        hx = ex + side * 17; hy = 244
        draw.line([shoulder, (ex, ey), (hx, hy)], fill=coat, width=17, joint="curve")
        circle(draw, hx, hy, 7, fill=skin, outline=(25, 25, 30, 255), width=2)

    bob = math.sin(t * 3 + phase) * 2.5
    head_y = 105 + bob
    if kind == "vex":
        hair_points = [
            (56, 112 + bob), (63, 92 + bob), (48, 70 + bob), (72, 64 + bob), (58, 42 + bob),
            (85, 47 + bob), (83, 18 + bob), (106, 34 + bob), (116, 4 + bob), (132, 30 + bob),
            (150, 8 + bob), (152, 38 + bob), (176, 26 + bob), (169, 56 + bob), (192, 58 + bob),
            (175, 79 + bob), (190, 100 + bob), (165, 96 + bob), (155, 116 + bob), (130, 128 + bob),
            (92, 126 + bob),
        ]
        draw.polygon(hair_points, fill=hair, outline=(25, 25, 30, 255))
        circle(draw, 110, head_y, 54, fill=skin, outline=(25, 25, 30, 255), width=3)
    else:
        circle(draw, 110, head_y, 54, fill=skin, outline=(25, 25, 30, 255), width=3)
        draw.pieslice((48, 39 + bob, 172, 148 + bob), 180, 360, fill=hair, outline=(25, 25, 30, 255), width=2)

    eye_y = head_y - 5
    for ex in (85, 135):
        circle(draw, ex, eye_y, 14, fill=(248, 248, 242, 255), outline=(24, 24, 30, 255), width=2)
        gaze = 4 * math.sin(t * 1.1 + phase)
        circle(draw, ex + gaze, eye_y, 4.5, fill=(20, 22, 28, 255))
    if (t + phase) % 3.4 < 0.10:
        for ex in (85, 135):
            draw.line((ex - 12, eye_y, ex + 12, eye_y), fill=(20, 22, 28, 255), width=3)

    talking = int(t * 3 + phase * 4) % 5 in (1, 2)
    if talking:
        draw.ellipse((94, head_y + 24, 126, head_y + 41), fill=(61, 28, 31, 255), outline=(20, 20, 25, 255), width=2)
    else:
        draw.line((94, head_y + 30, 126, head_y + 30), fill=(30, 30, 34, 255), width=3)
    return image


def draw_set(image, draw, camera):
    image.paste((20, 25, 36), (0, 0, W, H))
    for x in range(0, 1401, 120):
        line_world(draw, camera, [(x, 70), (x, 525)], (52, 60, 73), 1)
    line_world(draw, camera, [(0, 84), (1280, 84)], (38, 45, 58), 3)
    rect_world(draw, camera, (70, 326, 760, 350), (91, 61, 41))
    rect_world(draw, camera, (100, 350, 133, 525), (77, 82, 91))
    rect_world(draw, camera, (210, 292, 345, 332), (10, 17, 25), outline=(4, 7, 10), width=3)
    rect_world(draw, camera, (227, 304, 328, 321), (51, 205, 214))

    # Render each board as one rasterized world-space object. This keeps its text
    # locked to the panel during camera zoom/pan instead of re-laying glyphs every frame.
    paste_world_sprite(image, camera, CARD_RULES, (74, 128, 357, 282))
    paste_world_sprite(image, camera, CARD_CHECK, (423, 132, 718, 286))

    floor_screen = proj(camera, 0, SET.floor_y)[1]
    floor_top = proj(camera, 0, 520)[1]
    draw.rectangle((0, floor_top, W, H), fill=(83, 68, 55))
    for x in range(-200, 1500, 100):
        line_world(draw, camera, [(640, 520), (x, 720)], (112, 86, 65), 1)
    for y in range(555, 721, 45):
        line_world(draw, camera, [(0, y), (1280, y)], (104, 82, 64), 1)
    draw.line((0, floor_screen, W, floor_screen), fill=(245, 207, 66), width=max(1, int(2 * camera.scale)))


def draw_portal(draw, camera, t):
    placement = place_portal(set_geometry=SET, camera=camera)
    cx, cy = placement.frame_outer.center.x, placement.frame_outer.center.y
    outer, inner = placement.frame_outer.radius, placement.frame_inner.radius
    circle(draw, cx, cy, outer, fill=(21, 27, 36), outline=(6, 10, 15), width=max(2, int(8 * camera.scale)))
    circle(draw, cx, cy, outer * 0.88, fill=(73, 82, 96), outline=(105, 113, 126), width=max(2, int(6 * camera.scale)))
    for i in range(12):
        angle = 2 * math.pi * i / 12
        bolt_radius = outer * 0.93
        bx = cx + math.cos(angle) * bolt_radius; by = cy + math.sin(angle) * bolt_radius
        circle(draw, bx, by, max(4, 6 * camera.scale), fill=(112, 120, 132), outline=(10, 13, 18), width=1)
    circle(draw, cx, cy, inner, fill=(20, 50, 38), outline=(21, 168, 67), width=max(2, int(7 * camera.scale)))

    # Energy uses the exact inherited inner opening.
    energy = placement.energy
    assert energy.center == placement.frame_inner.center and energy.radius == placement.frame_inner.radius
    pulse = 0.96 + 0.025 * math.sin(t * 5)
    for fraction in (0.92, 0.78, 0.64, 0.50, 0.36, 0.22):
        radius = energy.radius * fraction * pulse
        circle(draw, energy.center.x, energy.center.y, radius, outline=(78, 255, 130), width=max(2, int(4 * camera.scale)))
    circle(draw, energy.center.x, energy.center.y, max(8, 12 * camera.scale), fill=(207, 244, 79), outline=(82, 255, 130), width=max(1, int(2 * camera.scale)))
    for i in range(14):
        angle = 0.9 * i + t * (0.8 + 0.03 * i)
        radius = energy.radius * (0.18 + 0.7 * ((i * 37) % 100) / 100)
        x = energy.center.x + math.cos(angle) * radius
        y = energy.center.y + math.sin(angle) * radius
        circle(draw, x, y, max(1.5, 2.4 * camera.scale), fill=(194, 255, 186))
    return placement


def draw_character_world(image, draw, camera, t, kind, anchor_name, scale):
    placement = place_character(
        character=kind,
        set_geometry=SET,
        set_anchor=anchor_name,
        rig=RIG,
        camera=camera,
        sprite_scale=scale,
    ).placement
    ax, ay = placement.anchor_screen.x, placement.anchor_screen.y
    draw.ellipse((ax - 62 * placement.scale, ay - 10 * placement.scale, ax + 62 * placement.scale, ay + 8 * placement.scale), fill=(25, 24, 24))
    sprite = make_character(kind, t)
    sprite = sprite.resize(
        (max(1, int(round(sprite.width * placement.scale))), max(1, int(round(sprite.height * placement.scale)))),
        Image.Resampling.LANCZOS,
    )
    image.alpha_composite(sprite, (int(round(placement.top_left.x)), int(round(placement.top_left.y))))
    return placement


def render_frame(index):
    t = index / FPS
    camera = camera_at(t)
    image = Image.new("RGBA", (W, H), (20, 25, 36, 255))
    draw = ImageDraw.Draw(image)
    draw_set(image, draw, camera)
    portal = draw_portal(draw, camera, t)
    vex = draw_character_world(image, draw, camera, t, "vex", "vex_start", 0.92)
    milo = draw_character_world(image, draw, camera, t, "milo", "milo_start", 0.92)

    draw.rounded_rectangle((24, 20, 610, 76), radius=14, fill=(9, 14, 22, 235))
    draw.text((44, 34), "2D GEOMETRY CANDIDATE 002 — NOT B1", font=font(22, True), fill=(242, 245, 247))
    draw.rounded_rectangle((24, 640, 655, 698), radius=12, fill=(9, 14, 22, 225))
    info = f"camera origin=({camera.origin.x:.0f},{camera.origin.y:.0f})  scale={camera.scale:.2f}   floor/contact + portal share transform"
    draw.text((42, 657), info, font=font(15), fill=(207, 218, 228))

    if t < 1.8 or t > 7.3:
        for placement in (vex, milo):
            ax, ay = placement.anchor_screen.x, placement.anchor_screen.y
            circle(draw, ax, ay, 6, fill=(255, 220, 45), outline=(20, 20, 20), width=1)
        center = portal.energy.center
        draw.line((center.x - 15, center.y, center.x + 15, center.y), fill=(255, 220, 45), width=2)
        draw.line((center.x, center.y - 15, center.x, center.y + 15), fill=(255, 220, 45), width=2)
    return image.convert("RGB")


# Intentionally silent: this candidate validates composition/geometry only.
command = [
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    str(OUT),
]
process = subprocess.Popen(command, stdin=subprocess.PIPE)
for frame_index in range(N):
    process.stdin.write(render_frame(frame_index).tobytes())
process.stdin.close()
return_code = process.wait()
if return_code:
    raise SystemExit(return_code)
print(OUT)
