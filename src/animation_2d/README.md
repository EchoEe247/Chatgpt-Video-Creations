# 2D Animation

Reusable 2D production code is organized around shared scene geometry rather than guessed screen coordinates.

Current implementation includes:

- `src/core/geometry.py` — set geometry, floor anchors, portal geometry, camera transforms, and sprite placement by local anchors;
- `src/animation_2d/layout.py` — character foot anchoring and portal frame/effect placement derived from one canonical set definition;
- `tests/test_geometry.py` — regression coverage for floor anchoring, camera transforms, portal alignment, and invalid geometry.

The intended production boundaries remain:

- rigs / character parts and pose logic;
- sets / canonical floor + object anchors;
- camera / shot transforms;
- effects / portal, particles, overlays;
- renderer / frame generation.

Hard requirement: character feet and physical-effect sources use shared set anchors. Long-form episodes render richer scenes independently and assemble afterward.
