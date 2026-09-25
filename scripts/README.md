# Scripts

Use the narrowest entry point that matches the task.

- `productionctl.py` — production state machine, deterministic QA gate, repair history/budget, blockers, and final user acceptance transition.
- `videoctl.py` — media inspection/QA primitives: probe, decode, audio, frames, contact sheets, baseline comparison, receipts, and review packs.
- `assemble-scenes.py` — compatibility-checked long-form scene concatenation plus master decode verification.
- `validate-production-v2.py` — production package schema/gate validation.
- `validate-scene-plan.py` — scene timeline/review-point validation.
- `validate-continuity.py` — episode continuity-state validation.
- `validate-scene-alignment.py` — structural shared-geometry validation.
- `validate-baselines.py` — B-series registry validation.
- `render-2d-geometry-candidate*.py` — preserved reproducible geometry baseline renderers.

For ChatGPT/Local Workspace work, long render commands should normally be started through the plugin's persisted background-job tools. The scripts define reproducible behavior; Local Workspace supplies execution, observation, and recovery.
