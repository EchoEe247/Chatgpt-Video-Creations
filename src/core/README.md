# Core

Shared production infrastructure belongs here. CLI scripts should orchestrate these modules rather than reimplementing media or state logic.

Current modules:

- `geometry.py` — reusable 2D canvas/coordinate contract, camera transforms, set floor anchors, portal geometry, and sprite placement by local contact anchor.
- `fonts.py` — portable font discovery for Linux/Termux rendering.
- `media.py` — FFprobe/FFmpeg metadata, decode checks, audio analysis, frame/contact-sheet generation, master QA, artifact receipts, and baseline SSIM comparison.
- `review_pack.py` — one implementation for review receipts, contact sheets, scene-boundary frames, and declared review-point frames.
- `production_manifest.py` — production-v2 schema and gate validation.
- `production_runtime.py` — autonomous workflow defaults, gate normalization, repair budget, final-review readiness, and next-action derivation.
- `scene_plan.py` — scene timeline/review-point validation before rendering.
- `baseline_registry.py` — formal B-series baseline metadata validation.

The core scene model keeps one set geometry authoritative so render lanes do not invent unrelated floor/effect/camera coordinates.

The runtime model keeps objective QA and repair inside the assistant workflow. A user-facing review should normally happen only after deterministic and assistant gates pass.

A structural or registry pass proves only the contract it actually tests; it does not replace rendered-media inspection or user acceptance where those are required.
