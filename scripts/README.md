# Scripts

Use the narrowest entry point that matches the task.

- `directorctl.py` — validates director briefs and compiles hash-bound, agent-independent execution plans with renderer lanes, asset resolution, timing, review points, and explicit blockers.
- `timelinectl.py` — compiles execution plans plus production-specific events into one hash-bound seconds/frame/sample timeline shared by picture, audio, and QA.
- `audioctl.py` — builds/verifies the tiny procedural Core Audio Commons and applies explicit loudness/true-peak/silence master checks.
- `productionctl.py` — restart-safe production controller. Persists Local Workspace render-job identity, copies candidates into immutable iteration directories, binds technical/creative/final-screening evidence to candidate SHA-256, reconciles interrupted jobs, tracks repair history/budget, and requires a complete candidate-bound `--studio-review` record before assistant acceptance when studio review is enabled.
- `videoctl.py` — media inspection/QA primitives: probe, strict decode, loudness/silence analysis, frames, contact sheets, full-runtime baseline comparison, codec/pixel/audio delivery checks, receipts, and review packs.
- `canvas_handdrawn_adapter.py` — stable Pixel/Termux setup, browser discovery, preview, and full-render entry point for the integrated Canvas2D hand-drawn renderer.
- `rendererctl.py` — reports standardized renderer lanes versus actual device runtime readiness, including the current WebGL degradation/fallback state.
- `creativeqactl.py` — builds candidate-bound experience QA: freeze/motion and interior cadence, camera repetition, phone/layout checks, every-cut transition strips/clips, visual-style continuity, audio boundary/spectral/stem/pacing analysis, A/V sync clips, evidence-bound assistant review, and BEFORE/AFTER repair comparison.
- `cinematicqactl.py` — current cinematic/physical triage layer for continuity, exposure/detail, camera periodicity, stereo spatialization, shared motion-model inputs, and production-plan hygiene. It complements creative QA; its current heuristics are risk signals/production checks, not a substitute for perceptual review.
- `python_shot_adapter.py`, `browser_shot_adapter.py`, `blender_termux_adapter.py`, `ffmpeg_shot_adapter.py` — common `{request}` frame-render contract used by `shotctl` across the major local renderer lanes.
- `assemble-scenes.py` — assembles only the explicit ordered scenes listed in an assembly manifest. It rejects missing/duplicate inputs, output-as-input collisions, stream incompatibility, optional SHA mismatches, and duration mismatches before concat-copy and master decode verification.
- `validate-production-v2.py` — production package schema/gate validation.
- `validate-scene-plan.py` — scene timeline/review-point validation.
- `validate-continuity.py` — episode continuity-state validation.
- `validate-scene-alignment.py` — structural shared-geometry validation.
- `validate-baselines.py` — B-series registry validation.
- `render-2d-geometry-candidate*.py` — preserved reproducible geometry baseline renderers.

For ChatGPT/Local Workspace work, long render commands should normally be started through the plugin's persisted background-job tools. Record the returned job ID immediately with `productionctl.py rendering`, then reconcile it after every interruption/resume.

Use `templates/scene-assembly.json` as the starting point for long-form assembly. Do not replace it with a directory sweep.