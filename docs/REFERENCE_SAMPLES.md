# Reference Samples and Lessons

This file records the capability exploration that established the repository baselines. It preserves accept/reject decisions so later sessions do not regress to earlier prototypes.

The MP4 files named below originated in ChatGPT production sessions. They are not assumed to be present in every future session.

---

## A. Professional / business motion sample — accepted

Reference file: `programmatic_video_demo.mp4`

### What it demonstrated

- 720×1280 vertical composition;
- 24 FPS H.264;
- animated typography;
- motion graphics;
- dashboard cards;
- animated charts/data;
- clean transitions/easing;
- programmatic effects;
- finished MP4 rendering without stock footage.

### User decision

The user liked this example for the professional/business side and considers it a valid base for real work.

### Production meaning

Future business videos should preserve clarity, polish, intentional motion, and business usefulness, while being customized to the exact project/release/brand/audience/platform.

---

## B. Early 2D animation prototype — rejected as final baseline

Reference file: `cartoon_animation_sample.mp4`

It placed generated character artwork over a background and moved/bobbed/rotated the cutouts. It looked like moving artwork rather than convincing cartoon animation.

**Rule derived:** do not use a single static character image with only transform animation as the default 2D production method.

---

## C. Intermediate 2D animation prototype — improved but defective

Reference file: `original_scifi_cartoon_scene_sample.mp4`

Important defects found during self-review:

- mouth overlays sometimes landed on the torso instead of the face;
- characters remained mostly static cutouts;
- camera cuts were largely crops/zooms of the same source art;
- creature interaction lacked depth/reaction acting;
- voices overlapped because dialogue timing used guesses;
- subtitles could end before speech.

**Rules derived:** face components must inherit the rig, dialogue windows must use measured clip duration, important events require visible reactions, and camera changes cannot substitute for acting.

---

## D. Current short-form 2D visual baseline — accepted

Reference file: `original_scifi_cartoon_scene_v2.mp4`

Characters were rebuilt as part-based rigs drawn in code.

Baseline features:

- independent character parts;
- head movement;
- pupil direction;
- blinking;
- multiple mouth states;
- articulated arms/hands;
- recoil/body response;
- animated portal vortex;
- creature entrance;
- shot changes and close-ups;
- dialogue, subtitles, ambience/SFX;
- corrected dialogue overlap.

The user considered this good as the 2D animation baseline.

**Default:** when a future request says `2D animation video`, this remains the short-form visual/acting baseline unless a project brief overrides it.

---

## E. First real 3D prototype — rejected as final baseline

Reference file: `programmatic_3d_scifi_scene.mp4`

It proved actual 3D geometry, perspective, parallax and articulated primitive parts, but looked like a development/debug prototype: primitive characters, sparse/dark set, weak lighting, limited acting, primitive creature design, portal-dominated composition, and no audio stream.

**Rule derived:** technical 3D alone is not enough; production 3D needs art direction, staging, readable set dressing, lighting, acting and audio.

---

## F. Current 3D animation baseline — accepted

Reference file: `programmatic_3d_scifi_scene_v2.mp4`

Key upgrades:

- real 3D engine rendering;
- stylized/cel character treatment;
- stronger silhouettes;
- modeled lab environment;
- articulated limbs/head/eyes/mouths;
- multiple camera shots;
- portal energy geometry and lighting;
- contact-shadow treatment;
- creature emergence;
- measured dialogue timing;
- subtitles;
- voices and SFX/ambience;
- H.264 + AAC output.

A portal-orientation defect was caught during review and fixed before handoff. The user accepted this as enough to understand the current 3D capability/limit.

---

## G. First 2-minute 2D workflow proof — assembly accepted, visual quality not promoted

Reference file: `two_minute_2d_animation_scene_based.mp4`

Purpose: test whether a two-minute animation could be planned as multiple scenes and delivered as one coherent MP4.

What it proved:

- 12 planned scene segments could form a continuous 2-minute timeline;
- recurring character/set designs stayed coherent;
- one master audio timeline could span scene boundaries;
- ordinary hard cuts could hide production boundaries cleanly.

Compromise: the whole two-minute render was simplified to 12 FPS/cached pose states to fit runtime constraints. That lowered animation quality below the short 2D V2 baseline.

**Decision:** keep this as an architecture proof only. Do not make the lower-detail 12 FPS implementation the new 2D baseline.

---

## H. Independent-scene long-form 2D proof — architecture accepted, spatial QA tightened

Reference lineage:

- `two_minute_2d_animation_rich_scenes_final_v2.mp4`
- `two_minute_2d_animation_v3_updated.mp4`

Purpose: scale the richer 2D architecture by rendering scenes independently, reviewing/replacing defective scenes, then assembling the two-minute master.

What it proved:

- 12 scenes can be rendered independently and assembled without black gaps/broken seams;
- defective scenes can be rerendered without redoing the whole episode;
- 18–24 FPS richer per-frame animation scales better than one giant simplified render;
- continuous master audio remains compatible with scene replacement;
- 1280×720 / 24 FPS final delivery is practical after scene-based production.

Important user QA feedback remained after the V3 pass:

- characters should be positioned by their **feet on the floor**, not by approximate sprite bounds;
- the green portal energy circle must be **concentric/aligned with the physical gray/black portal frame**;
- set/effect/camera placement should derive from one canonical geometry definition rather than separate guessed screen-coordinate tables.

These observations became hard rules in `docs/VISUAL_QA_STANDARDS.md` and the set-anchor template.

**Decision:** the independent-scene system is the long-form production architecture baseline. The short 2D V2 remains the visual/acting quality baseline to match or exceed inside each scene.

---

## Canonical interpretation summary

| Requested type | Accepted reference/architecture | Interpretation |
| --- | --- | --- |
| Business / professional | `programmatic_video_demo.mp4` | polished programmatic motion graphics, now release/version-grounded for OSS work |
| Short 2D animation | `original_scifi_cartoon_scene_v2.mp4` | rigged limited 2D cartoon animation |
| Long-form 2D | independent-scene architecture from the two-minute tests | render richer short scenes separately, QA/fix, then assemble |
| 3D animation | `programmatic_3d_scifi_scene_v2.mp4` | stylized real-3D cel/low-poly animation |

The baseline is a floor. Real productions should improve scene composition, acting, spatial anchoring, audio, pacing and platform fit when useful.
