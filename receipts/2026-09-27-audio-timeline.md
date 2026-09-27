# Phase 4 — Audio Commons + Unified A/V Timeline receipt

Date: 2026-09-27

## Goal

Make audio a first-class production system and put important picture/audio events on one durable clock.

## Implemented

### Unified event timeline

- `src/core/av_timeline.py`
- `scripts/timelinectl.py`
- `templates/av-events.json`

The timeline compiles from the Phase 3 execution plan and optional production-specific events.

Each event records:
- seconds;
- video frame index;
- audio sample index;
- event kind;
- label;
- picture/audio/QA targets;
- optional stem and production metadata.

The compiled timeline is SHA-256 bound to:
- the execution plan;
- the custom event file when one is used.

If either source changes, validation fails until the timeline is recompiled.

### Stem model

The workflow now explicitly plans four separable stems where practical:

- narration/dialogue;
- score;
- ambience;
- effects.

### Core Audio Commons

Added:
- `scripts/build_audio_commons.py`
- `scripts/audioctl.py`
- tracked `assets/audio-commons.json`
- ignored/rebuildable payload at `assets/core/payload/audio-procedural/`

The deterministic fallback pack contains six 48 kHz stereo primitives:
- UI tick;
- soft impact;
- air whoosh;
- short riser;
- low pulse;
- signal chime.

The pack is deliberately tiny. It guarantees basic local effects without making the workflow depend on network retrieval. Better production-specific free assets remain preferred when they materially improve the shot.

The asset catalog now also includes Freesound as a **per-file license-filtered** source. The default automated/Core policy is CC0-only. Kenney and Sonniss remain available through the existing catalog policy.

### Audio QA

`audioctl.py qa` now checks:
- integrated loudness against an explicit target/tolerance;
- true peak against an explicit ceiling;
- unintended silence duration;
- optional declared intentional-silence intervals.

This supplements the existing `videoctl` technical/decode checks.

## Mercy Engine back-test

After the asset catalog changed, the Phase 3 Mercy Engine execution plan was correctly detected as stale and recompiled against the current catalog. The A/V timeline was then compiled against the refreshed execution plan.

Tracked sources:
- `productions/standalone/mercy-engine/source/av-events.json`
- `productions/standalone/mercy-engine/source/av-timeline.json`

Timeline result:
- runtime: 180 seconds;
- frame rate: 24 fps;
- sample rate: 48 kHz;
- total unified events: 62;
- audio-targeted events: 35;
- picture-targeted events: 47;
- QA-targeted events: 15;
- explicit narration-start events: 12.

Example shared event:
- `scene-07.narration-start`
- 91.15 seconds;
- frame 2188;
- sample 4,375,200;
- targets both picture and audio.

This demonstrates that picture and sound can resolve the same event ID rather than independently retyping an offset.

## Mercy Engine master audio back-test

The existing final MP4 passed the new production-specific audio gate:

- integrated loudness: -17.02 LUFS;
- true peak: -2.5 dBFS;
- unintended silence: 0 seconds;
- result: PASS.

This is a back-test only. The old film was not originally authored from the new unified timeline.

## Asset state

After Phase 4:
- catalog entries: 9;
- detected local assets: 3;
- Core candidates/integrated entries represented in the Core manifest: 3.

## Validation

- focused Phase 4 tests: 7 passed;
- full repository suite: 83 passed;
- audio commons byte/hash status: PASS;
- asset catalog validation: PASS;
- Mercy execution plan binding: PASS after recompilation;
- Mercy A/V timeline binding: PASS;
- Mercy final audio QA: PASS.

## Phase boundary

Phase 4 establishes the shared time authority, Core Audio Commons, stem model, and audio QA.

Phase 5 standardizes invocation/recovery adapters across Python, Canvas, Three.js/WebGL, Blender, and FFmpeg so the execution plan can dispatch each shot through a stable renderer contract.