# Final-Production Quality Floor

## Purpose

A technically valid video is not automatically a production-quality video.

This contract exists to prevent a fresh session from silently downgrading a user-facing cinematic goal into a cheap proxy implementation and then relying on technical QA to justify delivery.

The quality floor is enforced twice:

1. **director/execution plan** — decide what kind of production this is and prove the expensive path is justified before rendering;
2. **production controller** — refuse final rendering/review when the bound execution plan or review requirements do not satisfy that floor.

## Required director declaration

New director briefs use:

```json
"quality_floor": {
  "delivery_level": "final",
  "visual_mode": "cinematic_3d",
  "character_mode": "performance",
  "environment_mode": "spatial",
  "proxy_assets_allowed": false,
  "minimum_delivery_height": 720,
  "notes": ""
}
```

Allowed values:

- `delivery_level`: `final`, `prototype`, `unresolved`;
- `visual_mode`: `cinematic_3d`, `stylized_2d`, `motion_graphics`, `unresolved`;
- `character_mode`: `none`, `incidental`, `performance`, `unresolved`;
- `environment_mode`: `graphic`, `spatial`, `unresolved`.

`unresolved` is a blocker. Do not choose a cheaper mode merely because it is easier to render. The mode must describe the user's actual target.

## Final vs prototype

`prototype` is allowed for experiments, smoke tests, blocking and previews. It can become execution-ready, but it is never `final_delivery_ready`.

A prototype must not be presented as the final user-facing candidate.

`final` activates the quality-floor checks below.

## Final cinematic 3D

A `final + cinematic_3d` plan cannot be execution-ready unless:

- proxies are not allowed in the final;
- delivery height meets the declared minimum;
- moving previs is explicitly `required`, `approved`, and has a declared artifact;
- look-dev is explicitly `required`, `approved`, and has a declared artifact;
- at least one Blender renderer lane is actually used;
- performance characters have an explicit `character` asset requirement;
- spatial environments have an explicit `environment` asset requirement;
- the relevant character/environment requirement has a concrete `proof_artifact`.

Notes cannot waive these checks. Marking previs or look-dev `not_required` does not satisfy a final cinematic-3D plan.

## Semantic motion and environment completeness

The structural checks above are necessary but not sufficient. Final cinematic 3D also has two manual fail-closed review requirements:

- **semantic motion** — the subject's modeled forward axis, world-space travel vector, screen direction, camera motion, configuration changes, contact events and expected kinematics must agree. A car, aircraft or character that visibly reads as traveling backward or sliding incorrectly fails even when motion/freeze metrics report activity;
- **environment completeness** — the spatial environment must look production-complete from the actual hero/wide/landing/action cameras. A declared environment asset, valid geometry and successful render do not pass if the world still reads as sparse blockout, missing expected airport/city/set structure, or unfinished background dressing.

These are currently evidence-backed review requirements even where they are not represented by a single compiler field. Previs is the earliest gate for motion semantics; representative look-dev is the earliest gate for environment completeness; final candidate review rechecks both on the encoded film.

Automated motion-density, freeze, decode, hash and asset-presence checks cannot certify either property.

## Asset proof

`proof_artifact` is evidence that the high-impact noun is real and production-usable rather than an intention.

Examples:

- a downloaded/adapted rigged character or its production provenance/inspection receipt;
- a locally authored character-rig proof;
- an adapted environment scene/package receipt;
- a representative asset integration proof.

The director compiler requires the field for performance characters and spatial environments under the final quality floor. Before final rendering, `productionctl` verifies that the referenced proof actually exists on disk.

A provider catalog entry such as Mixamo is not the proof. The selected/acquired character or production evidence is.

## Visual-development artifacts must exist

The compiler checks the declared decisions. The production controller checks the actual files.

For `workflow.quality_floor_required=true`, final `render-spec`, `rendering`, `prepare-review`, `assistant-pass`, and `user-accept` verify the bound execution plan and its source hashes. Required previs/look-dev artifacts and asset proof artifacts must still exist.

This prevents a session from typing `status: approved` around a nonexistent preview.

## Audio and full studio review

New production manifests default to:

```json
"quality_floor_required": true,
"creative_qa_required": true,
"studio_review_required": true
```

For a final quality-floor production with required audio, `studio_review_required=false` is a hard preflight failure.

The existing studio final-screening contract then requires auditory and synchronized-A/V review for audio-required deliveries. Audio measurements, waveform plots, silence detection, or a successful encode do not substitute for hearing the candidate.

Use the validated auditory perception route and `media_audio_listen_clip` when making subjective listening claims. See `docs/STUDIO_REVIEW_CONTRACT.md` and `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`.

## Renderer suitability

Renderer choice is part of quality, not merely technical availability.

A final cinematic-3D plan cannot be implemented entirely through Python/Pillow or Canvas and still satisfy the `cinematic_3d` quality floor. Programmatic renderers remain valid for motion graphics, stylized 2D, overlays, diagnostics and prototypes.

This does not mean every cinematic shot must be Blender. UI inserts, compositing and other purpose-built lanes may coexist with Blender. The rule prevents replacing the entire spatial/character production with a cheap programmatic approximation.

## The rejected regression case

`tests/fixtures/eighth-hour-quality-regression.json` preserves the failure shape that triggered this contract:

- final cinematic/character-heavy goal;
- proxy-like author-local visual world;
- no explicit character production asset;
- no environment proof;
- previs marked not required;
- look-dev marked not required;
- all-Python/Pillow rendering.

The regression test must remain blocked for independent reasons. A future refactor that makes this fixture execution-ready is a workflow regression.

Recent cinematic failures add two additional regression shapes that must remain visible in review even when technical QA is green: an incomplete spatial world presented as finished, and a moving hero whose direction/kinematics read incorrectly. See `docs/REFERENCE_SAMPLES.md`.

## Production-controller boundary

For new user-facing productions:

**workflow bootstrap → director quality floor → asset proof → previs → look-dev → execution-ready plan → productionctl render preflight → shot/scene render → candidate QA → mandatory studio screening → user review**

Do not route around this by manually setting production state fields. `productionctl` is the state authority.

## Backward compatibility

Historical plans without `quality_floor` still compile as legacy material so old evidence can be inspected.

They are not considered final-delivery ready under the new contract. New manifests opt into strict enforcement with `workflow.quality_floor_required=true`.
