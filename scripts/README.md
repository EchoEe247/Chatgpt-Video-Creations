# Scripts

Use the narrowest entry point that matches the task.

- `directorctl.py` — validates director briefs and compiles hash-bound, agent-independent execution plans with renderer lanes, asset resolution, timing, review points, and explicit blockers.
- `timelinectl.py` — compiles execution plans plus production-specific events into one hash-bound seconds/frame/sample timeline shared by picture, audio, and QA.
- `audioctl.py` — builds/verifies the tiny procedural Core Audio Commons and applies explicit loudness/true-peak/silence master checks.
- `productionctl.py` — restart-safe production controller. Persists Local Workspace render-job identity, copies candidates into immutable iteration directories, binds technical/creative/final-screening evidence to candidate SHA-256, reconciles interrupted jobs, tracks repair history/budget, validates studio review transactionally before immutable publication, and requires a fresh Local Workspace bootstrap result for bound render dispatch.
- `videoctl.py` — media inspection/QA primitives: probe, strict decode, loudness/silence analysis, frames, contact sheets, full-runtime baseline comparison, codec/pixel/audio delivery checks, receipts, and review packs.
- `canvas_handdrawn_adapter.py` — stable Pixel/Termux setup, browser discovery, preview, and full-render entry point for the integrated Canvas2D hand-drawn renderer.
- `rendererctl.py` — reports standardized renderer lanes versus actual device runtime readiness, including the current WebGL degradation/fallback state.
- `blender_phase0_fixture.py` + `finishing_phase0.py` — conditional Blender-finishing feasibility proof: animated 720p multilayer EXR render, idempotent per-frame resume, actual OpenImageIO channel inventory, non-zero vector validation, and resource-budget receipt. See `docs/FINISHING_ENGINE.md`.
- `finishingctl.py` — validates/fingerprints Render Bundle and Finishing Recipe v1 contracts, optionally verifies frame bytes/hashes, and checks a recipe against the exact bundle policy/pass/mask inventory.
- `creativeqactl.py` — builds candidate-bound experience QA: freeze/motion and interior cadence, camera repetition, phone/layout checks, every-cut transition strips/clips, visual-style continuity, audio boundary/spectral/stem/pacing analysis, A/V sync clips, evidence-bound assistant review, and BEFORE/AFTER repair comparison.
- `cinematicqactl.py` — current cinematic/physical triage layer for continuity, exposure/detail, camera periodicity, stereo spatialization, shared motion-model inputs, and production-plan hygiene. It complements creative QA; its current heuristics are risk signals/production checks, not a substitute for perceptual review.
- `studiovalidate.py` — freezes opaque seeded-defect/clean-control media benchmarks with a concealed answer key, freezes findings before reveal, scores detection/localization/false alarms, and generates a separate neutral operational fresh-session handoff.
- `python_shot_adapter.py`, `browser_shot_adapter.py`, `blender_termux_adapter.py`, `ffmpeg_shot_adapter.py` — common `{request}` frame-render contract used by `shotctl` across the major local renderer lanes.
- `assemble-scenes.py` — assembles only the explicit ordered scenes listed in an assembly manifest. It rejects missing/duplicate inputs, output-as-input collisions, stream incompatibility, optional SHA mismatches, and duration mismatches before concat-copy and master decode verification.
- `workflowctl.py` — workflow freshness/binding entry point. Repository-native bootstrap is discovery/CI only for bridge compatibility; final production binding consumes the evaluated Local Workspace bootstrap JSON via `--bootstrap-result`.
- `validate-production-v2.py` — production package schema/gate validation. Default mode applies runtime compatibility aliases; `--strict` validates committed JSON exactly as stored. Repository CI uses strict mode so committed data cannot rely on legacy normalization.
- `validate-scene-plan.py` — scene timeline/review-point validation.
- `validate-continuity.py` — episode continuity-state validation.
- `validate-scene-alignment.py` — structural shared-geometry validation.
- `validate-baselines.py` — B-series registry validation.
- `validate-quality-status.py` — validates the machine-readable current user quality-state registry without conflating it with formal baselines.
- `generate-lane-brief.py` — deterministically generates compact lane briefs from `workflow/CURRENT.json` plus current quality status; CI checks the checked-in cinematic brief for drift.
- `validate-workflow-version-bump.py` — CI guard requiring canonical workflow changes to increase the dot-separated workflow version monotonically; unavailable event bases emit an explicit warning and fall back to `HEAD^` when possible.
- `validate-markdown.py` — tracked Markdown local-link and literal-escape hygiene checks.
- `validate-repository.py` — consolidated repository contract validation, including all tracked v2 production manifests, templates, workflow docs, baselines, quality status, generated brief, Markdown and Python compilation.
- `render-2d-geometry-candidate*.py` — preserved reproducible geometry baseline renderers.

For ChatGPT/Local Workspace work, long render commands should normally be started through the plugin's persisted background-job tools. Record the returned job ID immediately with `productionctl.py rendering`, then reconcile it after every interruption/resume.

Use `templates/scene-assembly.json` as the starting point for long-form assembly. Do not replace it with a directory sweep.