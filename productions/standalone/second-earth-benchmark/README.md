# SECOND EARTH benchmark

This is the fresh integrated benchmark planned after the Mercy Engine workflow upgrades.

## Target

A 2:30 cinematic speculative AI story that is harder than Mercy Engine in shot density, scale changes, renderer diversity, and synchronization while remaining practical on the Pixel-local production stack.

The benchmark is intentionally split across three 25-minute runs:

- **Run 7 / Phase 7A:** story, directing, assets, storyboard, execution plan and shared A/V plan.
- **Run 8 / Phase 7B:** implement renderer sources, render shots, build narration/score/effects, assemble candidate.
- **Run 9 / Phase 7C:** technical + creative QA, targeted repairs, final candidate and user-review handoff.

## Current checkpoint

**Phase 7B is complete.** A first full candidate is registered with the production controller and is waiting for technical QA.

Candidate:

- runtime: 150.000 seconds
- video: H.264, 1280×720, 24 fps, yuv420p
- audio: AAC, 48 kHz stereo
- SHA-256: `185f2eb4d6b10145c8610e4a1602845baf441a03dac674f92e0cd5d93992a732`
- decode: PASS
- production state: `CANDIDATE`
- next action: `technical_qa`
- user review: still PENDING

The implementation now has independently restartable source lanes for:

- deterministic Python/Pillow/NumPy motion design;
- integrated hand-drawn Canvas scenes;
- Blender physical/server-vault scenes;
- Blender probe/orbit/station scenes;
- FFmpeg editorial/contact/final-card shots;
- deterministic score/ambience/effects plus cached Deepgram narration;
- final local assembly.

## Blender recovery learned during Phase 7B

The Pixel/PRoot Blender path proved that a single long Workbench movie render can terminate under EGL/PRoot despite valid frames.

The production therefore uses the repository's intended resilient pattern:

1. author and save the Blender scene;
2. render low-rate spatial keyframes to PNG checkpoints;
3. keep every successful PNG after a crash;
4. resume only missing work;
5. encode the checkpoint sequence locally;
6. convert the spatial reel to 24 fps at the shot boundary;
7. repair sub-frame tail shortages deterministically so every authored shot duration remains exact.

For SECOND EARTH the Blender spatial lane uses 6 fps source checkpoints and 24 fps final delivery. This is a device-specific production compromise, not a change to the final delivery frame rate.

## Director contract

The compiled plan has:

- 150-second runtime;
- 21 purposeful shots, all 8 seconds or shorter;
- 7 hero shots;
- Python, Canvas2D, Blender and FFmpeg lanes;
- zero unresolved assets;
- zero blocked shots;
- zero director warnings;
- 134 shared A/V events;
- creative QA required before assistant PASS.

No online video-generation model is part of the production.

## Local-first assets

The first pass required no new download.

It reuses:

- the integrated hand-drawn Canvas runtime;
- the existing Quaternius CC0 spacecraft source already present locally;
- the deterministic Core Audio Commons;
- the existing Deepgram narration account for speech only.

Optional Poly Haven / ambientCG CC0 additions remain non-blocking and are allowed only if a preview proves a specific quality improvement.

## Source of truth

Read these in order:

1. `source/story.md`
2. `source/director-brief.json`
3. `source/storyboard.md`
4. `source/asset-resolution.json`
5. `source/execution-plan.json`
6. `source/implementation-map.json`
7. `source/av-events.json`
8. `source/av-timeline.json`
9. `source/layout-qa.json`
10. `source/benchmark-acceptance.json`
11. `render_benchmark.py`
12. `production.json`

Run 9 should start from the immutable iteration-00 candidate and use the Phase 6 technical/creative evidence gates. It should repair only concrete failures rather than reopening the story or regenerating already accepted lanes without cause.
