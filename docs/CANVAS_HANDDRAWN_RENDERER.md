# Canvas Hand-Drawn Renderer

## Purpose

This renderer adds a local Canvas2D animation lane for hand-drawn, illustrative, print, and stylized motion work.

It is intended for shots where Pillow/SVG is too rigid and Blender is unnecessary or too expensive.

## Upstream basis

Selective source integration from:

- repository: `alesha-pro/tools`
- upstream commit: `b80438eb33823156c575cbedd282a8aa1b32de9f`
- skill: `skills/hand-drawn-canvas-animation`
- license: MIT
- local upstream notice: `src/renderers/canvas_handdrawn/LICENSE.upstream`

Only the reusable runtime and renderer surface was vendored. Demo films, reference photos, and production-specific art were deliberately excluded.

Vendored runtime:

- `runtime/core.js`
- `runtime/studio.js`
- `runtime/cels.js`
- `runtime/materials.js`
- `render.mjs`
- pinned npm lockfile

## Local adapter

Use:

    python scripts/canvas_handdrawn_adapter.py setup
    python scripts/canvas_handdrawn_adapter.py doctor
    python scripts/canvas_handdrawn_adapter.py preview <film.html> --grid 18
    python scripts/canvas_handdrawn_adapter.py render <film.html>

The adapter handles the Pixel/Termux Chromium binary location directly. This avoids depending on the browser binary being discoverable through ordinary PATH lookup.

The core render path is:

**HTML/Canvas scene code → deterministic absolute-time frame evaluation → headless Chromium → PNG frame sequence → FFmpeg → H.264/AAC MP4 + contact sheet**

## Pixel fit

The selected runtime is Canvas2D-first. It does not require WebGL or p5.brush for the core lane.

That matters on the current device because:

- rendering is deterministic and seekable;
- frames can be generated without real-time capture;
- 1280×720 native 24 fps output is practical for lightweight scenes;
- the runtime can synthesize score/effects from the same timeline;
- Chromium and FFmpeg already exist locally;
- scene complexity can scale independently from Blender.

Use previews before full renders. Dense watercolor/particle/material effects can still become expensive.

## ClaudeAnimationBase evaluation

`JohnHeibel/ClaudeAnimationBase` was evaluated at upstream commit:

`0ac8bf2b31942376cb6b8c4074715595d512acd2`

Its strongest transferable rules are retained in our directing workflow:

- frames must be pure functions of time;
- storyboard before coding;
- one readable focal event at a time;
- cause then reaction;
- anticipation before fast actions;
- hold important meanings long enough for the viewer to register them;
- use contact sheets and motion strips before accepting a scene.

Its p5.js/p5.brush runtime is **not** vendored in this phase. The upstream project itself warns that watercolor fills can take seconds per frame without a dedicated GPU. We already gained the useful directing/timing methods while keeping the first integrated Canvas lane lighter and easier to run on the Pixel.

This can be revisited if a future goal needs a look that the current Canvas2D runtime cannot reproduce efficiently.

## Production rules

- Treat the runtime as a renderer, not as a pre-made art style.
- Build original characters, compositions, and story elements.
- Keep upstream license/attribution with redistributed runtime code.
- Do not copy upstream example art or another creator's reference film shot-for-shot.
- Use deterministic seeded variation rather than uncontrolled frame-to-frame randomness.
- Separate scene package duration from shot duration.
- Review normal-speed motion, not only still frames.
- Use generated contact sheets as triage, not final creative acceptance.
- Run repository media QA on the encoded MP4.

## Phase 2 local proof

Original proof film:

`examples/canvas-handdrawn/signal-seed.html`

The film uses no upstream demo art. It exercises:

- 16:9 format;
- three independently timed visual beats;
- moving hand-drawn/procedural forms;
- palette progression;
- seeded drawing variation;
- local synthesized score;
- exact 24 fps frame export;
- H.264/AAC assembly;
- contact-sheet generation.

Validated local output:

- 1280×720
- 24 fps
- 4.5 seconds
- 108 video frames
- H.264 / yuv420p
- stereo AAC / 48 kHz
- strict decode: PASS
- unintended silence: none detected
- freeze scan at `-45 dB / 0.6 s`: no freeze spans after motion-strengthening repair

The proof is functional validation of the renderer lane, not a visual-quality baseline.
