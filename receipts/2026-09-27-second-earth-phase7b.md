# Phase 7B — SECOND EARTH implementation/render receipt

Date: 2026-09-27

## Result

Phase 7B produced the first complete 150-second SECOND EARTH candidate using the local workflow.

Candidate SHA-256:

`185f2eb4d6b10145c8610e4a1602845baf441a03dac674f92e0cd5d93992a732`

Candidate technical identity before formal Phase 7C QA:

- duration: 150.000000 seconds
- size: 13,615,179 bytes
- video codec: H.264
- resolution: 1280×720
- frame rate: 24/1
- pixel format: yuv420p
- audio codec: AAC
- audio sample rate: 48 kHz
- channels: 2
- full decode: PASS, no ffmpeg decode errors

The production controller copied the candidate into immutable iteration 00 and moved the state to `CANDIDATE` with `technical_qa` as the next action. User review remains PENDING.

## Implemented production sources

- `render_benchmark.py` — restartable local orchestration and final assembly
- `renderers/python_frames.py` — seven deterministic procedural/motion-design shots
- `renderers/canvas_world.html` — six hand-drawn inner-world shots
- `renderers/render_canvas_shots.mjs` — headless local Canvas encoder
- `renderers/build_blender_physical.py` — physical lab/operator/breaker scene
- `renderers/build_blender_probe.py` — launch/orbit/station scene
- `audio/build_audio.py` — cached narration, score, ambience, effects and final mix

No online video-generation model was used.

## Renderer coverage

All 21 planned shots now exist at their authored durations.

Visual lanes:

- Python/Pillow/NumPy: shots 01, 04, 08, 14, 15, 17, 19
- Canvas hand-drawn: shots 03, 05, 06, 09, 13, 18
- Blender physical: shots 02, 07, 16
- Blender probe/spatial: shots 10, 11, 20
- FFmpeg editorial: shots 12, 21

## Blender reliability finding

Long Workbench movie renders inside Pixel/PRoot can terminate with SIGSEGV/EGL instability even when frames are valid.

The production was changed to fail safely:

- render spatial checkpoints as PNGs;
- use 6 fps Blender source checkpoints to bound cost;
- preserve successful frames across failures;
- resume rather than restart;
- encode the checkpoint sequence only after the required count exists;
- produce 24 fps delivery shots locally;
- deterministically pad/trim interpolation tails when the final fractional frames would otherwise make a shot short.

This turned a crash-prone Blender lane into a restartable one and is now part of the durable workflow rather than a one-off manual workaround.

## Audio

The 21 narration lines were generated as individually cached clips with the existing Deepgram account.

The local audio build also creates independent:

- narration;
- score;
- ambience;
- effects;
- final master

stems.

The final master is 48 kHz stereo and exactly 150 seconds. Formal loudness/silence analysis belongs to Phase 7C.

## Known implementation compromise

Blender spatial source checkpoints are rendered at 6 fps on this device and converted to the 24 fps delivery timeline. The final file itself is native 24 fps H.264, but the spatial lane is not a 24 fps Blender source render.

That compromise is explicit so later agents can improve it instead of silently assuming every lane was rendered identically.

## Next action

Run 9 / Phase 7C:

1. deterministic technical QA;
2. candidate-bound creative-QA bundle;
3. inspect phone-scale frames and normal-speed clips;
4. repair only concrete failures;
5. rerun QA on the repaired candidate;
6. assistant creative PASS only with bound evidence;
7. expose the final review link to Angel;
8. leave user gate PENDING until Angel explicitly accepts.
