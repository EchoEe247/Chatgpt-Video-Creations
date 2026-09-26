"""Blender adapter for shotctl. Reads an existing scene; samples real subframes.

Run with Blender --background --python-exit-code 1 --python THIS -- REQUEST.
All external textures, linked scenes and this adapter must be declared as sources.
"""
import json
import math
import sys
from pathlib import Path
import bpy

request = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text())
shot = request['shot']
blend = next(p for p in request['source_paths'] if p.endswith('.blend'))
bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
source_fps = scene.render.fps / scene.render.fps_base
scene.render.resolution_x = shot['width']
scene.render.resolution_y = shot['height']
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.threads_mode = 'FIXED'
scene.render.threads = 2
scene.render.engine = shot.get('settings', {}).get('engine', 'BLENDER_WORKBENCH')
if 'camera_lens' in shot.get('settings', {}):
    # Only remove lens animation; preserve camera movement and tracking.
    scene.camera.data.animation_data_clear()
    scene.camera.data.lens = shot['settings']['camera_lens']
out = Path(request['output_dir'])
for index in request['frames']:
    frame = scene.frame_start + (shot.get('source_offset_seconds', 0) + index / shot['fps']) * source_fps
    if frame > scene.frame_end:
        raise ValueError('requested time exceeds source scene range')
    scene.frame_set(math.floor(frame), subframe=frame % 1)
    scene.render.filepath = str(out / f'{index:06d}.png')
    bpy.ops.render.render(write_still=True)
    print(f'SHOT_FRAME {index} source_frame={frame:.3f}', flush=True)
