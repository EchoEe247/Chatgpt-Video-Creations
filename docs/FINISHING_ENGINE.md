# Local Blender Finishing Engine

## Scope

This document applies only when a Blender shot uses `multipass`, `hybrid`, or another explicitly finishing-enabled path. Beauty-only shots do not need this workflow.

The finishing engine extends the existing production chain:

**director brief → previs → look-dev → shotctl → Blender preview + optional render bundle → finishing → encoded candidate → existing QA/review**

It does not replace Blender, shotctl, productionctl, creative QA, studio review, or user quality promotion.

## Phase 0 feasibility gate

Before defining production Render Bundle schemas, the real Pixel/Termux runtime had to prove that useful Blender pass data can be produced, read back, measured, and resumed locally.

The checked-in proof uses:

- `scripts/blender_phase0_fixture.py` — animated 1280×720 Cycles fixture that writes one multilayer EXR per frame and resumes by skipping already valid frames;
- `scripts/finishing_phase0.py` — independent OpenImageIO readback that inventories actual EXR channels and measures motion-vector pixels;
- OpenEXR/OpenImageIO command-line tools installed inside `hermes-ubuntu`;
- runtime outputs under `.runtime/phase0-finishing/`;
- committed measurement receipt `receipts/2026-09-28-finishing-phase0.json`.

Phase 0 is capability/resource evidence, not a cinematic-quality benchmark.

## Verified Phase 0 result

The accepted local proof rendered three animated Cycles frames at 1280×720, 24 fps, one sample, with a representative hybrid pass set.

Measured on the actual local runtime:

- 49 EXR channels were independently read back;
- Combined, Depth, Normal, Vector, Emission and supporting channels were present;
- `ViewLayer.Vector.X/Y/Z/W` were present on the animated middle frame;
- vector statistics were materially non-zero;
- average render time was approximately 3.38 seconds per frame for this intentionally simple fixture;
- average multilayer EXR size was approximately 21.45 MiB per frame;
- peak reported process RSS was approximately 750 MiB;
- a second run skipped all three existing valid frames, proving idempotent frame-level resume for the fixture.

These numbers are not forecasts for production scenes. Real scenes must measure their own representative frame/range before committing to a full multipass render.

## Required local readback tools

The Phase 0 reader currently uses `oiiotool` from the Ubuntu `openimageio-tools` package and `exrheader` from the Ubuntu `openexr` package.

Do not treat a Blender pass flag as proof that a channel was written. Production validation must inspect the actual artifact.

The earlier static Eevee smoke demonstrated why: the vector pass flag could be enabled while the written static EXR contained no Vector channels. Animated Cycles Phase 0 output produced the required Vector channels and non-zero data.

## Render-bundle boundary

The normal `shotctl` adapter contract remains RGB preview frames. A future finishing-enabled Blender adapter extension may additionally emit a production Render Bundle for `multipass` or `hybrid` shots.

That bundle must eventually bind:

- source scene and execution-plan hashes;
- frame range, native cadence, resolution, renderer and color state;
- canonical pass names mapped to actual artifact channels;
- approved camera/kinematics facts such as forward axis and travel vector where relevant;
- protection semantics for masks/objects;
- per-frame paths, hashes, sizes and readback status;
- runtime/tool versions.

Bulk frame/pass payloads stay out of Git. Compact schemas, manifests and receipts may be committed.

## Protection semantics

Do not use an ambiguous `protected=true` flag. Finishing-aware masks/regions distinguish:

- `geometry_protected` — shape/position cannot move;
- `appearance_protected` — photometric treatment is constrained;
- `geometry_and_appearance_protected` — both are constrained.

Identity, orientation, travel direction and contact semantics remain Blender/previs facts. Finishing verification checks whether an operation could have violated them; it does not infer them from scratch from final pixels.

## Processor risk classes

- **Class P — photometric:** grade, exposure, saturation, grain. Must not move geometry.
- **Class S — spatial filtering:** bloom, halation, haze, blur. Requires protected-edge/mask-leak checks.
- **Class G — geometry/resampling:** distortion, interpolation, scaling, warping and future generative processing. Requires the strongest structural/temporal checks and is disabled by default unless justified.

## Native-cadence rule

Interpolation is finishing, not a substitute for native motion.

For serious camera/subject motion, native 24 fps remains the default final-quality target when practical. Lower native cadence is a constrained-runtime exception that must pass normal-speed review before interpolation is allowed. Existing LAX evidence shows that 6-fps-class source motion is not a reliable final-quality default.

## Color ordering

Finishing recipes must distinguish scene-linear and display-referred stages.

Scene-linear examples include depth atmosphere, emission manipulation, physically meaningful bloom/glare and lighting-pass recombination. Display-referred examples include final display contrast, grain, restrained vignette and delivery encoding preparation.

Do not reorder an operation across that boundary without changing the recipe revision.

## Restartability and resource control

Long local work must remain frame-addressable and restartable. Finished frames or pass files are immutable once verified; resume skips verified outputs and repairs only missing/invalid ones.

Heavy production rendering/finishing should reuse the existing `shotctl` device lock or an equivalent shared lock so concurrent memory-heavy jobs cannot collide.

Every real production must measure representative seconds/frame, bytes/frame, peak memory and projected disk use before a long multipass run.

## QA integration

The finishing engine creates no parallel acceptance path.

Reuse existing `creativeqactl compare` / `build_iteration_compare` for before/after review. A finishing-only rerun creates a new candidate hash and therefore regenerates candidate-bound evidence as required by the current workflow.

Finishing repair cycles participate in the existing autonomous repair budget unless the controller explicitly identifies a non-candidate diagnostic trial.

## Next phase

With Phase 0 passed, Phase 1 may define the Render Bundle and Finishing Recipe contracts and extend the existing Blender/shotctl path. Do not add model-backed/generative finishing until deterministic contracts and QA are stable.
