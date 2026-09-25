# Scripts

Use the narrowest entry point that matches the task.

- `productionctl.py` — restart-safe production controller. Persists Local Workspace render-job identity, copies candidates into immutable iteration directories, binds QA to candidate SHA-256, reconciles interrupted jobs, tracks repair history/budget, and verifies evidence again before final acceptance.
- `videoctl.py` — media inspection/QA primitives: probe, strict decode, loudness/silence analysis, frames, contact sheets, full-runtime baseline comparison, codec/pixel/audio delivery checks, receipts, and review packs.
- `assemble-scenes.py` — assembles only the explicit ordered scenes listed in an assembly manifest. It rejects missing/duplicate inputs, output-as-input collisions, stream incompatibility, optional SHA mismatches, and duration mismatches before concat-copy and master decode verification.
- `validate-production-v2.py` — production package schema/gate validation.
- `validate-scene-plan.py` — scene timeline/review-point validation.
- `validate-continuity.py` — episode continuity-state validation.
- `validate-scene-alignment.py` — structural shared-geometry validation.
- `validate-baselines.py` — B-series registry validation.
- `render-2d-geometry-candidate*.py` — preserved reproducible geometry baseline renderers.

For ChatGPT/Local Workspace work, long render commands should normally be started through the plugin's persisted background-job tools. Record the returned job ID immediately with `productionctl.py rendering`, then reconcile it after every interruption/resume.

Use `templates/scene-assembly.json` as the starting point for long-form assembly. Do not replace it with a directory sweep.
