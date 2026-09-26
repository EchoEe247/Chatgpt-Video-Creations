# Blender Agent Action

Short comparison production used to validate the local agent-controlled Blender
video path.

## Current target

V5 keeps the V4 action timing at 4 seconds / 24 fps so visual improvements can
be compared without changing the basic story beat:

**run → plant/aim → two shots → target reaction**

V4 is the scratch-built proxy baseline. V5 replaces its proxy character and box
corridor with locally downloaded CC0 assets while keeping scene authorship,
animation assembly, lighting, cameras, VFX, audio timing, rendering, and QA in
this repository.

## Durable source

- `source/prepare_external_assets.py` fixes the downloaded MegaKit's shared
  texture references locally without copying texture payloads.
- `source/build_v5_asset_scene.py` builds the Blender scene from the declared
  local external assets.
- `provenance.json` records source URLs, licenses, archive hashes, and usage.

Downloaded packs and generated renders remain local and are intentionally
ignored by Git. They can be re-acquired from the provenance record.

## Generated working paths

The current local workspace contains `scene/`, `frames*/`, `audio/`,
`qa/`, and `final/` artifacts. Those are build/review outputs unless a
specific artifact is deliberately promoted later.
