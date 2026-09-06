# Capability Baselines

This file records what the repository can already treat as established production capability.

I keep these baselines so a fresh ChatGPT or agent session does not go backward and start proving the same basic things again. If the request is for a business video, 2D animation, 3D animation, or a longer episode, start from the relevant accepted capability below and improve it where the real production benefits.

These are minimum starting points, not permanent ceilings.

## Capability baseline vs formal validated baseline

The word **baseline** has two related but different uses in this repository.

This document is the **capability baseline** layer: it records methods and quality levels that have already been demonstrated and accepted well enough to guide future work.

The formal B-series registry under `baselines/` is stricter. `B1`, `B2`, and later identifiers require an exact repository commit, exact representative artifact, render/validation conditions, capability claim, known limitations, and validation evidence matching that claim.

Do not retroactively call an older reference video `B1` only because it was useful. The older references predate the durable artifact/provenance capture required for that stronger claim.

See `baselines/README.md`.

---

## 1. Professional / business programmatic video

### Default interpretation

A clean, polished motion-graphics video for practical use such as:

- OSS release marketing;
- product ads and demos;
- Shorts, Reels, or TikTok promos;
- software/dashboard explainers;
- service advertisements;
- feature launches;
- data and metrics stories;
- screen-demo sequences;
- animated titles and CTAs.

### Accepted reference

`programmatic_video_demo.mp4`

Reference characteristics:

- vertical 720×1280;
- 24 FPS;
- H.264 / yuv420p;
- roughly 10 seconds;
- animated typography;
- UI/dashboard cards;
- numerical and chart animation;
- easing, transitions, and effects;
- direct MP4 output.

This lane was accepted as suitable for real professional work.

### Business quality rule

The final should feel intentional, readable, and useful. It should not look like a debug visualization that happens to contain marketing text.

For OSS/project marketing, the capability is also **release/version grounded**. The video should visibly identify the exact release it describes and use verified facts from the project and business release workflow.

See `docs/BUSINESS_RELEASE_MARKETING.md`.

---

## 2. Short-form 2D animation

### Default interpretation

When the request is for a **2D animation video**, start from the accepted rigged 2D baseline rather than static-PNG transform animation.

Accepted reference: `original_scifi_cartoon_scene_v2.mp4`.

### Reference characteristics

- 1280×720;
- 24 FPS;
- H.264 + AAC;
- roughly 15 seconds;
- original cartoon characters;
- independently animated body parts;
- head movement;
- eyes, pupils, and gaze;
- blinking;
- multiple mouth states;
- articulated arm gestures;
- recoil and body acting;
- animated portal and effects;
- multiple camera shots;
- dialogue, subtitles, and audio.

### Visual target

The practical target is **limited 2D television/cartoon animation**: clear poses, readable acting, expressive timing, dialogue, cuts, and effects.

A character should not spend the whole scene as one static cutout being moved or zoomed. Use meaningful head, eye, arm, body, and reaction changes when the beat needs them.

### Spatial rule

A good rig is not enough if the character and effects do not belong to the same set.

Hard relationships:

- standing character **feet anchor to the set floor plane**;
- pose changes preserve that foot/floor anchor unless intentional movement occurs;
- portal, glow, and energy effects inherit the **physical portal frame center, inner radius, and orientation**;
- held props inherit hand anchors;
- camera crops transform the same set/world anchors;
- depth and layering are deliberate.

Do not create separate guessed coordinate tables for a physical object and the effect that belongs to it.

The relationship is established. The exact production measurements still need to be visually validated before being promoted as formal known-good geometry.

See `docs/SCENE_GEOMETRY.md` and `docs/VISUAL_QA_STANDARDS.md`.

### Current limits

This lightweight programmatic approach is strong for stylized limited animation, but it is not the same thing as a full traditional animation-studio pipeline.

Harder areas still include highly fluid frame-by-frame acting, complex deformable rigs, advanced phoneme lip sync, painterly frame-by-frame effects, and premium voice acting without a stronger voice source.

---

## 3. Long-form 2D animation / episodes

### Default architecture

Long-form production does **not** mean one giant simplified render.

Use:

**master episode plan → independent 5–15s scenes → richer short-form rig quality → scene QA/fixes → continuity check → assembly → master audio → final QA**

The two-minute experiments proved that independently rendered scenes can assemble smoothly while preserving continuity and allowing targeted rerenders.

### Preferred technical target

When practical:

- 24 FPS scene renders;
- at least 1280×720 final landscape output for episodic work;
- consistent rig and set versions across scenes;
- one continuous master audio timeline;
- scene handles or overlap where continuous action needs them;
- exact scene-duration and timeline specs;
- hard-cut editing unless the story calls for another transition.

### Quality interpretation

The short 2D V2 remains the **visual and acting capability baseline** to match or exceed inside each scene.

The long-form two-minute tests established the **production architecture**. They are not permission to lower the animation baseline just because the final runtime is longer.

See `docs/LONG_FORM_SCENE_ARCHITECTURE.md` and `docs/REFERENCE_SAMPLES.md`.

---

## 4. 3D animation

### Default interpretation

When the request is for a **3D animation video**, use the accepted V2 baseline: real 3D geometry, perspective, articulated characters, lighting, camera motion, effects, and audio.

Accepted reference: `programmatic_3d_scifi_scene_v2.mp4`.

### Reference characteristics

- 960×540;
- 24 FPS;
- H.264 + AAC;
- roughly 14 seconds;
- actual 3D geometry rendered with a 3D engine;
- perspective and parallax;
- stylized/cel character treatment;
- modeled environment and props;
- articulated limbs, head, eyes, and mouths;
- multiple camera shots;
- portal energy and lighting;
- creature emergence;
- contact-shadow treatment;
- dialogue, subtitles, and SFX.

### Visual target

A **stylized low-poly / cel-shaded indie cartoon or game-cinematic scene**.

### Current limits

Without a full Blender/Maya-class character pipeline, difficult areas include advanced skeletal deformation and skinning, high-quality facial blendshapes, sophisticated walk/run cycles, cloth and hair physics, complex materials/global illumination, and feature-film studio character animation.

For long-form 3D, use the same independent-scene principle, generally with shorter scene chunks when the render is heavier.

---

## 5. Choosing the rendering lane

1. **Business/ad/explainer/product/social/OSS release** → professional programmatic video.
2. **Narrative/cartoon/character animation** → 2D by default.
3. **Long episode/season animation** → 2D independent-scene architecture unless 3D is explicitly needed.
4. **Explicit 3D/depth/game-cinematic/low-poly/cel-3D request** → 3D animation.

The lanes can be combined intentionally. For example, a business demo can use a 2D narrative hook, or a 3D product reveal can use 2D UI/title overlays.

The combination should serve the production rather than exist only to prove more techniques can be mixed together.

---

## 6. Improvement policy

For every serious production, ask what would make the final MP4 visibly better:

- Can the hook be stronger?
- Can acting and reactions read more clearly?
- Are characters actually grounded on the set?
- Are effects aligned with the physical source geometry?
- Is scene composition clear?
- Can audio or lip timing improve?
- Can a defective scene be rerendered instead of degrading the whole production?
- Would real product or brand assets improve business truth and usefulness?
- Is the result appropriate for the target platform?

Improve where the viewer gets real value from the change. Avoid complexity that only makes the implementation look more sophisticated.

When an improvement reveals a reusable deterministic rule, formalize it after validation. When it is still a subjective visual choice, keep it flexible.
