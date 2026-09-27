# RIDGELINE — A Descent

A 132-second original 3D mountain-bike film built and rendered entirely through Local Workspace on the Pixel. All rider/bicycle/environment motion is authored geometry and animation. No real riding footage or online video-generation model is used.

## Deliverable

- Watch locally: http://127.0.0.1:8881/
- Master: final/ridgeline.mp4
- Native picture: 960×540, 24 fps, H.264/yuv420p.
- Audio: AAC stereo, 48 kHz, mastered toward -16 LUFS.
- 22 six-second shots cover a continuous route. There are no recycled action clips, interpolated frames or freeze-frame padding.
- Music and ground textures are external reusable assets; provenance lives in source/provenance.json.

## Adrenaline revision

The current review candidate incorporates the rider-feedback pass: the rider uses a more anatomical layered silhouette and drops into a lower attack stance during the two fast descent windows; airborne motion is tied to visible authored dirt kickers/drops instead of appearing over flat trail; high-speed windows widen the lens, look farther down-trail, add controlled inertial camera movement, and introduce ground-hugging dust/needle cues; wind and tire-bed energy rise with speed while calmer trail sections remain. Landing audio timings are regenerated from the revised route.

Current candidate SHA-256: `348de54393756c5d7e28b9c9fb64383242e56fa76ea336cc92203de34ea99e56`. Technical QA passes. Creative QA passes with review notes on motion cadence for shots 01/22 and one non-click loudness transition at 72.0 s.

## Honest quality boundary

This is a visibly computer-rendered, game-like 3D result. It does not achieve the requested photorealism. The terrain, fir silhouettes and procedural rider need higher-quality meshes/materials and more sophisticated lighting for that standard. This file must not be presented as proof of photorealistic local video capability.

Preview stills were inspected and the neck gap / helmet-in-POV defects were corrected. The final candidate (SHA-256 `846454e86350267cb24142735f629c9b2ed9925cda8df07dc0743eb91742f803`) passes technical QA and automated creative QA. No freezes, weak-motion shots, repeated-camera warnings, visual-cut warnings, audio-transition warnings, AV-sync warnings, or layout violations remain. Two cadence points (shots 01 and 08) remain explicit review notes rather than automated failures. Automated measurements and still/sequence inspection still do not replace a complete human audiovisual watch, so user review remains the final perceptual gate.

## Reproduce locally

The existing repository's director/execution/timeline and video/creative QA tools remain the production contract. The production renderer is a new Python/ModernGL implementation using the same local Ubuntu runtime as Blender, with EGL/llvmpipe software rendering.

Runtime: Python 3 with numpy, Pillow, moderngl==5.12.0 and glcontext; FFmpeg. On this device, these dependencies are in hermes-ubuntu. Rendering is native CPU software rasterization, not remote GPU use.

1. Acquire the three asset files documented in source/provenance.json into assets/.
2. Compile source/director-brief.json with scripts/directorctl.py.
3. Render via proot-distro login hermes-ubuntu -- env LP_NUM_THREADS=3 python3 ABSOLUTE_SOURCE_RENDER_3D_PATH.
4. Run source/build_audio.py with native Termux Python.
5. Run source/finish.py with native Termux Python. This assembles an explicit shot list, applies titles/finishing, masters audio, writes the final hash, and executes repository QA.
6. Run serve.py from this production directory for byte-range-aware playback on port 8881.

Render jobs are persisted in render-job.json. Valid finished shot MP4s are retained when the renderer resumes. A source change affecting picture requires invalidating affected shot files; do not silently reuse stale shots.

## Implementation notes

- Bicycle wheel rotation follows traveled distance.
- Coasting, pedaling, corner lean, airborne trajectory and rider contact anchors are deterministic in time.
- Ground height and camera ground clearance share the trail's world coordinates.
- All cameras follow increasing route distance.
- The same jump world positions produce picture trajectory and landing sound timestamps.
- Static terrain/foliage are divided into world-space regions; mesh instances batch rider and bike geometry.
- Final score, local effects and master mix remain separate.
- No general renderer readiness claim was changed; this production documents one working EGL path on the current runtime.
