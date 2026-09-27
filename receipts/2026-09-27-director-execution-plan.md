# Phase 3 — Director to Execution Plan receipt

Date: 2026-09-27

## Goal

Convert a creative director brief into a durable operational contract that a capable agent can execute without reconstructing hidden conversation reasoning.

## Implemented

- `src/core/director_execution.py`
  - strict director-brief validation;
  - contiguous absolute shot timing;
  - hero-shot marking;
  - renderer-lane normalization;
  - local adapter readiness;
  - asset catalog/provenance resolution;
  - local → absolute review-point conversion;
  - common QA requirements;
  - long-shot density warnings;
  - single-agent-default execution policy;
  - source SHA-256 binding and stale-plan detection.

- `scripts/directorctl.py`
  - `validate-brief`
  - `compile`
  - `validate-plan`
  - `status`

- `templates/execution-plan.json`
- `docs/DIRECTOR_EXECUTION_PLAN.md`
- regression tests in `tests/test_director_execution.py`

## Deliberate behavior

The compiler does not silently invent missing creative decisions.

It rejects briefs with missing shot intent, visible event, camera, subject/environment motion, audio cue, renderer, invalid review points, duplicate IDs, or runtime mismatch.

It also does not mechanically split long shots. Instead it emits a `shot_density_review` warning so the directing agent must either justify the hold or rewrite the brief into purposeful shorter shots.

Unknown renderers and unresolved assets remain explicit blockers.

## Mercy Engine back-test

The preserved Mercy Engine brief was compiled to:

`productions/standalone/mercy-engine/source/execution-plan.json`

Result:
- runtime: 180 seconds;
- 12 planned shots;
- 7 hero shots;
- renderer lane: Python;
- exact Quaternius spacecraft resolved through the asset catalog;
- unresolved assets: 0;
- blocked shots: 0;
- 12 shot-density warnings, correctly exposing the known uniform 15-second structure.

The compiled plan is hash-bound to both the director brief and asset catalog. `directorctl validate-plan` and `status` reject stale bindings after either source changes.

## Agent-independence contract

Every plan records:

- `owner_mode: single_agent_default`
- `cooperation_required: false`
- `parallelism: optional_only_when_beneficial`
- `state_authority: repository_files`

This makes cooperation an optimization rather than a production dependency.

## Validation

- focused Phase 3 tests: 6 passed;
- complete repository suite: 76 passed;
- Mercy Engine compiled execution plan: PASS;
- source-binding status: PASS.

## Boundary to later phases

Phase 3 decides **what** each shot requires and surfaces whether its renderer adapter is ready.

Phase 5 remains responsible for standardizing generic invocation adapters across Python, Canvas, Three.js/WebGL, Blender, and FFmpeg. The execution plan deliberately exposes an unstandardized adapter as a blocker instead of pretending it is executable.
