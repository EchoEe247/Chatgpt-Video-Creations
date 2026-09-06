# Production Workflow

This is the default workflow for real video work in this repository.

The central rule is simple: **the deliverable is the rendered video, not the code that happened to render it.**

## 1. Define the production brief

Before rendering, establish the minimum useful brief:

- video lane: business / 2D / 3D;
- objective: sell, explain, entertain, demonstrate, announce, etc.;
- platform and aspect ratio;
- target duration;
- audience;
- hook;
- core message;
- CTA if applicable;
- source assets available;
- audio requirements;
- whether multiple variants are needed.

Do not ask unnecessary questions when the user has already supplied enough context. Infer sensible defaults from the canonical lane definitions in `CAPABILITY_BASELINES.md`.

## 2. Plan scenes before implementation

Create a compact scene plan with:

- timestamp range;
- visual action;
- camera/framing;
- text/dialogue;
- audio cue;
- transition/effect;
- purpose of the scene.

For short-form business video, prioritize the first 1–2 seconds.

For animation, prioritize acting beats and reactions rather than constant motion.

## 3. Choose the rendering architecture

### Professional / business

Prefer programmatic motion graphics when the content is driven by text, data, UI, screenshots, charts, product imagery, or simple branded assets.

Typical stack may include:

- Python/Pillow for frame generation;
- FFmpeg for encoding/compositing/audio;
- Remotion/React when available and useful;
- generated or supplied images/assets;
- screenshots/product images;
- captions and timed overlays.

### 2D animation

Prefer rigged/part-based character construction or pose-sheet animation over moving a single static cutout.

Useful building blocks:

- torso/head/limbs as separate layers;
- multiple mouth states;
- eye/pupil states;
- blink states;
- pose variants;
- foreground/background layers;
- independent effects animation;
- camera crops/cuts;
- timed dialogue/subtitles;
- sound effects and ambience.

### 3D animation

Use an actual 3D renderer/geometry pipeline when the user asks for 3D.

Required signals of genuine 3D include:

- 3D geometry;
- perspective camera;
- parallax;
- spatially placed characters and props;
- lighting/shading;
- articulated parts or rigging;
- camera motion through 3D space.

Do not substitute flat sprites with zoom effects and call the result 3D.

## 4. Build for the target platform

Common defaults:

- TikTok / Reels / Shorts: 9:16 vertical;
- YouTube / landscape explainer / animation scene: 16:9;
- square social creative: 1:1 when explicitly useful.

Use H.264 with `yuv420p` for broad compatibility unless another format is required.

Aim for clean decode compatibility on mobile devices.

## 5. Audio timing must be deterministic

For dialogue:

1. generate or obtain the voice clip;
2. measure its real duration;
3. schedule the subtitle and character talking window from that duration;
4. verify consecutive dialogue clips do not unintentionally overlap;
5. mix ambience/SFX below speech;
6. validate that the final MP4 actually contains an audio stream.

The early 2D exploration exposed a concrete failure mode: scheduling dialogue by guessed timing caused overlapping voices and subtitles ending before speech. Do not repeat this.

## 6. Render the actual MP4

A successful script execution is not sufficient.

Render the real target file and validate at minimum:

- codec;
- dimensions;
- frame rate;
- pixel format;
- duration;
- presence/absence of audio as intended;
- file size is plausible;
- decode succeeds.

Use `ffprobe` or an equivalent inspection tool.

## 7. Review the finished video itself

This step is mandatory for serious work.

Sample frames across the timeline and inspect the actual rendered video. When practical, inspect:

- opening frame;
- each major scene transition;
- dialogue close-ups;
- effect/portal/event frames;
- reaction frames;
- end card/CTA.

Check for:

### Visual defects

- text clipping;
- incorrect layer ordering;
- detached facial features;
- characters floating or intersecting badly;
- inconsistent scale;
- unreadable subtitles;
- awkward camera crops;
- black/empty frames;
- broken transparency;
- portal/effect orientation errors;
- poor lighting/readability.

### Animation defects

- characters that remain static for too long;
- motion with no acting purpose;
- mouth animation disconnected from dialogue;
- no reaction to important events;
- unnatural limb movement;
- insufficient anticipation/recoil/follow-through;
- repeated identical shots disguised as zooms.

### Audio defects

- dialogue overlap;
- subtitle mismatch;
- missing audio stream;
- SFX louder than speech;
- abrupt cuts/clicks;
- robotic voice quality that harms the production.

## 8. Fix visible defects before handoff

If review finds a clear defect, fix it before telling the user the video is finished when feasible.

Examples from the capability exploration:

- early 2D mouth overlays landed on the characters' torsos → rebuilt characters as independently rigged parts;
- dialogue overlapped → measured voice duration and rescheduled clips;
- first 3D test looked like debug geometry → upgraded to cel/stylized rendering, stronger set dressing, lighting, articulated posing, audio, and better camera staging;
- portal orientation was wrong during a 3D review → corrected the geometry orientation before final handoff.

## 9. Deliver with concise production facts

When handing the file to the user, provide:

- a direct MP4 link;
- duration;
- resolution/aspect ratio;
- key features only when useful;
- any meaningful limitation that remains.

Do not drown the handoff in implementation details unless the user asks.

## 10. Preserve reusable production work

For a real project, retain the reusable pieces when appropriate:

- source script/code;
- scene plan;
- character rig definitions;
- reusable motion components;
- audio timing data;
- source assets;
- render command/preset;
- QA notes;
- final render receipt.

Prefer a reproducible production package over a one-off script when the video pattern is likely to be reused.

## 11. Iteration policy

Use this loop:

**brief → scene plan → implementation → render → technical validation → visual/audio review → fix → re-render → final handoff**

Stop when the video is fit for the requested use, not when every theoretical enhancement has been exhausted.
