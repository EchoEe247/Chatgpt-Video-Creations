# 2D Geometry Candidate 001 Receipt — 2026-09-06

## Purpose

Exercise the shared 2D geometry layer in an actual rendered MP4 before promoting any production measurements into a B-series validated baseline.

This is a **candidate validation artifact**, not `B1`.

## Reproducible source state

Renderer/config commit: `4c2b03064d9a5552ff8409a4d44907decbec5d39`

Relevant sources:

- `src/core/geometry.py`
- `src/animation_2d/layout.py`
- `candidates/2d-geometry-001/set.json`
- `scripts/render-2d-geometry-candidate.py`

The renderer imports the shared geometry/layout code rather than maintaining separate scene-coordinate tables.

## Candidate geometry

Canvas:

- 1280×720
- top-left origin
- +X right
- +Y down
- pixel units

Candidate set measurements:

- floor/contact plane: `y = 613`
- Dr. Vex standing anchor: `(338, 613)`
- Milo standing anchor: `(650, 613)`
- portal center: `(1035, 340)`
- portal outer radius: `165`
- portal inner radius: `132`

These numbers remain candidate measurements until user review passes. They are not general project constants.

## Render conditions

Artifact: `2d_geometry_candidate_001.mp4`

- duration: 8.000 s
- resolution: 1280×720
- frame rate: 24 FPS
- codec: H.264
- pixel format: yuv420p
- audio: none; this candidate validates spatial composition, not audio behavior
- file size: 1,868,437 bytes
- SHA-256: `00c699ca7a8cf3590557e8ee8de7c0145573e12026a6d052368aba2b5f108b20`

Representative contact sheet: `2d_geometry_candidate_001_contact_v2.jpg`

- SHA-256: `4005d7830449a1ade01f38c73907637d53ffc4cb1bad3ddd69f95ad8311db278`

The portable renderer reproduced the exact same MP4 SHA-256 in a second local run.

## What the candidate exercised

The 8-second render moves through multiple camera origins/scales and returns to the full composition.

The render intentionally exercises:

- standing-character placement through local foot/contact anchors;
- one set-owned floor/contact plane;
- portal hardware and green energy derived from one portal geometry definition;
- shared world-to-screen camera transforms;
- character animation above the feet without changing the contact anchor;
- diagnostic foot markers and portal-center crosshair at the beginning/end.

## Assistant review

Status: **PASS for the narrow geometry-candidate claim**.

Visual review of representative frames found:

- both characters' shoe/contact points remain on the transformed floor/contact line through the tested camera sequence;
- character scaling follows camera scaling without introducing visible floating;
- portal green energy remains concentric with the physical frame through the tested camera sequence;
- the portal frame and energy move/scale together rather than drifting through independent coordinates;
- the revised camera path keeps the floor/contact area visible enough to inspect during the zoomed states.

Technical review passed the expected H.264/1280×720/24 FPS/yuv420p output conditions.

## What this does not validate

This candidate does **not** yet validate:

- user acceptance of the candidate measurements;
- final episode/show art direction;
- safe-zone or text-safe values;
- preferred character scale ranges by shot type;
- full production z-order/layer rules;
- scenery clipping rules;
- all pose-specific contact anchors;
- the prior long-form episode renderer itself;
- audio/dialogue/subtitle timing;
- 3D composition behavior;
- business-video composition rules.

## Baseline decision

No B-series baseline is promoted by this receipt.

The candidate has passed assistant technical/visual review for its narrow geometry claim, but user review is still required before these exact candidate measurements can be treated as a trusted visual baseline.

If user review passes, the next step is to decide whether the evidence is sufficient for `B1`, preserve the accepted artifact/provenance, and update the baseline registry. If user review identifies a defect, keep this candidate as evidence, refine the specific measurement/relationship, rerender, and compare rather than starting over.
