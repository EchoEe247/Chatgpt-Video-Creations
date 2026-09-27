# Canvas hand-drawn renderer

This is a **selective integration**, not a wholesale copy of the upstream demo repository.

Upstream source:
- `alesha-pro/tools`
- skill: `skills/hand-drawn-canvas-animation`
- license: MIT (preserved in `LICENSE.upstream`)

Vendored runtime pieces:
- `runtime/core.js`
- `runtime/studio.js`
- `runtime/cels.js`
- `runtime/materials.js`
- `render.mjs` plus its pinned npm lockfile

Not vendored:
- upstream example films and their creative assets;
- reference photos;
- demo-specific art;
- optional rotoscope/sand/paper3d engines for now.

The local adapter is `scripts/canvas_handdrawn_adapter.py`. It discovers the Termux Chromium binary that is installed outside the normal PATH, preserves the upstream deterministic frame renderer, and exposes stable setup/doctor/preview/render commands.

Quick proof:

    python scripts/canvas_handdrawn_adapter.py setup
    python scripts/canvas_handdrawn_adapter.py doctor
    python scripts/canvas_handdrawn_adapter.py preview examples/canvas-handdrawn/signal-seed.html
    python scripts/canvas_handdrawn_adapter.py render examples/canvas-handdrawn/signal-seed.html

The smoke film is original and exists only to prove that the integrated runtime renders 16:9 native 24 fps frames, contact sheets, synthesized audio, and an H.264/AAC MP4 locally on the Pixel.

## Why this runtime was selected first

It is Canvas2D-first and does not require p5.brush/WebGL for the core path, making it a better fit for reliable Pixel rendering. ClaudeAnimationBase remains a useful reference for timing, acting, pure-time animation and contact-sheet review, but its p5.brush path is deliberately not vendored in Phase 2 because it adds a heavier dependency/render-cost surface without first proving a unique need.
