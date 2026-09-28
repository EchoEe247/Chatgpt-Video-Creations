# Director → Execution Plan

The director brief is creative authority. The execution plan is the durable operational contract produced from it.

Use:

    python scripts/directorctl.py validate-brief path/to/director-brief.json
    python scripts/directorctl.py compile path/to/director-brief.json path/to/execution-plan.json
    python scripts/directorctl.py validate-plan path/to/execution-plan.json
    python scripts/directorctl.py status path/to/execution-plan.json

## What compilation does

Compilation does not invent a film from scratch. It converts explicit directing decisions into a machine-readable plan:

- assigns contiguous absolute start/end times;
- marks hero shots;
- normalizes renderer requests into stable lanes;
- records whether the local adapter is currently ready;
- resolves declared assets against `assets/catalog.json`;
- carries source URL, license, distribution mode, and local hint into the work unit;
- converts local review points into absolute timeline review points;
- carries narrative purpose, visible event, motion, camera, look, transitions, audio cues, continuity dependencies, and failure modes;
- applies a common QA contract;
- hash-binds the plan to the director brief and asset catalog;
- records single-agent ownership as the default and cooperation as optional.

The compiler is intentionally strict. Missing narrative purpose, visible event, camera, motion, audio cue, renderer, invalid timing, duplicate shot IDs, or inconsistent runtime cause validation failure rather than hidden guessing.

`validate-plan` and `status` also verify the stored SHA-256 bindings against the current director brief and asset catalog. If either source changes, the plan is stale and must be recompiled before execution.

## Shot-density rule

The compiler does **not** automatically split a long shot. Shot subdivision is a directing decision because a mechanical split can destroy cause/reaction, music synchronization, or an intentional hold.

Instead, shots above the configured heuristic (8 seconds by default) receive `shot_density_review`.

The agent must either:

1. justify the hold through the viewer reads and keep it, or
2. revise the director brief into multiple purposeful shots and recompile.

This is how the workflow avoids returning to the uniform 15-second structure exposed by The Mercy Engine.

## Renderer lanes

Current normalized lanes:

- `python` — Pillow/NumPy/programmatic rendering;
- `canvas_handdrawn` — integrated Canvas2D hand-drawn renderer;
- `threejs` — Three.js/WebGL;
- `blender` — Blender;
- `ffmpeg` — composition/temporal treatment;
- `unresolved` — explicit blocker.

The plan distinguishes **renderer choice** from **runtime readiness**. Phase 5 now provides stable request/output adapters for Python, Canvas, Three.js/WebGL, Blender, and FFmpeg. Use `python scripts/rendererctl.py doctor` to verify the current device before rendering.

The current Pixel reports Python, Canvas, Blender, and FFmpeg ready. The Three.js/WebGL contract is standardized but the headless Chromium runtime does not currently expose a WebGL context, so that lane remains an explicit blocker with Blender/Canvas fallback lanes rather than being falsely marked ready.

## Asset-strategy gate

New serious director briefs should include the top-level `asset_strategy` review before rendering. Each high-impact requirement declares its need, kind, make-vs-source decision, selected assets when applicable, structural/license requirements, adaptation plan and local-authorship responsibilities.

The compiler treats `unresolved` requirements as explicit blockers. `source_free`, `reuse_local` and `hybrid` requirements remain unresolved until a selected asset resolves deterministically and an adaptation plan exists. `author_local` and `hybrid` must state what is locally authored.

Legacy briefs without `asset_strategy` remain compilable for compatibility but receive `asset_strategy_missing`; that warning is not a precedent for new productions.

Provider entries such as `provider.mixamo` are discovery routes, not concrete selected assets, so they cannot satisfy a production requirement by themselves. `directorctl.py status` reports `blocked_asset_requirements`, and the plan summary exposes `execution_ready=false` while a concrete asset decision remains unresolved.

This prevents a fresh agent from turning “we need a convincing human/car/environment” into an undocumented scratch-build simply because a renderer can generate primitives.

## Visual-development gate

The compiled plan carries `visual_development` and each shot's compositing contract.

For new briefs, a required previs/look-dev gate is unresolved until its status is `approved` and a reviewable artifact is declared. A deliberate `not_required` decision must use matching `not_required` status. `directorctl.py status` reports blocked development gates.

New Blender shots also remain execution-blocked while `compositing.mode` is `unresolved`. Multipass/hybrid shots require both a non-empty pass list and explicit goals. Status reports blocked compositing shots separately.

Legacy briefs without these fields receive compatibility warnings and remain compilable.

See `docs/VISUAL_DEVELOPMENT.md`.

## Asset resolution

Prefer asset IDs in new director briefs:

    "assets": ["model.quaternius-ultimate-space-spaceship"]

Human-readable legacy names can resolve only when the match is deterministic and unique. Ambiguous or unknown resources remain unresolved and are surfaced in plan warnings/status.

No fuzzy model guess is accepted as provenance.

## Agent independence

The plan contains:

    "owner_mode": "single_agent_default"
    "cooperation_required": false

One agent owns the production by default. ChatGPT, Hermes, Astra, or another capable agent may independently execute the same durable contract. Parallel/cooperative work is an optimization only.

Critical creative and operational details belong in repository files, not in hidden session reasoning.

## Relationship to existing controls

The execution plan sits above the current shot and production controls:

**director brief → execution plan → shot implementation/shotctl → productionctl → technical + creative QA → user review**

`shotctl` remains responsible for version-bound frame evidence and preview/motion review.

`productionctl` remains responsible for immutable candidate iterations, candidate hashes, final technical evidence, repair cycles, assistant review, and the user gate.

The execution plan does not weaken either control.

## Mercy Engine back-test

The preserved Mercy Engine director brief compiles successfully as a regression test:

- 180 seconds;
- 12 shots;
- 7 hero shots;
- Python renderer lane;
- Quaternius spacecraft resolved to the exact catalog asset/license;
- zero unresolved assets;
- all twelve 15-second shots flagged for density review.

That last result is intentional: the compiler exposes the structural limitation we already identified instead of accepting it silently.