# Asset Commons and Catalog

This directory is the durable metadata/control plane for reusable production assets.

- `catalog.json` records source, license, compatibility, tags, distribution mode and optional local hints.
- `core-manifest.json` records what is intentionally considered for the small always-available Core Commons.
- `local-state.json` is machine-specific and ignored by Git. Generate it with `python scripts/assetctl.py scan-local`.
- `core/payload/` is local payload storage and ignored by Git. Do not commit bulk assets just because their license permits redistribution.
- production-specific downloads belong to a goal pack or the production package with provenance.

Use `python scripts/assetctl.py validate` before accepting catalog changes. Use `search`, `list`, `status`, and `scan-local` to answer what exists before downloading or rebuilding assets.
