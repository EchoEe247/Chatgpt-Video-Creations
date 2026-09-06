# Capability Baselines

This document defines the current production baseline for the supported rendering lanes. It exists so a fresh ChatGPT/agent session can interpret requests such as `business video`, `2D animation`, `3D animation`, or a longer animated episode consistently.

These are **minimum expected starting points**, not permanent ceilings.

---

## 1. Professional / business programmatic video

### Default interpretation

A clean, polished motion-graphics video for real use cases such as:

- OSS release marketing;
- product ads/demos;
- Shorts/Reels/TikTok promos;
- software/dashboard explainers;
- service advertisements;
- feature launches;
- data/metrics stories;
- screen-demo sequences;
- animated titles/CTAs.

### Accepted reference

`programmatic_video_demo.mp4`

Reference characteristics:

- vertical 720×1280;
- 24 FPS;
- H.264 / yuv420p;
- roughly 10 seconds;
- animated typography;
- UI/dashboard cards;
- numerical/chart animation;
- easing/transitions/effects;
- direct MP4 output.

The user accepted this lane as suitable for real professional work.

### Business quality rule

The final should look professional, intentional, readable and useful—not like debug visualization.

For OSS/project marketing, the business lane is now also **release/version grounded**. The video should visibly identify the exact release it describes and use verified project/release facts from the business release workflow.

See `docs/BUSINESS_RELEASE_MARKETING.md`.

---

## 2. Short-form 2D animation

### Default interpretation

When the user asks for a **2D animation video**, start from the accepted rigged 2D baseline, not static-PNG transform animation.

Accepted reference: `original_scifi_cartoon_scene_v2.mp4`.

### Reference characteristics

- 1280×720;
- 24 FPS;
- H.264 + AAC;
- roughly 15 seconds;
- original cartoon characters;
- independently animated body parts;
- head movement;
- eyes/pupils/gaze;
- blinking;
- multiple mouth states;
- articulated arm gestures;
- recoil/body acting;
- animated portal/effects;
- multiple camera shots;
- dialogue/subtitles/audio.

### Visual target

The useful target is **limited 2D television/cartoon animation**: clear poses, readable acting, expressive timing, dialogue, cuts and effects.

A scene should not rely only on a static cutout drifting/zooming. Use meaningful head/eye/arm/body/reaction changes.

### Spatial rule

The rig is not enough by itself. Characters/effects must inhabit a coherent set.

Hard requirements:

- standing character **feet anchor to the set floor plane**;
- pose changes preserve that foot/floor anchor unless intentional movement occurs;
- portal/glow/energy effects inherit the **physical portal frame center, inner radius and orientation**;
- held props inherit hand anchors;
- camera crops transform the same set/world anchors;
- depth/layering is deliberate.

Do not create separate guessed coordinate tables for a physical object and the effect that belongs to it.

See `docs/VISUAL_QA_STANDARDS.md`.

### Current limits

The lightweight programmatic approach is suitable for stylized limited animation, but not equivalent to a full traditional animation studio pipeline. Harder areas include highly fluid frame-by-frame acting, complex deformable rigs, advanced phoneme lip sync, painterly frame-by-frame effects and premium voice acting without a stronger voice source.

---

## 3. Long-form 2D animation / episodes

### Default architecture

Long-form production does **not** use one giant simplified render.

Use:

**master episode plan → independent 5–15s scenes → richer short-form rig quality → scene QA/fixes → continuity check → assembly → master audio → final QA**

The two-minute experiments proved that independently rendered scenes can assemble smoothly while preserving continuity and allowing targeted rerenders.

### Preferred technical target

When practical:

- 24 FPS scene renders;
- at least 1280×720 final landscape output for episodic work;
- consistent rig/set versions across scenes;
- one continuous master audio timeline;
- scene handles/overlap where continuous action needs them;
- exact scene-duration/timeline specs;
- hard-cut editing unless the story calls for another transition.

### Quality interpretation

The short 2D V2 remains the **visual/acting quality baseline** to match or exceed inside each scene.

The long-form two-minute tests are the **production architecture baseline**, not permission to lower animation quality.

See `docs/LONG_FORM_SCENE_ARCHITECTURE.md` and `docs/REFERENCE_SAMPLES.md`.

---

## 4. 3D animation

### Default interpretation

When the user asks for a **3D animation video**, use the accepted V2 baseline: real 3D geometry, perspective, articulated characters, lighting, camera motion, effects and audio.

Accepted reference: `programmatic_3d_scifi_scene_v2.mp4`.

### Reference characteristics

- 960×540;
- 24 FPS;
- H.264 + AAC;
- roughly 14 seconds;
- actual 3D geometry rendered with a 3D engine;
- perspective/parallax;
- stylized/cel character treatment;
- modeled environment/props;
- articulated limbs/head/eyes/mouths;
- multiple camera shots;
- portal energy/lighting;
- creature emergence;
- contact-shadow treatment;
- dialogue/subtitles/SFX.

### Visual target

A **stylized low-poly / cel-shaded indie cartoon or game-cinematic scene**.

### Current limits

Without a full Blender/Maya-class character pipeline, difficult areas include advanced skeletal deformation/skinning, high-quality facial blendshapes, sophisticated walk/run cycles, cloth/hair physics, complex materials/global illumination and feature-film studio character animation.

For long-form 3D, use the same independent-scene principle with generally shorter scene chunks.

---

## 5. Choosing the rendering lane

1. **Business/ad/explainer/product/social/OSS release** → professional programmatic video.
2. **Narrative/cartoon/character animation** → 2D by default.
3. **Long episode/season animation** → 2D independent-scene architecture unless 3D is explicitly required.
4. **Explicit 3D/depth/game-cinematic/low-poly/cel-3D request** → 3D animation.

Lanes may be combined intentionally, such as 2D narrative hooks around a business demo or 3D product reveals with 2D UI/title overlays.

---

## 6. Improvement policy

For every real production ask internally:

- Can the hook be stronger?
- Can acting/reactions be clearer?
- Are characters actually grounded on the set?
- Are effects aligned with their physical source geometry?
- Can scene composition be clearer?
- Can audio/lip timing improve?
- Can a defective scene be rerendered instead of degrading the full production?
- Can real product/brand assets improve business truth/usefulness?
- Is the output platform-appropriate?

Improve where it produces visible value. Avoid complexity that does not improve the final MP4.
