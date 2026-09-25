# Core

Shared production infrastructure belongs here. CLI scripts should orchestrate these modules rather than reimplementing media or state logic.

Current modules:

- `geometry.py` — reusable 2D canvas/coordinate contract, camera transforms, set floor anchors, portal geometry, and sprite placement by local contact anchor.
- `fonts.py` — portable font discovery for Linux/Termux rendering.
- `media.py` — FFprobe/FFmpeg metadata, strict decode checks, validated loudness/silence analysis, frame/contact-sheet generation, delivery QA, artifact receipts, intentional-silence handling, and full-runtime sampled SSIM comparison.
- `review_pack.py` — one implementation for review receipts, contact sheets, scene-boundary frames, and declared review-point frames plus short motion/audio clips; it can reuse already-computed QA data instead of repeating probe/decode/audio work.
- `production_manifest.py` — production-v2 schema, delivery-profile, persisted-render-job, artifact-hash, and gate validation.
- `production_runtime.py` — autonomous workflow defaults, render-job reconciliation state, gate normalization, repair budget, final-review readiness, and next-action derivation.
- `scene_plan.py` — scene timeline/review-point validation before rendering.
- `baseline_registry.py` — formal B-series baseline metadata validation.

The core scene model keeps one set geometry authoritative so render lanes do not invent unrelated floor/effect/camera coordinates.

The runtime model keeps objective QA and repair inside the assistant workflow. A user-facing review should normally happen only after deterministic and assistant gates pass.

Production state is not trusted merely because paths are populated. The controller must verify candidate/evidence existence and SHA-256 bindings at the transition points that matter.

A structural or registry pass proves only the contract it actually tests; it does not replace rendered-media inspection or user acceptance where those are required.