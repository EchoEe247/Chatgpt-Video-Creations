# 2D Scene Geometry Contract

This document records the geometry relationships we understand well enough to reuse now, and separates them from values that are still provisional.

The reason for this contract is practical. Earlier renders showed two obvious classes of failure:

- characters could appear to float because sprite bounds were positioned instead of the actual foot/contact point;
- green portal energy could drift away from the gray/black portal frame because the effect and the physical frame used separate coordinate tables.

Those failures should not be repaired by repeatedly nudging pixels. The reusable relationship is more important than any one set of numbers.

## Coordinate model

The reusable 2D geometry code uses a declared canvas and a world/set coordinate system.

For the current programmatic 2D lane:

- origin: top-left;
- positive X: right;
- positive Y: down;
- units: pixel-like set units;
- camera scale: uniform;
- camera origin and scale transform related objects together.

A production set should record its canvas dimensions explicitly. The geometry layer does not assume that every future production is 1280×720, even though 1280×720 at 24 FPS is the current preferred long-form 2D target.

## Character grounding

A standing character has two different anchors:

1. **set/world anchor** — where the character is standing;
2. **rig-local foot anchor** — the point inside the character sprite/rig that physically touches the floor.

Placement is derived from the relationship:

`screen_foot = camera.project(world_foot)`

`screen_top_left = screen_foot - (rig_local_foot * combined_scale)`

The sprite's bounding-box bottom is not the floor authority.

This lets poses with different image bounds remain grounded as long as each pose/rig preserves the correct local contact anchor.

## Floor rule

A set owns the floor plane used by its named standing anchors.

If a named standing anchor declares a different floor value from the set, the geometry is rejected.

That rule is already covered by automated regression tests.

The exact numeric floor value for the accepted lab production is **not yet a validated production baseline**. The current template value is a synthetic example used to test the relationship.

## Portal rule

A portal owns one physical geometry definition:

- center;
- outer radius;
- inner radius;
- orientation.

The energy opening is derived from the portal's inner opening.

It must not have an unrelated second center/radius table.

For a circular portal:

`energy.center = portal.inner.center`

`energy.radius = portal.inner.radius`

The current 2D layout code enforces that relationship through camera transforms.

The exact production lab portal measurements are still provisional until the renderer is connected to this layer and a corrected scene passes visual review.

## Camera rule

Camera crops and zooms should transform set geometry rather than create replacement screen coordinates.

If the camera moves or scales, the floor anchor, character foot contact, physical portal, portal energy, and attached props/effects should move through the same transform chain.

A camera change should not require a new hand-maintained `PORTAL_POS` table.

## Canvas metadata

`SetGeometry` can carry explicit canvas metadata:

```json
{
  "canvas": {
    "width": 1280,
    "height": 720,
    "origin": "top-left",
    "x_axis": "right",
    "y_axis": "down",
    "units": "px"
  }
}
```

The width and height are production data, not universal constants.

The axis/origin convention above is the current 2D engine contract.

## What is not formalized yet

The following should be measured from accepted output before becoming hard project values:

- action-safe margins;
- text-safe regions;
- preferred character scale ranges by shot type;
- production lab floor measurement;
- production portal measurements;
- camera preset library;
- full z-order/layer schema;
- scenery clipping boundaries;
- pose-specific foot anchors for every future rig.

Future agents should not fill these gaps with arbitrary numbers just to make the schema look complete.

## Template status

`templates/set-anchors.json` is a **structural example**, not a known-good production set.

Its numbers exist so tests and validators can exercise the contract.

Passing `scripts/validate-scene-alignment.py` proves that the file is internally coherent. It does not prove that those coordinates look correct in an actual rendered scene.

## Next promotion step

The next relevant production step is:

**connect renderer → use shared geometry → render corrected reference scene → inspect floor/portal alignment → refine measurements → user review → preserve accepted measurements → consider B1**

Until that visual loop passes, do not call the current geometry values a validated baseline.
