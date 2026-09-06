# Core

Shared production infrastructure belongs here:

- timeline/timecode models;
- scene/set transforms and anchors;
- master audio timing;
- composition/assembly;
- technical/visual QA helpers.

The core scene model should make one set geometry authoritative so render lanes do not invent unrelated floor/effect/camera coordinates.
