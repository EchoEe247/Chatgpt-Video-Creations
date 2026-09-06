# B1 — 2D Geometry / Composition Baseline

Promoted: 2026-09-06

## Exact baseline state

Repository commit: `de7fe83c900491a84dc671a9e13f7fd186ea9371`

Lane: `2d`

This is the first formal B-series baseline. It promotes the user-accepted Candidate 002 geometry/composition state; it does not claim that every aspect of 2D animation is solved.

## Durable reviewed artifacts

Primary MP4:

- Google Drive file ID: `1twg27bMliRvF7VGShBvWRGwxo9MDzauP`
- file: `B1_2d_geometry_candidate_002.mp4`
- SHA-256: `0ba84767a393d55b01717b4a65de0e0c567ec59b7e64a0db0866f6fbbb9f41cf`

Representative contact sheet:

- Google Drive file ID: `1Sq8nvC4CZc7KqNr-OhqpwwPb7-5oVGU5`
- file: `B1_2d_geometry_candidate_002_contact.jpg`
- SHA-256: `02e6cfcfb5d535f8b243f1bda20aaaf345f316feeacb2c9a0c63bd8ba0f088e1`

The Drive folder is `Chatgpt-Video-Creations Baselines` (`12qE6o7QOHgSFuee_M3z9XnI8u7tbi-QH`).

## Render conditions

- canvas: 1280×720
- frame rate: 24 FPS
- duration: 8.0 seconds
- codec: H.264
- pixel format: yuv420p
- audio: intentionally none (`-an`)
- floor/contact plane: `y = 613`
- Vex standing anchor: `(338, 613)`
- Milo standing anchor: `(650, 613)`
- portal center: `(1035, 340)`
- portal outer radius: `165`
- portal inner radius: `132`

## What passed

Technical validation:

- renderer completed successfully;
- MP4 was produced at the stated canvas/frame rate;
- shared `SetGeometry` / `place_character` / `place_portal` code was used;
- character placement uses the rig-local foot anchor rather than sprite-bottom guessing;
- portal energy inherits the physical inner opening rather than a second coordinate table;
- the same camera transform drives related set geometry.

Visual review:

- character-to-floor positioning remained visually grounded during camera movement;
- green portal energy remained aligned/concentric with the gray/black physical portal frame during camera movement;
- the revised panel implementation fixed the unnatural word movement during zoom/pan by transforming each world-space board as one rendered object;
- the revised Vex hair silhouette was accepted as improved and usable for this candidate.

User review: **PASS**.

The user explicitly confirmed that the portal/alignment issues look great, then approved Candidate 002 after the wording motion and hair refinements.

## Intentional silence

Candidate 002 has no voice or other audio by design. This render was a geometry/composition validation artifact, not a dialogue/audio test. The lack of an audio stream is therefore not a defect and is not part of the B1 capability claim.

## Known limitations / not validated

B1 does not establish:

- voice quality, dialogue timing, sound effects, music, or audio mixing;
- a final character-art style for future original shows;
- universal character scale ranges for every shot type;
- action-safe or text-safe margins for all productions;
- a complete reusable camera preset library;
- full z-order rules for every scene type;
- long-form episode animation quality;
- business-video or 3D-animation behavior.

The Vex hair design is accepted for this reference candidate, but future show character design remains a creative decision rather than a universal project rule.

## Regression use

If a later 2D composition candidate develops floating feet, portal drift, detached board text during camera motion, or another regression covered here, compare the new render and implementation against B1 before changing geometry by eye.

Do not replace B1 merely because newer code exists. Promote a newer baseline only after its claimed capabilities are genuinely validated.
