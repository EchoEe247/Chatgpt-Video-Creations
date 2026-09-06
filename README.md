# Chatgpt-Video-Creations

This repository is the production system I use for videos created through ChatGPT sessions. The main thing is that I do not want every video request to become another one-off experiment where the capability has to be rediscovered from scratch. Once a production method is proven and accepted, it becomes part of the baseline here and future work should build from it.

There are two main lanes, and I want them kept separate because they have different goals:

1. **Business / OSS release marketing** — videos that explain and market useful public projects based on the exact release being promoted.
2. **Original animation production** — original scenes, shows, seasons, and episodes built as an actual production system rather than unrelated generated clips.

The existing professional motion-graphics, 2D, and 3D baselines are the rendering engines underneath both lanes. They are starting points, not ceilings.

## Business / OSS release marketing

For business work, the point is not to make a generic promo for a repository just because it is public. I want the video tied to something users can actually use and to the exact version where the shown behavior exists.

The preferred source-of-truth flow is:

**OSS Shipping System → marketing-eligible public product → exact release/tag/commit → release facts/changelog → production snapshot → render → QA → distribution**

The release version should be visible in the video. If somebody sees the marketing later, they should be able to tell which version is being demonstrated instead of assuming every feature shown still maps to whatever the newest release happens to be.

When a newer release is worth marketing, create new/update marketing for that release and explain what materially changed from the previous canonical release. Do not rewrite history by silently replacing old release packages.

See [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md).

## Original animation production

For original animation, I do not want to improvise Episode 1 first and only afterward figure out what the show or season is supposed to become. A show should have enough structure behind it that Episode 1 already knows what later episodes may need from it.

The working flow is:

**research/vision → show bible → season arc → episode map → story/dialogue foundation → Episode 1 production → assistant QA → user review → fixes when needed → accepted canon → Episode 2**

Episodes are produced one at a time. That keeps review focused and makes continuity easier to control. An episode is not accepted canon just because the MP4 rendered successfully; assistant review and user review both have to pass first.

See [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) and [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md).

## Rendering baselines

| Engine | Default use | Baseline |
| --- | --- | --- |
| Professional motion graphics | OSS releases, product demos, explainers, ads, business/social content | Strong and practical |
| 2D animation | Original rigged limited-animation scenes and long-form episodes | Preferred animation baseline |
| 3D animation | Stylized real-3D scenes with geometry, perspective, lighting, and articulation | Valid, but more constrained than 2D |

See [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md).

## Long-form production

Long-form work should not become lower-quality animation just because the final runtime is longer. The better approach is to keep the richer scene-level quality and assemble the final video from independently rendered scenes.

**master plan → scene renders → scene QA/fixes → continuity check → assembly → master audio → final QA**

That also means a bad Scene 6 can normally be replaced without rerendering Scenes 1–5 and 7–12 unless a shared asset or continuity change genuinely affects them.

See [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md).

## Spatial consistency is a hard requirement

One issue I specifically do not want repeated is visual elements being positioned independently when they are supposed to belong to the same physical set.

Characters, props, effects, and cameras should derive from one shared scene/set coordinate system:

- character feet anchor to the floor plane;
- portal energy inherits the physical portal frame center and radius;
- held props inherit hand anchors;
- camera crops transform the same world/set anchors instead of introducing unrelated screen coordinates.

So if a character is visibly floating above the floor, or a green portal effect is offset from the gray/black portal frame it belongs to, that is not a small cosmetic issue. It is a QA failure that should be fixed before the video is treated as done.

See [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md).

## Repository map

- [`AGENTS.md`](AGENTS.md) — operating handoff for fresh ChatGPT/agent sessions.
- [`docs/VISION.md`](docs/VISION.md) — what this repository is for and why the two production lanes stay separate.
- [`docs/PRODUCTION_WORKFLOW.md`](docs/PRODUCTION_WORKFLOW.md) — shared build, render, review, repair, and acceptance flow.
- [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md) — version-grounded OSS/business marketing.
- [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) — show, season, and episode lifecycle.
- [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md) — accepted canon and episode-to-episode state.
- [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md) — independent scene rendering and assembly.
- [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md) — spatial alignment, composition, acting, and final visual gates.
- [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md) — current accepted rendering baselines and limits.
- [`docs/REFERENCE_SAMPLES.md`](docs/REFERENCE_SAMPLES.md) — what earlier production tests proved, failed, or established.
- [`templates/`](templates/) — business release, show, season, episode, and production starters.
- [`productions/`](productions/) — expected layout for real production packages.
- [`scripts/`](scripts/) — lightweight validation and assembly helpers.
- [`src/`](src/) and [`presets/`](presets/) — reusable rendering framework boundaries.

## What counts as done

For me, the deliverable is the **finished MP4**, not the fact that a script ran without crashing.

For serious work the standard is:

**plan → build → render → inspect the actual MP4 → fix visible/audio defects → re-render → validate → user review**

That distinction matters because code can succeed while the video is still visibly wrong. Technical success is useful evidence, but the final rendered result is what gets accepted.

For episodic animation, the episode becomes `DONE ✅` only after both assistant QA and user acceptance pass.