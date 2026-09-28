# Standard Renderer Adapter Contract

Phase 5 standardizes how `shotctl` asks local renderers for frames. The directing model chooses the lane; the adapter hides environment-specific invocation details.

## Request contract

Every shot adapter receives exactly one JSON request path:

    adapter REQUEST.json

The request is created by `shotctl` and contains:

- the complete shot specification;
- exact frame indices to render;
- resolved source paths;
- output directory;
- production/spec directory;
- source fingerprint;
- selected visual mode.

The adapter must write one PNG per requested frame:

    000000.png
    000001.png
    ...

The image must exactly match the shot width/height. The adapter must exit non-zero if a requested frame cannot be produced. `shotctl` independently verifies every frame before caching it, so a renderer returning exit code 0 without valid output is not accepted.

Renderer argv may use:

- `{request}` — exact generated request file;
- `{repo}` — repository root, expanded by `shotctl`.

This removes machine-specific absolute script paths from portable shot specs.

## Standard lanes

### Python

Entry point:

    python {repo}/scripts/python_shot_adapter.py {request}

A production-owned Python source declares:

    render_frame(shot, frame_index, output_path, request)

Use for Pillow/NumPy/programmatic geometry, diagrams, particles, typography, and lightweight deterministic visual systems.

### Canvas2D / hand-drawn browser

Entry point:

    python {repo}/scripts/browser_shot_adapter.py {request}

The declared HTML source exposes:

    window.renderFrameAt(seconds, frameIndex, shot)

The adapter uses the existing pinned Puppeteer/Chromium runtime and screenshots exact requested frames. Use this for Canvas2D, SVG/browser motion, illustrative work, and the integrated hand-drawn engine.

The older film-level `canvas_handdrawn_adapter.py` remains useful for complete standalone Canvas films; the request adapter is the shot-level contract.

### Three.js / WebGL

Uses the same deterministic browser contract:

    python {repo}/scripts/browser_shot_adapter.py {request}

Current Pixel limitation: headless Chromium 149 does not expose a WebGL context in this runtime, including with software/ANGLE flags. `rendererctl doctor` therefore reports the lane as degraded.

Do not pretend the lane is usable. Current fallbacks are:

- Blender for spatial 3D;
- Canvas2D for non-WebGL motion/graphics.

The adapter contract remains in place so a future working Chromium/WebGL or another local WebGL runtime can activate the lane without changing director briefs.

### Blender

Entry point:

    python {repo}/scripts/blender_termux_adapter.py {request}

The wrapper owns the environment-specific call into `hermes-ubuntu` and Blender. It delegates frame sampling to `blender_shot_adapter.py`, which opens the declared `.blend`, maps delivery-frame time to the source scene, renders exact subframes, and uses bounded threads.

Current validated runtime: Blender 4.0.2.

For serious Blender shots, the director plan also carries a compositing strategy. The standard shot adapter still owes `shotctl` inspectable RGB preview frames. Production-owned Blender scene/scripts may additionally write declared AOV/pass artifacts for a `multipass` or `hybrid` shot. Those pass outputs are production artifacts, not a substitute for the adapter's normal preview contract.

Before a long pass render, prove one representative frame/short range, verify the intended compositor can reconstruct the shot, and keep pass data in a suitable high-fidelity intermediate rather than prematurely encoding it as lossy delivery media. See `docs/VISUAL_DEVELOPMENT.md`.

### FFmpeg / existing media

Entry point:

    python {repo}/scripts/ffmpeg_shot_adapter.py {request}

The adapter samples declared local media at exact shot times and writes delivery-size PNG frames. Use it for existing footage, cached renders, deterministic temporal source sampling, and compositor-oriented paths.

## Runtime inspection

Use:

    python scripts/rendererctl.py list
    python scripts/rendererctl.py doctor

`doctor` distinguishes:

- standardized adapter exists;
- runtime is actually usable on this device.

The overall doctor can pass while an optional lane is degraded when a safe local fallback exists. The current required local floor is Python + Canvas + Blender + FFmpeg. WebGL is explicitly reported separately.

## Fallback policy

Fallbacks are semantic, not merely technical.

- WebGL spatial 3D → Blender.
- WebGL used only for flat/abstract motion → Canvas.
- Canvas unavailable → Python when the intended look can survive the change.
- Blender unavailable → Python only for shots whose spatial/lighting requirements can honestly be simplified.
- FFmpeg source path unavailable → repair/acquire the source; do not fabricate equivalent footage.

If the fallback would materially change the intended shot, revise the director brief/execution plan instead of silently degrading quality.

## Device/recovery rules

- One expensive render at a time through `shotctl`.
- Render only requested/missing frames.
- Valid completed frames survive interruption.
- Output verification matters more than wrapper exit status.
- Preview before full native-motion render.
- Long Blender work remains independently restartable by frame/range.
- Browser rendering is deterministic by absolute shot time; do not rely on real-time capture.
- Renderer-specific setup must stay behind the adapter rather than leaking into each production spec.

## Phase 5 smoke evidence

Validated locally on the Pixel environment:

- Python adapter: three requested 320×180 frames — PASS.
- Canvas browser adapter: three requested 320×180 frames — PASS.
- FFmpeg adapter: three exact frames sampled from a generated H.264 source — PASS.
- Blender wrapper: one 320×180 Workbench frame through `hermes-ubuntu`, Blender 4.0.2 — PASS.
- Blender multilayer EXR smoke: Eevee, 96×64, `OPEN_EXR_MULTILAYER`, with depth/normal/diffuse/glossy/emission/shadow/mist/AO/Cryptomatte pass flags enabled — PASS. Re-run with `scripts/blender_multipass_smoke.py` when the Blender runtime changes.
- Three.js/WebGL contract: standardized, but runtime probe — DEGRADED (`WebGL unavailable`).

This is adapter/recovery validation, not a visual-quality baseline.