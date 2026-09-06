# Operating Model Integration Receipt — 2026-09-06

## Scope

Integrate the clarified project operating philosophy into `Chatgpt-Video-Creations` without replacing the existing business/OSS and original-animation goals.

## Starting state

Starting commit: `5206a03024df5cafd1fd4407aadd1cda14c46e0a`

Already established before this pass:

- two production lanes;
- release-grounded business marketing;
- season-first / episode-by-episode animation workflow;
- independent-scene long-form rendering;
- shared 2D set geometry primitives;
- foot-anchor and portal-inheritance regression tests;
- MP4 visual QA requirement.

## Changes made

- added the discovery → formalization → validation → baseline → operation model;
- added explicit agent-autonomy and stop/escalation gates;
- separated qualitative capability baselines from formal B-series validated baselines;
- added an intentionally empty B-series registry and validator rather than inventing a retroactive `B1`;
- added durable baseline receipt rules;
- formalized 2D canvas/coordinate metadata in the geometry model;
- marked the existing set-anchor template as synthetic/unvalidated rather than production truth;
- clarified that structural geometry tests do not prove visual correctness;
- documented which current geometry relationships are mature and which numeric measurements are still provisional;
- extended CI coverage for geometry and baseline registry validation.

## Validation performed before commit

Local stdlib test/validation run:

- `python -m unittest discover -s tests -v` — PASS, 13 tests;
- `python scripts/validate-scene-alignment.py templates/set-anchors.json` — PASS structural geometry, explicitly not visual validation;
- `python scripts/validate-baselines.py baselines/registry.json` — PASS with zero promoted baselines, intentionally.

## Baseline decision

No B-series baseline was created in this pass.

Reason: the shared geometry relationships are structurally validated, but the actual corrected production renderer has not yet produced a visually reviewed artifact with validated floor/portal measurements. Promoting `B1` now would overstate the evidence.

## Next evidence gate

Connect the actual 2D renderer to the shared geometry layer, render the corrected reference scene, inspect floor contact and portal alignment, refine measurements, obtain user review, then decide whether the state is strong enough to promote as `B1`.
