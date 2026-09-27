# Phase 5 — Standard Renderer Adapters receipt

Date: 2026-09-27

## Goal

Give every major local rendering lane one stable `shotctl` request/output contract so an agent does not need to rediscover environment-specific invocation for each production.

## Standardized lanes

### Python
- entrypoint: `python {repo}/scripts/python_shot_adapter.py {request}`
- production source contract: `render_frame(shot, frame_index, output_path, request)`
- current runtime: READY

### Canvas2D / hand-drawn browser
- entrypoint: `python {repo}/scripts/browser_shot_adapter.py {request}`
- HTML contract: `window.renderFrameAt(seconds, frameIndex, shot)`
- reuses the pinned local Chromium/Puppeteer runtime
- current runtime: READY

### Three.js / WebGL
- entrypoint contract: `python {repo}/scripts/browser_shot_adapter.py {request}`
- current runtime: DEGRADED
- observed blocker: current Pixel headless Chromium does not expose a WebGL context, including software/ANGLE launch attempts
- declared fallback lanes: Blender, then Canvas when the visual requirement can honestly survive the change

This is deliberately represented as a blocker rather than falsely marking WebGL ready.

### Blender
- entrypoint: `python {repo}/scripts/blender_termux_adapter.py {request}`
- wrapper owns the `hermes-ubuntu` PRoot invocation
- inner renderer: `scripts/blender_shot_adapter.py`
- current runtime: Blender 4.0.2
- current runtime: READY

### FFmpeg
- entrypoint: `python {repo}/scripts/ffmpeg_shot_adapter.py {request}`
- exact-time frame sampling from declared local media
- current runtime: READY

## Portable renderer argv

`shotctl` now expands two special renderer tokens:

- `{request}` → exact generated request JSON
- `{repo}` → repository root

This removes device-specific absolute adapter paths from reusable shot specifications. `templates/shot-workflow.json` now uses the stable Blender wrapper through `{repo}`.

## Runtime doctor

`python scripts/rendererctl.py doctor` now separates adapter standardization from actual device capability.

Current Pixel result:
- Python: READY
- Canvas: READY
- Three.js/WebGL: DEGRADED
- Blender: READY
- FFmpeg: READY
- overall required local floor: PASS

The required floor intentionally excludes WebGL because safe local fallback lanes exist.

## Local smoke evidence

All available required lanes produced verified 320×180 PNG frames from the common request contract.

Representative SHA-256 values:

- Python frame 12: `3c8abf0031a5e045dc4a33ead57e6d8a7ee00adc483e3db38b4c24a48d775d2f`
- Canvas frame 12: `2106bfc1c8f11929fb8e27639ce27b1cc2282ed405896b7756dc28b9870ddb0d`
- FFmpeg frame 12: `bbd854ad560830feec68ecb93d28c6d280430b77eeb7fa4e9cb6e75dda955a8d`
- Blender frame 0: `1d29d817be0366fad1850129a791758d082bbcaee49a422afceef0ec03d1b3c2`

Observed Blender stderr included EGL initialization warnings, followed by successful surfaceless EGL fallback and a valid rendered frame. Output validation, not wrapper chatter, remains authoritative.

The WebGL smoke failed explicitly with `WebGL unavailable`; no output was fabricated.

## Recovery behavior

This Phase keeps the existing `shotctl` guarantees:

- render only missing/requested frames;
- verify dimensions and file integrity after every batch;
- keep valid completed frames across interruption;
- distrust a renderer process that exits 0 but omits/corrupts output;
- preview/review before full native motion;
- one expensive render at a time on the device.

## Validation

- renderer adapter focused tests: 6 passed;
- existing shot workflow + director execution focused tests: 19 passed;
- complete repository suite after final changes: 89 passed;
- `rendererctl doctor`: PASS with only Three.js/WebGL explicitly degraded;
- Mercy Engine execution plan: recompiled and PASS;
- Mercy Engine A/V timeline: recompiled against the new execution-plan hash and PASS.

## Validation boundary

This receipt proves adapter invocation/recovery and device readiness. It is not a visual-quality baseline.

Phase 6 will improve automated QA signals around motion density, freezes, composition/text bounds, phone-scale readability, and normal-speed review.