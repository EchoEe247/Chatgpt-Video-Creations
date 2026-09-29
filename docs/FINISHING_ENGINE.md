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

## Phase 1 contract

Phase 1 is now implemented as a repository-native contract layer.

Use:

```bash
python scripts/finishingctl.py validate-bundle path/to/render-bundle.json
python scripts/finishingctl.py validate-recipe path/to/recipe.json
python scripts/finishingctl.py validate-pair path/to/render-bundle.json path/to/recipe.json
python scripts/finishingctl.py validate-pair path/to/render-bundle.json path/to/recipe.json --verify-files
```

Templates live under `templates/finishing/`.

The Render Bundle contract binds source scene/execution hashes, render dimensions/cadence/color state, canonical pass names to actual channels, exact frame paths/hashes/sizes/readback status, approved kinematics, protection semantics, allowed processor classes, and runtime metadata.

The Finishing Recipe contract enforces ordered scene-linear → display-referred processing, canonical input passes, protection-mask references, processor risk classes, deterministic randomness seeds, and additional justification/verification for Class G operations.

`validate-pair` checks the recipe against the exact bundle so a recipe cannot consume an absent pass/mask or use a processor class prohibited by the bundle policy. `--verify-files` additionally verifies referenced frame bytes and SHA-256 values.

Canonical JSON fingerprints identify the bundle and recipe definitions. Actual frame SHA-256 values remain separate evidence; an encoded MP4 hash is not used as deterministic source-frame identity.

## Phase 2 deterministic MVP

Phase 2 is implemented as a guarded local processor path.

Normal use:

```bash
python scripts/finishingctl.py doctor
python scripts/finishingctl.py apply \
  path/to/render-bundle.json \
  path/to/recipe.json \
  path/to/output-dir \
  --root path/to/bundle-root
```

`apply` validates the exact bundle, recipe, referenced source-frame bytes and policy before dispatch. It uses the shared shot/finishing device lock, runs the worker inside `hermes-ubuntu`, then validates the returned receipt and every finished-frame/preview hash.

The current deterministic processors are:

- `depth_atmosphere` — scene-linear depth-controlled atmospheric separation;
- `emission_rebalance` — scene-linear rebalance of the existing Emission contribution without inventing geometry;
- `selective_grade` — scene-linear exposure adjustment through a declared protection mask; the Phase 2 proof resolves the `Hero` Cryptomatte selector from the actual EXR manifest;
- `display_transform` — deterministic Reinhard + sRGB transfer used for the MVP review/delivery proof.

The first three operations demonstrate pass-aware control. The current display transform is deliberately simple and is **not** the final cinematic color target or a replacement for Blender/OCIO AgX-quality color management.

### Runtime dependency

The current worker uses Ubuntu's OpenImageIO Python binding and NumPy. The verified runtime has:

```bash
apt-get install openexr openimageio-tools python3-openimageio
```

`finishingctl doctor` fails cleanly when the guest processing dependency is unavailable.

### Deterministic-output rule

Finished EXRs set stable `DateTime` and `Software` metadata. OpenEXR writers otherwise stamp wall-clock time, causing different file hashes even when pixels are identical.

The Phase 2 proof rendered two independent output directories from the same exact bundle+recipe and obtained identical SHA-256 hashes for every lossless EXR and every PNG preview. A subsequent in-place run skipped all verified frames.

The lossless artifact hash remains the authoritative finished-frame identity; the encoded comparison MP4 is review evidence, not the deterministic source identity.

### Phase 2 measured proof

The proof used the real animated Phase 0 multilayer EXRs at 1280×720.

- validated Render Bundle fingerprint: `8884410991cf4c3c581f1af9c27fa231c2a911c65092790dbf9cce277564cb55`;
- validated Recipe fingerprint: `6f382c1f28236bf6fe8f6be61fce674fc57c846be2b6d2513dcd6714313ebdad`;
- finished-frame processing time in the final proof: 0.333 s, 0.354 s and 0.320 s;
- Hero Cryptomatte middle-frame region: 84,768 pixels above 0.5 coverage, maximum coverage 1.0;
- baseline-versus-finished middle-frame mean absolute RGB delta: approximately 0.0616;
- independent replay: bit-identical lossless and preview hashes;
- resume: verified existing outputs are skipped.

This remains a capability/architecture proof, not a cinematic-quality benchmark.

## Phase 3 production binding and benchmark harness

Phase 3 is implemented in two deliberately separate pieces.

### Candidate provenance binding

`productionctl.py candidate` accepts an optional all-or-nothing finishing triplet:

```bash
python scripts/productionctl.py candidate production.json candidate.mp4 \
  --finishing-bundle path/to/render-bundle.json \
  --finishing-recipe path/to/recipe.json \
  --finishing-receipt path/to/finishing-receipt.json
```

When supplied, the controller validates the Render Bundle, Finishing Recipe, exact bundle/recipe compatibility, source-frame hashes, Finishing Receipt, and finished output hashes before mutating production state.

It then copies the small bundle/recipe/receipt evidence into the immutable iteration directory and records `artifacts.finishing_provenance` with the candidate SHA-256, canonical bundle and recipe fingerprints, copied file SHA-256 values, a canonical finished-frame manifest SHA-256, and an immutable provenance-file SHA-256.

The finished-frame manifest records frame number plus source, lossless-finished, and preview hashes. Bulk EXR payloads remain outside Git and outside the production manifest.

A new candidate clears prior finishing provenance exactly like other candidate-bound evidence. `repair-start` archives the prior iteration and increments the existing repair cycle; finishing-only repair does not get a parallel free retry budget.

### Three-arm benchmark harness

`scripts/finishing_benchmark.py` starts from one validated Render Bundle plus the full pass-aware recipe and constructs the three arms under identical source geometry:

- A = Blender beauty plus only the recipe's shared display transform;
- B = A plus a deterministic conventional FFmpeg curves/contrast/saturation/vignette treatment;
- C = the full pass-aware finishing recipe.

It encodes all three review arms at the same cadence, adds silent audio so the existing creative comparison path can run without special cases, creates an A/B/C triptych, and records per-frame A→B, B→C, and A→C pixel deltas.

When `--execution-plan` is supplied, the benchmark also calls the existing `creativeqactl compare` path for B→C and records the resulting `iteration-compare.json` hash. That reuses the current shot-aware comparison machinery instead of introducing a second QA system.

The receipt is descriptive only. It does not score or automatically choose a preferred arm. Cinematic quality still requires normal-speed perceptual review.

Example:

```bash
python scripts/finishing_benchmark.py \
  render-bundle.json pass-aware-recipe.json benchmark-output/ \
  --root bundle-root/ \
  --execution-plan execution-plan.json
```

The Phase 3 fixture proof generated all three arms successfully and reused the existing B→C creative compare. On that deliberately tiny fixture, the B→C comparison marked its only shot as changed; this proves the benchmark plumbing, not a quality preference.

### Current boundary

Phase 3 provides the production-state binding and reusable benchmark machinery. It does not claim that the Phase 0 fixture establishes a cinematic-quality gain. The real longer cinematic A/B/C benchmark should use a representative shot, native cadence, the normal creative QA evidence path, and perceptual review.

## Phase 4 representative benchmark result

Phase 4 produced a representative 1280×720, native-24-fps cinematic Blender fixture with camera parallax, a moving Cryptomatte-protected subject, metallic surfaces, emissive practicals, foreground occlusion and meaningful depth.

The first attempt reused SECOND EARTH's full physical-lab scene. That path was abandoned after a 720p Eevee smoke frame exceeded roughly three minutes on the Pixel/PRoot runtime. The useful lesson is renderer-specific: on this device, software Eevee is not automatically the fast lane.

The replacement fixture uses Cycles CPU at one sample. It successfully rendered 36 consecutive native frames:

- average render time: 9.97 seconds/frame;
- range: 6.50–12.97 seconds/frame;
- average multilayer EXR size: 7.99 MiB/frame;
- 36-frame payload: 287.5 MiB;
- peak reported process RSS: 482.5 MiB;
- required beauty, depth, normal, emission, AO and object-Cryptomatte channels were present.

The resulting full Render Bundle and pass-aware recipe validated with exact file hashes. This establishes that a representative native-cadence render is locally feasible.

### Finishing-throughput blocker

The normal-speed A/B/C review could **not** be completed within the local benchmark budget because multilayer-EXR readback/post became slower than rendering:

- OpenImageIO CLI beauty extraction measured about 16.4 seconds for one 720p Cycles EXR;
- the pass-aware PNG-only benchmark worker measured 16.92 seconds for its first frame and 15.51 seconds for its second;
- a full A + C 18-frame review would therefore spend several additional minutes primarily decoding/post-processing EXRs, before review encoding and QA.

This is now the active bottleneck. The next optimization target is not Blender render speed; it is pass-readback/cache throughput.

The current route also reports continuous-video perception as UNAVAILABLE, so this phase does not claim direct model perception of normal-speed playback. Existing QA and sampled evidence remain valid, but they are not a substitute for claiming genuine continuous playback review.

### Partial A/B/C evidence

Two completed representative frames were compared:

- conventional post B versus beauty A mean RGB delta: approximately 0.0107;
- pass-aware C versus conventional B mean RGB delta: approximately 0.0403;
- pass-aware C versus beauty A mean RGB delta: approximately 0.0314.

This proves that pass-aware processing makes a materially different image, but pixel distance does not establish that the difference is better.

### Default-policy decision

No deterministic finishing processor is promoted to a production default from Phase 4.

- `depth_atmosphere`: remains experimental/opt-in;
- `emission_rebalance`: remains experimental/opt-in;
- `selective_grade`: remains experimental/opt-in;
- `display_transform`: remains a diagnostic MVP transform, not the cinematic color target.

The reason is evidentiary, not conceptual: a full normal-speed B→C perceptual review has not yet been completed. The system must not turn an incomplete benchmark into a quality policy.

The durable Phase 4 fixtures are `scripts/blender_phase4_cinematic_fixture.py`, `scripts/prepare_phase4_benchmark.py`, and the PNG-only `scripts/finishing_benchmark_worker.py`. The benchmark worker intentionally reuses the exact deterministic finishing math while avoiding unnecessary finished-EXR writes during review experiments.

## Next phase

Optimize local pass ingestion before attempting the full normal-speed benchmark again. Prefer a one-decode-per-frame cache or Blender-side extraction into only the required beauty/depth/emission/mask data, then rerun the same A/B/C harness. Do not promote processor defaults or add model-backed finishing until B→C can be reviewed at normal speed under a practical local runtime.
