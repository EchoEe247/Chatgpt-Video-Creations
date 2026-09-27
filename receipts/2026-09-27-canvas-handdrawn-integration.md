# Phase 2 — Canvas hand-drawn renderer integration receipt

Date: 2026-09-27

## Scope

Selective integration and local validation of a reusable Opus-era code-animation asset without making the workflow depend on Opus or any other specific model.

## Upstream evidence

Primary integrated source:
- `alesha-pro/tools`
- commit: `b80438eb33823156c575cbedd282a8aa1b32de9f`
- component: `skills/hand-drawn-canvas-animation`
- license: MIT

Evaluated but not vendored:
- `JohnHeibel/ClaudeAnimationBase`
- commit: `0ac8bf2b31942376cb6b8c4074715595d512acd2`
- license: MIT
- decision: retain timing/directing methods; defer p5.brush runtime until a production proves the heavier path is needed.

## Integrated files

- `src/renderers/canvas_handdrawn/runtime/core.js`
- `src/renderers/canvas_handdrawn/runtime/studio.js`
- `src/renderers/canvas_handdrawn/runtime/cels.js`
- `src/renderers/canvas_handdrawn/runtime/materials.js`
- `src/renderers/canvas_handdrawn/render.mjs`
- pinned `package-lock.json`
- upstream MIT notice
- `scripts/canvas_handdrawn_adapter.py`

Upstream demo films, photos, and creative art were not vendored.

## Device/runtime validation

Local runtime:
- Node v24.18.0
- Chromium 149.0.7827.155
- FFmpeg 8.1.2
- Chromium executable resolved from `/data/data/com.termux/files/usr/bin/chromium-browser`

Original proof:
- source: `examples/canvas-handdrawn/signal-seed.html`
- generated final: `.runtime/canvas-handdrawn-smoke/signal-seed-final.mp4`
- SHA-256: `168a7aef8ae0bd1f7f22b98050684cca24b81020c7b8d0251f1ea33f072fae2c`
- generated contact sheet SHA-256: `a11b8c390e069d0a2fd79f9c5b469ebf840090364a96701d920422c6447eca29`

Technical result:
- 1280×720
- 24 fps
- 108 frames
- 4.5 seconds
- H.264 / yuv420p
- stereo AAC / 48 kHz
- strict decode PASS
- no unintended silence detected
- post-repair FFmpeg freeze scan (`n=-45dB:d=0.6`) reported no freeze spans

## Repair performed during validation

The first proof was technically valid but the freeze detector classified each 1.5-second beat as effectively static because motion occupied too little of the frame.

The proof was repaired by adding broad, gradual background/palette progression while preserving the focal actions. The second render removed those freeze spans.

This is exactly the intended workflow behavior: render → inspect signal → repair → rerender → verify.

## Decision

Phase 2 exit condition is met for the first Canvas lane:

- reusable runtime is integrated;
- license is preserved;
- Pixel browser discovery is handled;
- local full render succeeds;
- encoded MP4 passes repository QA;
- motion signal no longer collapses into freeze spans;
- the workflow retains model-independent timing lessons from ClaudeAnimationBase.

This receipt does not claim studio-quality hand-drawn acting or promote a visual baseline.
