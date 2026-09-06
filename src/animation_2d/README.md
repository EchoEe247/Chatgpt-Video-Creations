# 2D Animation

Reusable 2D production code should be separated into:

- rigs/character parts and pose logic;
- sets/canonical floor + object anchors;
- camera/shot transforms;
- effects/portal, particles, overlays;
- renderer/frame generation.

Hard relationship: character feet and physical-effect sources use shared set anchors. Long-form episodes render richer scenes independently and assemble afterward.

The current geometry/layout layer is structurally implemented and unit-tested. It now includes explicit canvas metadata, foot-anchor placement, shared camera transforms, and portal energy derived from the physical portal opening.

Do **not** treat `templates/set-anchors.json` as a validated production layout. Its numbers are synthetic fixtures. The next maturity step is to wire the actual renderer to this layer, measure/refine the real lab geometry from rendered output, and promote those values only after visual + user review.

See `docs/SCENE_GEOMETRY.md` and `docs/OPERATING_MODEL.md`.
