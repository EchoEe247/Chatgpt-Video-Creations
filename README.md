# Chatgpt-Video-Creations

Production system for videos created through ChatGPT sessions.

This repository now has two primary operating lanes:

1. **Business / OSS release marketing** — explain, demonstrate, and market useful public projects by exact release version.
2. **Original animation production** — develop original shows season-first, then produce and review episodes one at a time using scene-based 2D or 3D rendering.

The existing business-motion, 2D, and 3D capability baselines remain the technical rendering engines underneath those production systems.

## Operating model

### Business / OSS

A release video must be grounded in the exact project/release being promoted. The preferred source-of-truth flow is:

**OSS Shipping System → marketing-eligible public product → exact release/tag/commit → release facts/changelog → video production snapshot → render → QA → distribution**

Every release-marketing video should visibly identify the release version so viewers know which behavior and features the video describes. Newer releases should receive new/update marketing that explains what changed from the prior canonical release.

See [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md).

### Original animation

Do not start an original show by improvising Episode 1 and discovering the season afterward.

Use:

**show research/vision → show bible → season arc → season episode map → dialogue/story foundation → Episode 1 production → assistant QA → user review → fix if needed → accepted canon → Episode 2**

Episodes are implemented one at a time. A completed episode is not canon until both the assistant review and user review pass.

See [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) and [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md).

## Rendering baselines

| Engine | Default use | Baseline |
| --- | --- | --- |
| Professional motion graphics | OSS releases, product demos, explainers, ads, business/social content | Strong and practical |
| 2D animation | Original rigged limited-animation scenes and long-form episodes | Preferred animation baseline |
| 3D animation | Stylized real-3D scenes with geometry, perspective, lighting and articulation | Valid but more constrained than 2D |

See [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md).

## Long-form rule

Long videos are assembled from independently rendered scenes. Do not lower the entire production quality merely to force a two-minute or longer animation through one giant render.

**master plan → scene renders → scene QA/fixes → continuity check → assembly → master audio → final QA**

See [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md).

## Visual geometry rule

Characters, props, effects and cameras should share one scene/set coordinate system.

- character feet anchor to the floor plane;
- portal energy inherits the physical portal frame center/radius;
- held props inherit hand anchors;
- camera crops transform the same world/set anchors rather than introducing unrelated screen coordinates.

This is now a hard QA requirement, not a cosmetic preference. See [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md).

## Repository map

- [`AGENTS.md`](AGENTS.md) — operating handoff for fresh ChatGPT/agent sessions.
- [`docs/VISION.md`](docs/VISION.md) — project mission and lane boundaries.
- [`docs/PRODUCTION_WORKFLOW.md`](docs/PRODUCTION_WORKFLOW.md) — shared render/review workflow.
- [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md) — version-grounded OSS/business marketing.
- [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) — show/season/episode lifecycle.
- [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md) — canon and episode-to-episode state.
- [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md) — independent scene rendering/assembly.
- [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md) — scene alignment and final visual gates.
- [`templates/`](templates/) — business release, show, season and episode starters.
- [`productions/`](productions/) — expected layout for real production packages.
- [`scripts/`](scripts/) — lightweight validation/assembly helpers.
- [`src/`](src/) and [`presets/`](presets/) — reusable render framework boundaries.

## Acceptance rule

The deliverable is the **finished MP4**, not the fact that a script ran.

For serious work:

**plan → build → render → inspect actual MP4 → fix visible/audio defects → re-render → validate → user review**

For episodic animation, the episode becomes `DONE ✅` only after both assistant QA and user acceptance pass.
