# Reference Samples and Lessons

This file preserves the production experiments that established the current baselines.

I keep both accepted and rejected examples because the failures matter too. A fresh session should be able to see not only what worked, but what looked wrong and why we stopped using it as the default.

The MP4 names below came from ChatGPT production sessions. The files are references to those accepted/rejected results and are not assumed to exist in every future session.

---

## A. Professional / business motion sample — accepted

Reference file: `programmatic_video_demo.mp4`

### What it proved

- 720×1280 vertical composition;
- 24 FPS H.264;
- animated typography;
- motion graphics;
- dashboard cards;
- animated charts and data;
- clean transitions and easing;
- programmatic effects;
- finished MP4 rendering without stock footage.

### Decision

I accepted this as a useful baseline for the professional/business lane.

### What that means now

Future business videos should keep the clarity, polish, intentional motion, and practical usefulness, but they should be customized to the actual project, release, brand, audience, and platform.

For OSS work specifically, the newer rule is that release-specific marketing also needs to be version-grounded.

---

## B. Early 2D animation prototype — rejected as the final baseline

Reference file: `cartoon_animation_sample.mp4`

This version placed generated character artwork over a background and mostly moved, bobbed, or rotated the cutouts.

The problem was visible: it looked like moving artwork rather than convincing cartoon animation.

**Rule that came from it:** one static character image with only transform animation is not the default 2D production method.

---

## C. Intermediate 2D prototype — improved, but still defective

Reference file: `original_scifi_cartoon_scene_sample.mp4`

The production moved forward, but review found important problems:

- mouth overlays could land on the torso instead of the face;
- characters still behaved mostly like static cutouts;
- camera cuts were largely crops or zooms of the same source art;
- creature interaction lacked depth and reaction acting;
- voices overlapped because dialogue timing was guessed;
- subtitles could end before speech.

**Rules that came from it:** face components inherit the rig, dialogue windows use measured clip durations, important events need visible reactions, and camera changes are not a substitute for acting.

---

## D. Current short-form 2D visual baseline — accepted

Reference file: `original_scifi_cartoon_scene_v2.mp4`

Characters were rebuilt as part-based rigs drawn in code.

Accepted baseline features:

- independent character parts;
- head movement;
- pupil direction;
- blinking;
- multiple mouth states;
- articulated arms and hands;
- recoil and body response;
- animated portal vortex;
- creature entrance;
- shot changes and close-ups;
- dialogue, subtitles, ambience, and SFX;
- corrected dialogue overlap.

I accepted this as the short-form 2D baseline.

**Default:** when a future request says `2D animation video`, start here unless the actual project brief needs something different.

---

## E. First real 3D prototype — rejected as the final baseline

Reference file: `programmatic_3d_scifi_scene.mp4`

It proved that actual 3D geometry, perspective, parallax, and articulated primitive parts were working.

But the result still looked like a development/debug prototype: primitive characters, a sparse dark set, weak lighting, limited acting, primitive creature design, portal-dominated composition, and no audio stream.

**Rule that came from it:** technical 3D is not enough by itself. Production 3D also needs art direction, staging, readable set dressing, lighting, acting, and audio.

---

## F. Stylized 3D capability baseline — historically accepted

Reference file: `programmatic_3d_scifi_scene_v2.mp4`

Key upgrades included:

- real 3D engine rendering;
- stylized/cel character treatment;
- stronger silhouettes;
- modeled lab environment;
- articulated limbs, head, eyes, and mouths;
- multiple camera shots;
- portal energy geometry and lighting;
- contact-shadow treatment;
- creature emergence;
- measured dialogue timing;
- subtitles;
- voices, SFX, and ambience;
- H.264 + AAC output.

A portal-orientation defect was caught during review and fixed before handoff. I accepted the final result as enough to establish the current 3D capability and its limits.

---

## G. First two-minute 2D workflow proof — assembly accepted, visual quality not promoted

Reference file: `two_minute_2d_animation_scene_based.mp4`

The purpose was to answer a practical question: can a two-minute animation be planned as multiple scenes and still arrive as one coherent MP4?

It proved that:

- 12 planned scene segments could form one continuous two-minute timeline;
- recurring character and set designs could stay coherent;
- one master audio timeline could span scene boundaries;
- normal hard cuts could hide production boundaries cleanly.

The compromise was that the full two-minute render had to be simplified to 12 FPS with cached pose states to fit runtime constraints. That dropped visual animation quality below the accepted short 2D V2 baseline.

**Decision:** keep this as an architecture proof only. Do not turn the lower-detail 12 FPS implementation into the new 2D quality baseline.

---

## H. Independent-scene long-form 2D proof — architecture accepted, spatial QA tightened

Reference lineage:

- `two_minute_2d_animation_rich_scenes_final_v2.mp4`
- `two_minute_2d_animation_v3_updated.mp4`

The goal was to keep the richer 2D scene quality while scaling to a longer runtime by rendering scenes independently, reviewing/replacing defects, and then assembling the master.

It proved that:

- 12 scenes can be rendered independently and assembled without black gaps or broken seams;
- bad scenes can be rerendered without redoing the whole episode;
- richer 18–24 FPS per-frame animation scales better than one giant simplified render;
- continuous master audio remains compatible with scene replacement;
- 1280×720 / 24 FPS final delivery is practical after scene-based production.

The V3 review still exposed important spatial problems that became permanent QA rules:

- characters should be positioned by their **feet on the floor**, not approximate sprite bounds;
- the green portal energy circle should be **concentric and aligned with the physical gray/black portal frame**;
- set, effect, and camera placement should derive from one canonical geometry definition rather than unrelated guessed screen-coordinate tables.

Those are now hard rules in `docs/VISUAL_QA_STANDARDS.md` and the set-anchor template.

**Decision:** the independent-scene system is the long-form production architecture baseline. The short 2D V2 remains the visual/acting quality baseline to match or exceed inside each scene.

---

## Current respectful cinematic work-in-progress references

### RIDGELINE — A Descent — latest mountain-bike candidate

Production: `productions/standalone/ridgeline`

User quality judgment: **respectful**.

This is the latest mountain-bike candidate the user means when referring to the respectful MTB video. It is worth keeping on-device, continuing to improve, and potentially releasing later. It is **not** declared finished and is not automatically a realistic/cinematic baseline.

### VELOCITY — A Highway Study — latest highway-driving recreation

Latest reviewed production: `productions/standalone/velocity-recreation`

User quality judgment: **respectful**.

This is the latest highway-driving candidate the user means when referring to the respectful car video. It is worth preserving, continuing to improve, and potentially releasing later. The user-facing film title remains **VELOCITY — A Highway Study**; the repository production is the recreation package. Respectful does not mean finished or baseline-promoted.

---

## I. THE EIGHTH HOUR — Severance-inspired candidate — rejected / failed

User quality judgment: **trash / failed**.

The production audit found that the candidate had regressed below the established workflow: scratch proxy humans and environments were used as finished content, meaningful moving previs/look-dev were skipped, the final picture path became primitive, and the audio treatment was thin.

**Decision:** preserve as failure evidence only. It is not a cinematic baseline and should not be incrementally polished into one. The failure shape is encoded in the strict final-quality contract.

**Reusable lesson:** a technically complete render can still be a foundational production failure when asset quality, visual development, environment work and finishing are below the promised cinematic target.

---

## J. AETHERFALL — THE LAST LIGHT — Avatar/alien concept candidate — not promoted

File: `aetherfall-last-light.mp4`

User quality judgment: **medium-bad**.

In that user review, the environment was stronger than the then-current LAX candidate, but the Avatar-replication concept itself did not land for the user, the characters needed to be better, and the audio needed improvement.

**Decision:** do not promote it. A future production may reuse validated workflow pieces, but not treat this candidate's concept, character quality or audio result as the target.

---

## K. LAX — Final Approach — airplane candidate — paused, not promoted

Production: `productions/standalone/lax-arrival`

Current preserved candidate: `final/lax-final-v11.mp4`

Candidate SHA-256: `8515f639e98453b2438c32ef038f186c439df2755c64aa5206a8c811e9aa840d`

User quality judgment remains **below respectful / salvageable**. The user explicitly wants this work preserved and considers it worth resuming when they are actually looking for an airplane-flight, approach, landing or related flying video. That is a resume decision, **not** promotion to the repo's `respectful` quality status.

The production made real progress after the original rejection:

- the imported aircraft's forward-axis/orientation error was diagnosed and corrected in the scene hierarchy;
- the missing-terrain/blue-ground failure was diagnosed and replaced with continuous LA-basin and airport ground surfaces;
- LAX-specific terminal/ramp/airfield structure was expanded;
- native temporal sampling was raised from the earlier 2 fps salvage path to 6 fps / 720 genuine Blender frames for the later production path;
- v11 rebuilt the externally criticized 22–65 s section with closer/moving cameras, stabilized close shots, procedural ground variation and held lighting continuity;
- v11 is exactly 120 seconds, 1280×720, 24 fps / 2880 frames, AAC stereo and decode-clean.

It is still not ready for promotion. The user continued to find motion insufficiently smooth, the early-ground artifact pass was not completed, the planned 95–104 s touchdown-mechanics rerender did not complete, and control-surface/gear physics, environment/material realism, lighting continuity and aviation-audio dynamics still need work.

**Decision:** pause here. Do not spend more cycles unless the user requests this class of aviation video again. When resumed, continue from the saved v11 scene/candidate instead of restarting. The authoritative continuation order and exact unresolved defects are in [`LAX_FINAL_APPROACH_HANDOFF.md`](LAX_FINAL_APPROACH_HANDOFF.md).

**Reusable lessons:** motion magnitude is not semantic motion; interpolation cannot replace adequate native temporal sampling; environment asset presence is not environment completion; final-camera review must catch ground overlap/z-fighting and horizon pop-in; flight-to-contact physics must be proven before final rendering; technical validity does not imply visual impressiveness.

---

## Canonical interpretation

| Requested type | Accepted reference / architecture | What it means |
| --- | --- | --- |
| Business / professional | `programmatic_video_demo.mp4` | polished programmatic motion graphics, version-grounded for OSS release work |
| Short 2D animation | `original_scifi_cartoon_scene_v2.mp4` | rigged limited 2D cartoon animation |
| Long-form 2D | independent-scene architecture from the two-minute tests | render richer short scenes separately, QA/fix, then assemble |
| 3D animation | `programmatic_3d_scifi_scene_v2.mp4` | stylized real-3D cel/low-poly animation |

The baseline is the floor only for the style/capability it actually demonstrates. Real productions should improve composition, acting, spatial anchoring, audio, pacing, and platform fit when the improvement is actually visible or useful.

There is currently **no accepted realistic/cinematic visual baseline**. **RIDGELINE — A Descent** and the latest reviewed **VELOCITY — A Highway Study** recreation are respectful work-in-progress references, not finished/promoted realism baselines. **LAX — Final Approach**, **AETHERFALL — THE LAST LIGHT**, and **THE EIGHTH HOUR** are below that threshold in their current preserved/reported states.