# 2D Animation

Reusable 2D production code should be separated into:

- rigs/character parts and pose logic;
- sets/canonical floor + object anchors;
- camera/shot transforms;
- effects/portal, particles, overlays;
- renderer/frame generation.

Hard relationship: character feet and physical-effect sources use shared set anchors. Long-form episodes render richer scenes independently and assemble afterward.

The current geometry/layout layer is structurally implemented and unit-tested. It now includes explicit canvas metadata, foot-anchor placement, shared camera transforms, and portal energy derived from the physical portal opening.

Do **not** treat `templates/set-anchors.json` as a validated production layout. Its numbers are synthetic fixtures. The repository already has the narrowly scoped B1 Candidate 002 geometry/composition baseline; future sets and rigs should reuse the shared geometry layer while measuring and validating their own production coordinates rather than copying the template values or overgeneralizing B1.

See `docs/SCENE_GEOMETRY.md` and `docs/OPERATING_MODEL.md`.