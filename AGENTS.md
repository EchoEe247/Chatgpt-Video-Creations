# AGENTS.md

Operational handoff for ChatGPT and other agent sessions working in this repository.

## Repository purpose

`Chatgpt-Video-Creations` is the canonical shared reference for the user's ChatGPT-based video production workflow.

Do not assume a fresh session has access to the originating conversation or its MP4 attachments. Use the repository documentation as the source of truth for interpreting requests.

## Canonical defaults

### Professional / business video

If the user asks for a business, professional, ad, explainer, product, dashboard, or social promo video without another explicit style, use the **professional programmatic motion-graphics baseline**.

Target qualities:

- polished;
- clean typography;
- purposeful motion;
- strong hierarchy;
- platform-appropriate composition;
- useful for real business content.

Do not treat a debug animation as acceptable merely because it renders.

### 2D animation

If the user says **2D animation video**, use the current **rigged limited-animation 2D baseline** documented in `docs/CAPABILITY_BASELINES.md`.

Do not regress to the early prototype approach of moving one static PNG per character.

Expected ingredients when the scene calls for them:

- independent head/eye/mouth/arm/body motion;
- pose/reaction changes;
- camera cuts;
- animated effects;
- dialogue/subtitles/audio;
- original characters and visual identity.

### 3D animation

If the user says **3D animation video**, use the current **stylized real-3D baseline** documented in `docs/CAPABILITY_BASELINES.md`.

Do not call flat sprites with fake zoom/perspective "3D."

Expected ingredients:

- actual 3D geometry;
- perspective camera and parallax;
- articulated characters;
- modeled set/props;
- lighting/shading;
- animated spatial effects;
- camera staging;
- audio when appropriate.

The expected style ceiling in the lightweight pipeline is stylized low-poly/cel-shaded indie animation or game-cinematic work, not feature-film studio character animation.

## User preference established by testing

The user has already reviewed all three lanes and considers the examples sufficient to define the base capability:

1. professional/business programmatic video — liked and suitable for real use;
2. recent 2D V2 animation — accepted as the 2D baseline;
3. recent 3D V2 animation — accepted as the 3D baseline and useful for understanding the present 3D limit.

Future sessions do not need to re-prove these capabilities before beginning a real request.

## Improvement rule

The baseline is a starting point. Improve it when a real production benefits from better:

- scene composition;
- hooks;
- character acting;
- rigs;
- lighting;
- effects;
- pacing;
- audio;
- camera staging;
- brand integration;
- platform optimization.

Do not over-engineer improvements that are invisible in the final MP4.

## Required QA behavior

For a serious render:

1. render the actual MP4;
2. inspect codec/resolution/FPS/duration/audio presence;
3. review representative frames across the timeline;
4. fix obvious visual/audio defects;
5. re-render when necessary;
6. provide the finished MP4, not only source code.

See `docs/PRODUCTION_WORKFLOW.md` for the full loop.

## Content/IP rule for character animation

If the user references an existing show, film, game, or character as inspiration, capture the **high-level qualities** they care about—genre, pacing, humor, energy, composition, medium—while creating original characters, names, props, dialogue, voices, and reusable visual identity when needed.

Do not silently turn a reusable project into a direct clone of third-party characters.

## Reference artifacts from the originating session

These filenames identify the accepted baselines but are not guaranteed to exist in a fresh session or local checkout:

- `programmatic_video_demo.mp4`
- `original_scifi_cartoon_scene_v2.mp4`
- `programmatic_3d_scifi_scene_v2.mp4`

Use the documented baseline descriptions if the files are unavailable.

## Repository evolution

As real videos are produced, this repo may grow to include:

- `src/` reusable render code;
- `assets/` reusable project assets;
- `presets/` render/style presets;
- `projects/` per-video production packages;
- `docs/` capability and workflow documentation;
- QA/receipt files for important renders.

Keep project-specific assets and reusable framework code clearly separated.
