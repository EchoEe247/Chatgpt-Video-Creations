# AGENTS.md

Operational handoff for ChatGPT and other agent sessions working in this repository.

## Repository purpose

`Chatgpt-Video-Creations` is the canonical production system for two related goals:

1. release-grounded business/OSS marketing videos;
2. original animated shows, seasons and episodes.

Fresh sessions should read this file plus the relevant workflow doc before producing a serious video.

## Never re-prove the basic capability

The user has already accepted these baselines:

- professional/business programmatic motion graphics;
- rigged 2D animation;
- stylized real-3D animation.

Use `docs/CAPABILITY_BASELINES.md` and improve from there when the production benefits.

## Business / OSS lane

When marketing a public project:

- resolve the exact current release from authoritative project/OSS state;
- prefer the OSS Shipping System marketing-eligible registry when the project belongs to that portfolio;
- record project, canonical release, prior release, exact tag/commit, public URL/package and source snapshot date;
- visibly identify the release version in the video;
- describe only behavior/features supported by that release;
- for a newer release, explain meaningful changes from the previous canonical release;
- do not market a repo merely because it is public.

See `docs/BUSINESS_RELEASE_MARKETING.md`.

## Original animation lane

For a **new show**, do not immediately render Episode 1.

First establish:

- research/inspiration synthesis;
- original premise and identity;
- show bible;
- world rules;
- recurring character bible;
- visual/audio identity;
- season arc;
- ordered episode map;
- story/dialogue foundation for the season;
- continuity/canon tracking.

Once implementation starts, produce **one episode per production turn**. Each episode follows:

**episode plan → scene plan → independent scene renders → assistant QA → user review → fixes if required → assistant re-QA → user acceptance → canon update → DONE ✅**

See `docs/ANIMATION_SHOW_WORKFLOW.md` and `docs/CONTINUITY_SYSTEM.md`.

## Long-form rendering

Do not render a long episode as one giant scene just to prove duration.

Use independent scene files at the richer quality baseline, preserve scene handles/state, review defective scenes individually, then assemble against a continuous master audio timeline.

See `docs/LONG_FORM_SCENE_ARCHITECTURE.md`.

## Hard spatial-layout rules

Do not position visual elements using unrelated guessed screen coordinates when they belong to the same set.

Required model:

- sets define floor/ground planes and named anchors;
- character transforms use foot/ground anchors;
- portal/glow/energy effects inherit the portal frame center, inner radius and orientation;
- held props inherit hand anchors;
- camera shots derive their screen transforms from the same set/world coordinates;
- depth/layer order is explicit.

A character floating above the floor or an effect visibly offset from its physical source is a QA failure.

See `docs/VISUAL_QA_STANDARDS.md`.

## Required MP4 QA

For serious renders:

1. inspect codec, dimensions, FPS, duration and audio stream;
2. inspect representative frames across every scene;
3. inspect before/after frames at scene boundaries;
4. inspect important effect/reaction/action frames;
5. verify floor/contact anchoring and set/effect alignment;
6. verify subtitles/dialogue timing;
7. fix important defects before handoff when feasible.

Do not declare completion based only on successful code execution.

## Content / originality rule

Research existing media for structure, genre, pacing, audience expectations and creative understanding when useful, but synthesize original characters, names, worlds, dialogue, visual identity and story logic. A reusable/monetizable show should not become a disguised clone of another show.

## Production package boundaries

Business production packages belong under:

`productions/business/<repo>/<release>/`

Animation productions belong under:

`productions/shows/<show>/seasons/season-XX/episodes/episode-YY/`

Use the templates in `templates/` as starting points.
