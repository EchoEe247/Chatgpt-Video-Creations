# Core

Shared production infrastructure belongs here:

- timeline/timecode models;
- scene/set transforms and anchors;
- master audio timing;
- composition/assembly;
- technical/visual QA helpers;
- validated-baseline registry logic.

The core scene model should make one set geometry authoritative so render lanes do not invent unrelated floor/effect/camera coordinates.

`geometry.py` now carries the reusable 2D canvas/coordinate contract, camera transform, set floor anchors, portal geometry, and sprite placement by local contact anchor.

`baseline_registry.py` validates formal B-series baseline records. A registry pass proves the metadata contract is coherent; it does not replace the render/visual evidence required by the baseline itself.
