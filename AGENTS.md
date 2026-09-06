# AGENTS.md

This file is the operating handoff for fresh ChatGPT or agent sessions working in this repository.

## Angel wording integration

For Angel-owned project communication, use `EchoEe247/Chatgpt-Angel-wording-refinement` as the wording/refinement authority.

Keep the boundary clear:

- this repository defines what `Chatgpt-Video-Creations` is, how production works, its accepted baselines, creative rules, QA gates, and project state;
- `Chatgpt-Angel-wording-refinement` defines how Angel-owned documentation, GitHub communication, marketing copy, captions, announcements, project explanations, and other project-facing wording should be refined.

For routine work, load that repository's `prompts/SESSION_BOOTSTRAP.md`. For important or ambiguous wording, also use its full system spec, the relevant context profile, and meaning-preservation rules.

Default to Angel-refined, with Angel-professional for serious technical/business material and Angel-direct for casual/social communication.

Do not apply Angel's voice to fictional character dialogue by default. Characters follow their own show/character voice unless a character is intentionally designed around Angel's speaking style. The wording system governs the surrounding Angel-owned project communication.

Project truth always outranks wording style.

## Existing production authority

The main thing to understand first is that this repo already has accepted production baselines. Do not spend a new session proving that professional motion graphics, rigged 2D animation, or stylized real-3D animation are possible. That work has already been done. Start from the accepted baseline, use the relevant workflow, and improve it when the production actually benefits.

## What this repository is for

`Chatgpt-Video-Creations` supports two main goals:

1. release-grounded business / OSS marketing videos;
2. original animated shows, seasons, episodes, and scenes.

Those goals share rendering and QA infrastructure, but they should not be treated as the same creative workflow.

Before serious production, read this file and the workflow document for the lane you are using.

## Business / OSS lane

For public-project marketing, the point is not to create a promo just because a repository exists. Resolve what is actually intended for users and which exact release the video is describing.

When the project belongs to the OSS Shipping System portfolio:

- resolve marketing eligibility from the canonical OSS registry;
- verify the exact current release from authoritative project state;
- record the project, canonical release, prior release, exact tag/commit, public URL or package, and source snapshot date;
- show the release version visibly in the video;
- describe only features and behavior supported by that release;
- when a newer release is being marketed, explain the meaningful change from the previous canonical release;
- keep material limitations visible when they matter to truthful use.

Do not market a repository merely because it is public.

See `docs/BUSINESS_RELEASE_MARKETING.md`.

## Original animation lane

For a new show, do not jump directly into Episode 1. I want the season to have enough direction that the first episode already understands what future episodes may need from it.

Establish first:

- research and inspiration synthesis;
- an original premise and identity;
- show bible and world rules;
- recurring character bible;
- visual and audio identity;
- season arc and ordered episode map;
- story/dialogue foundation;
- continuity and canon tracking.

After the season foundation is ready, production narrows to one episode at a time:

**episode plan → scene plan → independent scene renders → assistant QA → user review → fixes when needed → assistant re-QA → user acceptance → canon update → DONE ✅**

Do not start the next episode while the current one still needs refinement.

See `docs/ANIMATION_SHOW_WORKFLOW.md` and `docs/CONTINUITY_SYSTEM.md`.

## Long-form rendering

A long runtime is not a reason to lower the entire animation baseline.

Use independently rendered scenes, preserve scene handles and continuity state, inspect and replace defective scenes individually, then assemble them against a continuous master timeline. If one scene fails, fix that scene unless a shared asset or continuity change genuinely affects the others.

See `docs/LONG_FORM_SCENE_ARCHITECTURE.md`.

## Shared scene geometry is mandatory

Do not give elements unrelated guessed screen coordinates when they belong to the same physical set.

The set should define the geometry and anchors. Then:

- characters use foot/ground anchors;
- portal energy inherits the portal frame center, inner radius, and orientation;
- held props inherit hand anchors;
- screen content inherits screen bounds;
- camera shots derive their transforms from the same set/world coordinates;
- depth and layer order are explicit.

A character floating above the floor, or a portal effect visibly offset from its frame, is a production defect and should be fixed before acceptance.

See `docs/VISUAL_QA_STANDARDS.md`.

## MP4 QA

For serious renders, do not stop at successful code execution.

At minimum:

1. verify codec, dimensions, FPS, duration, and audio stream;
2. inspect representative frames throughout every scene;
3. inspect frames immediately before and after scene boundaries;
4. inspect important effects, actions, and reactions;
5. verify floor/contact anchoring and source/effect alignment;
6. verify subtitle and dialogue timing;
7. fix important visible or audio defects before handoff when feasible.

The final MP4 is the deliverable.

## Originality

Research existing media when it helps with structure, pacing, genre expectations, subject matter, or creative understanding. Use that research to synthesize something original.

Recurring characters, names, worlds, dialogue, visual identity, and story logic should belong to the new production. A reusable or monetizable show should not become a disguised clone of another show.

## Production package locations

Business releases:

`productions/business/<repo>/<release>/`

Animation productions:

`productions/shows/<show>/seasons/season-XX/episodes/episode-YY/`

Use the templates under `templates/` as starting points instead of rebuilding package structure manually.