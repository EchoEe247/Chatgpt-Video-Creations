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

The plan distinguishes **renderer choice** from **adapter standardization**. Phase 3 establishes what each shot requires. Phase 5 will finish stable generic invocation adapters for every renderer lane. Until then an unstandardized lane is visible as a blocker instead of being papered over.

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