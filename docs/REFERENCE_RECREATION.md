# Reference recreation — source-aligned production route

This is the correct repository's *supplemental* route for explicitly requested
replications of an uploaded video. It is not a new video renderer or competing
release controller. The normal studio workflow, `shotctl`, `productionctl`,
assistant creative/studio review, and final user-acceptance gate remain
authoritative. Do **not** use this on original films merely inspired by a style.

## 1. Inspect the uploaded video before choosing a renderer

Inspect the **entire moving reference**, not isolated thumbnails, and distinguish
the true creative area from phone UI/player chrome. Visually verify an exact
`W:H:X:Y` crop in source pixels, even for full-frame content. Note the source's
actual aspect, frame rate, audio, typography, camera/motion language, transitions,
scene ordering and intended timing changes.

Create a shot map of explicit source intervals and exact target frame intervals:

```json
[
  {
    "id": "opening",
    "source_start_seconds": 0,
    "source_end_seconds": 2,
    "target_start_frame": 0,
    "target_end_frame": 60,
    "complexity": "high",
    "visual_intent": "Authored kinetic opening and primary shape morph"
  },
  {
    "id": "ending",
    "source_start_seconds": 2,
    "source_end_seconds": 4,
    "target_start_frame": 60,
    "target_end_frame": 120,
    "complexity": "normal",
    "visual_intent": "Brand reveal with composed final composition"
  }
]
```

The example assumes 30 fps / 4 seconds: replace all values with observations
from the **actual** user's reference and delivery request. Intervals are half-open
target frame ranges, must tile the full film without gaps or overlaps, and
source intervals must remain ordered. Major source trims or intentional aspect
changes require an explicit documented production decision.

## 2. Lock reference geometry and timing

```sh
python scripts/referencectl.py lock \
  --reference /absolute/path/to/source.mp4 \
  --crop W:H:X:Y --crop-verified \
  --shots work/film/shot-map.json \
  --width 1920 --height 1080 --fps 30/1 --duration 20 \
  --out work/film/reference-lock.json

python scripts/referencectl.py verify --lock work/film/reference-lock.json
```

The lock binds the actual input's SHA-256, verified crop, creative aspect,
audio presence, target dimensions/duration/FPS and exact shot intervals.
Any changed source bytes, undocumented greater-than-0.5% aspect discrepancy,
missing soundtrack, or invalid timeline are surfaced. An explicit
`--aspect-override-reason` or `--audio-override-reason` records a genuine
exception; it cannot be used to ignore the user's stated requirements.

A valid lock **does not** imply creative accuracy, permission to redistribute
a reference soundtrack, or studio approval.

## 3. Use this repo's established rendering/review system

Use `scripts/shotctl.py` for shot-specific previews, motion proofs and
hash-bound repair. Choose Canvas, Blender, FFmpeg, local geometry, sourced assets,
or another audited renderer based on the reference's actual difficult
animation mechanisms. Do not downgrade a cinematic scene to flat titles
just because the geometry and duration are easy to match.

Use `productionctl.py` for immutable candidate iterations and its existing
technical, assistant and final-user review gates. The reference lock and
comparison report belong **alongside** the production's other evidence; they do
not automatically change `productionctl` state or declare a candidate DONE.

## 4. Compare exact encoded candidates, repair specific scenes

```sh
python scripts/referencectl.py compare \
  --lock work/film/reference-lock.json \
  --candidate work/film/candidate.mp4 \
  --board work/film/source-vs-candidate.jpg \
  --out work/film/reference-comparison.json
```

The comparison runs the canonical `src/core/media.validate_master` technical
QA, checks output geometry/FPS/duration/audio, decodes six proportionally aligned
frame pairs **per shot**, and reports per-shot luma difference, activity and
repair priority. It also checks source/candidate cut strength at locked
boundaries. The contact board shows midpoint pairs of each source/candidate shot.

The numerical values are only **diagnostics**: synthetic score improvements
do not establish artistic fidelity. Frame samples cannot assess detailed
letter motion, full camera choreography, motion blur, real-world acting, or
audio aesthetics. The source and final MP4 still require side-by-side
**normal-speed review** and targeted corrections. If that review was not
actually performed, explicitly mark it unavailable. Do not forge assistant or
user approval.

When a mismatch is found, update the relevant shot source/animation and
rerun the existing shot-specific proof/repair path; do not rerender unrelated
shots. Preserve failed versions as learning evidence, but do not promote them
to accepted cinematic baselines.

## 5. Audio and provenance

The reference's original soundtrack and source-derived stills are not
automatically cleared for redistribution. Track whether audio was
licensed/imported, Deepgram narration, native Earshot sound effects, or
original procedural/recorded audio. Follow
[Audio provider routing](AUDIO_PROVIDER_ROUTING.md); the primary A/V clock
is still `src/core/av_timeline.py`.

## Limits

The tooling does not infer a source's intended crop or automatically segment
shots, and it does not create any artistic approval. It is specifically a
reference-aware inspection and repair aid adapted to this repo's architecture.
Run `python -m pytest -q tests/test_reference_alignment.py` to verify real
source/candidate codec, crop, frame-map and fail-closed scenarios.
