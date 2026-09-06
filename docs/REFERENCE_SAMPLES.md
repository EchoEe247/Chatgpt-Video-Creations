# Reference Samples and Lessons

This file records the capability exploration that established the repository baselines. It is intentionally concise but preserves the important accept/reject decisions so later sessions do not regress to earlier prototypes.

The MP4 files named below originated in the ChatGPT conversation that created this repo. They are not assumed to be present in every future session.

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

Future business videos should preserve the same core strengths—clarity, polish, intentional motion, and business usefulness—but should be customized to the real product, brand, audience, and platform.

---

## B. Early 2D animation prototype — rejected as final baseline

Reference file: `cartoon_animation_sample.mp4`

### What it did

- placed generated character artwork over a background;
- moved/bobbed/rotated the cutouts;
- added portal glow;
- used speech bubbles/end card.

### Why it was insufficient

It looked like **moving artwork**, not convincing cartoon animation. The characters stayed in one basic pose and did not have independent acting controls.

### Rule derived

Do not use a single static character image with only transform animation as the default 2D production method.

---

## C. Intermediate 2D animation prototype — improved but defective

Reference file: `original_scifi_cartoon_scene_sample.mp4`

### Improvements

- dialogue;
- audio;
- camera cuts;
- rudimentary mouth/blink motion;
- portal event;
- creature entrance.

### Important defects found during self-review

- mouth overlays sometimes landed on the torso instead of the face;
- characters were still mostly static cutouts;
- camera cuts were largely crops/zooms of the same source art;
- creature interaction lacked depth and reaction acting;
- voices overlapped because dialogue timing used guesses rather than measured clip durations;
- subtitles could end before the voice finished.

### Rules derived

- character face components must be anchored to the actual rig;
- dialogue windows must come from measured voice durations;
- an important event must cause visible character reactions;
- camera changes cannot substitute for missing acting.

---

## D. Current 2D animation baseline — accepted

Reference file: `original_scifi_cartoon_scene_v2.mp4`

### Key upgrade

Characters were rebuilt as **part-based rigs drawn in code** rather than using one static source image.

### Baseline features

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

### User decision

The user considered this more set and good as a 2D animation baseline.

### Default instruction

When the user later requests a **2D animation video**, this is the conceptual baseline unless a project-specific brief overrides it.

---

## E. First real 3D prototype — rejected as final baseline

Reference file: `programmatic_3d_scifi_scene.mp4`

### What it proved

- actual 3D mesh geometry;
- perspective projection;
- camera motion and parallax;
- articulated primitive character parts;
- 3D portal and environment.

### Why it was insufficient

The scene looked like a development/debug prototype:

- block/cylinder/sphere characters;
- sparse and dark set;
- weak lighting;
- limited acting;
- minimal facial animation;
- primitive creature design;
- portal dominated the composition;
- no audio stream in the rendered file.

### Rule derived

Technical 3D is not enough. A production 3D render must also have deliberate art direction, readable set dressing, stronger silhouettes, lighting, staging, audio, and acting.

---

## F. Current 3D animation baseline — accepted

Reference file: `programmatic_3d_scifi_scene_v2.mp4`

### Key upgrades

- real 3D engine rendering;
- stylized/cel character treatment;
- stronger character silhouettes;
- modeled lab environment;
- articulated limbs/head/eyes/mouths;
- camera staging across multiple shots;
- portal energy geometry;
- dynamic portal lighting;
- contact-shadow treatment;
- creature emergence;
- measured dialogue timing;
- subtitles;
- voices and SFX/ambience;
- H.264 + AAC output.

### QA event

A portal-orientation problem was caught during review and corrected before the final handoff. This is a concrete example of why actual MP4 review is part of the workflow.

### User decision

The user considered this version better and accepted it as enough to understand the current 3D capability and limit.

### Default instruction

When the user later requests a **3D animation video**, use this as the conceptual baseline unless the project brief calls for a different visual direction.

---

## Summary of the three accepted baselines

| Requested type | Accepted reference | Interpretation |
| --- | --- | --- |
| Business / professional | `programmatic_video_demo.mp4` | polished programmatic motion graphics |
| 2D animation | `original_scifi_cartoon_scene_v2.mp4` | rigged limited 2D cartoon animation |
| 3D animation | `programmatic_3d_scifi_scene_v2.mp4` | stylized real-3D cel/low-poly animation |

These three references are now the canonical starting definitions for future work.
