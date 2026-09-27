# Asset Commons and Catalog

This directory is the durable metadata/control plane for reusable production assets.

- `catalog.json` records source, license, compatibility, tags, distribution mode and optional local hints.
- `core-manifest.json` records what is intentionally considered for the small always-available Core Commons.
- `local-state.json` is machine-specific and ignored by Git. Generate it with `python scripts/assetctl.py scan-local`.
- `core/payload/` is local payload storage and ignored by Git. Do not commit bulk assets just because their license permits redistribution.
- production-specific downloads belong to a goal pack or the production package with provenance.

Use `python scripts/assetctl.py validate` before accepting catalog changes. Use `search`, `list`, `status`, and `scan-local` to answer what exists before downloading or rebuilding assets.

## Audio commons

`audio-commons.json` is the tracked manifest for the tiny deterministic procedural fallback pack. The WAV payload lives under ignored `core/payload/audio-procedural/` and can be recreated exactly with:

    python scripts/audioctl.py build-commons
    python scripts/audioctl.py commons-status

Use the asset catalog before acquiring more sound. Keep large/specialized libraries goal-specific.
