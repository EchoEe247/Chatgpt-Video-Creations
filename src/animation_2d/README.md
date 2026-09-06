# 2D Animation

Reusable 2D production code should be separated into:

- rigs/character parts and pose logic;
- sets/canonical floor + object anchors;
- camera/shot transforms;
- effects/portal, particles, overlays;
- renderer/frame generation.

Hard requirement: character feet and physical-effect sources use shared set anchors. Long-form episodes render richer scenes independently and assemble afterward.
