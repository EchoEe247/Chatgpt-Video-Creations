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

### Pass-ingestion optimization

The initial Phase 4 blocker was OpenImageIO's `ImageBufAlgo.channels()` path on the Pixel/PRoot runtime. The original evidence was:

- `oiiotool` beauty extraction: about 16.42 seconds for one 720p multilayer EXR;
- pass-aware benchmark preview: 16.92 and 15.51 seconds for the first two frames.

The worker now opens each EXR with `ImageInput`, calls `read_image()` exactly once, and slices beauty/depth/emission/Cryptomatte data from the resident NumPy array. No persistent sidecar cache is required for this workload.

Measured after the change:

- one full 26-channel EXR decode: 0.336 seconds;
- 18-frame beauty-baseline worker: 2.73 seconds/frame average;
- 18-frame pass-aware worker: 2.75 seconds/frame average;
- pass-aware frame range: 2.34–3.40 seconds/frame;
- relative to the original two-frame pass-aware mean, end-to-end pass-aware throughput improved by about 5.9×.

The representative 18-frame A/B/C benchmark completed in about 128.5 seconds including both finishing arms, conventional post, MP4 assembly, pixel-delta calculation, and the existing creative B→C compare.

A direct production-path smoke through `finishingctl.py apply` also passed on five frames. The optimized worker produced verified finished EXR/PNG receipts, and the first two optimized PNG outputs are byte-for-byte hash-identical to outputs generated before the readback optimization. The speed change therefore did not alter the deterministic finishing math.

### Completed A/B/C evidence

The decisive benchmark is now complete at native cadence:

- 18 frames per arm;
- 1280×720;
- 24 fps;
- exactly 0.75 seconds for container, video, and silent audio on A, B, and C;
- B→C width/height match: PASS;
- B→C fps delta: 0;
- B→C duration delta: 0;
- B and C freeze detections: 0;
- B and C black-frame detections: 0;
- sampled B→C SSIM: 0.942526;
- existing creative compare: the single authored shot is consistently changed, with mean visual delta about 0.05008.

SSIM and pixel deltas are descriptive evidence only. They prove that the pass-aware arm is materially different from conventional post; they do not establish that it is aesthetically better.

The benchmark harness also now binds review-media duration to `frame_count / fps`. This fixed an AAC-padding artifact that previously made A/B containers report 0.981 seconds even though their video streams contained the correct 18 frames.

### Perception boundary and default-policy decision

The current ChatGPT route reports continuous-video perception as UNAVAILABLE. Sampled temporal evidence, decode checks, motion analysis, and the existing creative compare can verify structure and obvious defects, but they are not equivalent to genuine normal-speed aesthetic viewing.

No deterministic finishing processor is therefore promoted to a production default from Phase 4:

- `depth_atmosphere`: remains experimental/opt-in;
- `emission_rebalance`: remains experimental/opt-in;
- `selective_grade`: remains experimental/opt-in;
- `display_transform`: remains a diagnostic MVP transform, not the final cinematic color target.

This is no longer blocked by engineering throughput. It is blocked only on trustworthy perceptual/user judgment about whether B or C is the stronger image.

The durable Phase 4 fixtures are `scripts/blender_phase4_cinematic_fixture.py`, `scripts/prepare_phase4_benchmark.py`, `scripts/finishing_benchmark_worker.py`, and the single-decode path in `scripts/finishing_worker.py`.

## Phone review handoff

Finishing comparisons must be practically reviewable on the phone before asking for a user quality judgment.

Generate the synchronized B/C page:

```bash
python scripts/make_finishing_review.py \
  path/to/arm-b.mp4 path/to/arm-c.mp4 path/to/review/index.html \
  --title "Finishing review - B conventional vs C pass-aware" \
  --fps 24
```

Serve the review directory with byte-range support:

```bash
python scripts/range_server.py --root path/to/review-directory --port 8878
```

The page preserves native HTML5 controls and adds a shared unlocked scrubber, synchronized playback, ±1-frame stepping, 0.5×/1× playback, B-only, C-only and split modes, current-time/frame diagnostics, and direct MP4 links. The range server returns HTTP 206 for valid Range requests so Android Chromium can seek, rewind and jump without linear replay.

The page defaults to C-only on narrow displays so the image is large enough to inspect; B-only and Split remain one tap away.

## C2 micro-tune and 3-second validation

User review established current C as usable and preferred over the darker conventional B arm, with a request to test a slightly darker version. C remains preserved as the accepted baseline.

C2 is a separate recipe variant. It changes exactly one value:

- final display exposure: `+0.25 → +0.15` stops.

All depth-atmosphere, emission-rebalance and protected-subject selective-grade settings remain identical to C. Tests enforce that this is the only recipe-level change.

The 1.5-second C-versus-C2 pair is structurally matched at 1280×720, 24 fps, 36 frames and 1.5 seconds. Their sampled SSIM is 0.988294, confirming that C2 is a deliberately small visual adjustment rather than a new look. The phone review generator now accepts custom arm labels so C/C2 comparisons are unambiguous.

### Longer native-cadence validation

The representative cinematic fixture was extended from 48 to 72 authored frames with continued hero travel and camera motion; no frame interpolation or clip stretching is used.

The 72-frame / 3.0-second render completed locally with:

- 1280×720 at native 24 fps;
- Cycles CPU, one sample;
- 72/72 multilayer EXR frames;
- average render time: 6.53 seconds/frame;
- render-time range: 4.29–10.30 seconds/frame;
- average EXR size: 7.80 MiB/frame;
- total EXR payload: 561.4 MiB;
- peak reported process RSS: 517 MiB;
- exact-file Render Bundle + C2 recipe validation: PASS.

C2 finishing completed for all 72 frames. The encoded validation master is exactly 72 frames, 24 fps and 3.0 seconds. Strict decode passes, with zero detected freeze segments and zero black-frame segments.

This proves the current deterministic finishing architecture is stable across a longer continuously moving shot. It does **not** by itself promote C2 over C aesthetically; that remains a user/perceptual decision.

## Authoritative AgX / OCIO display path

The deterministic finisher now has an **opt-in** `agx_display_transform` processor. It does not approximate AgX in NumPy. It calls OpenImageIO's `ImageBufAlgo.ociodisplay()` against Blender's own installed OpenColorIO configuration:

- config: `/usr/share/blender/datafiles/colormanagement/config.ocio`;
- display: `sRGB`;
- view: `AgX`;
- source space: `Linear Rec.709`;
- look: none by default.

The recipe binds the exact runtime color assets:

- OCIO config SHA-256: `6a28581e9b567c42d752d8f2d7487d0c516238632e1597e277ecdfa84fb4d1b9`;
- `AgX_Base_sRGB.cube` SHA-256: `e707a36f3e90ee79bc342332febf91334c02ce3974cac700ece00ca9d4507491`.

The worker refuses to apply AgX if either file is missing or its hash differs. This prevents silent color drift after Blender/runtime changes.

`prepare_phase4_benchmark.py` now emits two additional opt-in variants without mutating the existing recipes:

- `recipe-agx-c.json` — current C exposure with the diagnostic Reinhard transform replaced by Blender AgX;
- `recipe-agx-c2.json` — C2 exposure with the same authoritative AgX replacement.

C and C2 themselves remain unchanged.

### AgX verification

A five-frame same-exposure C-versus-C-AgX test from the 3-second validation source showed:

- width/height/fps/duration match: PASS;
- sampled SSIM: 0.964786;
- mean absolute RGB delta across the five frames: 0.043585;
- repeated AgX frame output: byte-identical SHA-256;
- production `finishingctl apply` smoke: PASS;
- production worker AgX operation time on the smoke frame: 0.647 seconds.

The direct OCIO display transform itself completed on a representative 720p frame in about 0.33 seconds. Longer benchmark-worker timings were sensitive to transient device load, so they are not used as the color-path performance baseline.

These measurements prove that the AgX path is real, structurally safe, deterministic, and usable in the production controller. They do **not** establish an aesthetic preference over C/C2.

## Next phase

Keep C and C2 unchanged while AgX remains opt-in. The next visual review should compare the selected C/C2 exposure against the corresponding AgX variant on a longer 3–5 second shot. If that review prefers AgX, promote `agx_display_transform` into the production preset and retire the diagnostic Reinhard transform. Model-backed/generative finishing remains deferred.
