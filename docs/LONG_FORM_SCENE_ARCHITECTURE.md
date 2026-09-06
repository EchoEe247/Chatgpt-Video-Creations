# Long-Form Scene Architecture

## Principle

Long-form animation is a master production assembled from independently rendered scenes.

The goal is to preserve the richer short-scene quality baseline instead of simplifying animation solely to survive a long single render.

## Master timeline

Before rendering, define the whole episode/video:

- exact duration target;
- scene order and time ranges;
- dialogue/master audio positions;
- music/ambience continuity;
- character/set continuity state;
- transitions and camera intent.

Each scene receives its timeline range and continuity input.

## Independent scene render

Recommended scene lengths:

- 2D: commonly 5–15 seconds;
- 3D: commonly 4–12 seconds;
- business motion: may be longer when complexity is low.

These are production guidance, not hard caps.

Each scene should render with the appropriate quality FPS/resolution rather than inheriting a lower whole-video compromise.

## Handles

For transitions or continuous action, render extra handle frames when useful. Example:

- intended Scene A: 00:18–00:27;
- render: 00:17.5–00:27.5;

Use the overlap to choose a clean cut or verify deterministic continuity.

## Master audio

Prefer one continuous master audio timeline for dialogue, ambience, music and cross-scene SFX. Individual visual scene files can then be replaced without restarting or drifting the audio bed.

## Scene QA

Before final assembly:

- decode succeeds;
- duration/FPS match scene spec;
- starting/ending continuity states are correct;
- no floor/effect anchor drift;
- dialogue acting and subtitle timing are correct;
- no clipped props/characters unless intentionally framed.

## Assembly

Use exact scene ordering and avoid unnecessary re-encoding when formats match. After assembly, inspect all scene seams plus representative interior frames.

## Repair advantage

If Scene 6 fails, replace Scene 6. Do not rerender Scenes 1–5 and 7–12 unless a shared asset/continuity change genuinely requires it.
