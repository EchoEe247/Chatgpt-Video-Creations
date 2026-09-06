# Production Workflow

For this repository, the deliverable is the rendered video. Code, scripts, and successful commands are part of the process, but they are not the thing the viewer will see.

That means the workflow has to continue through actual MP4 review and repair instead of stopping when rendering technically succeeds.

## 1. Choose the lane first

### Business / OSS release marketing

Resolve the exact user-facing project and release before building the video. Use `docs/BUSINESS_RELEASE_MARKETING.md`.

### Original animation

If this is a new show, establish the show and season foundation before episode rendering. Use `docs/ANIMATION_SHOW_WORKFLOW.md`.

### One-off animation / scene

Use the accepted 2D or 3D capability baseline directly, with normal scene planning and QA. A one-off scene does not need an artificial season framework.

## 2. Build the brief

Before production, establish what the video is actually trying to accomplish:

- objective;
- audience;
- platform and aspect ratio;
- target duration;
- hook;
- main message or story beat;
- CTA when applicable;
- source assets;
- audio needs.

For release marketing, also record exact release/version provenance.

For episodic work, load the accepted continuity input.

## 3. Plan the master before individual scenes

Define scene timestamp ranges, camera/framing, action, dialogue or on-screen text, audio cues, transitions, continuity state, and the purpose of each scene.

For long-form production, the master timeline should exist before individual scene renders so those scenes are parts of one production from the beginning.

## 4. Use one shared set geometry

When characters, props, effects, and cameras belong to one set, derive them from that set instead of independently guessing screen positions.

Examples:

- feet → floor anchor;
- portal energy → physical portal inner center/radius;
- held object → hand anchor;
- monitor content → monitor bounds.

See `docs/VISUAL_QA_STANDARDS.md`.

This rule came from visible production defects, so treat it as a hard requirement rather than optional cleanup.

## 5. Choose the right rendering architecture

### Business

Programmatic motion graphics are the normal baseline for text, UI, screenshots, charts, product demonstrations, release callouts, and other business content.

### 2D

Use rigged or part-based characters with independently controllable mouth, eyes, head, limbs, reusable set definitions, effects, and camera shots.

Do not regress to moving one static PNG per character as the default 2D method.

### 3D

Use actual geometry, perspective camera, parallax, spatial props and characters, lighting/shading, and articulated parts.

### Long-form

Render scenes independently at the richer baseline and assemble later. See `docs/LONG_FORM_SCENE_ARCHITECTURE.md`.

## 6. Keep audio deterministic

Generate or obtain voice clips, measure their real durations, and schedule dialogue and subtitle windows from those durations instead of guesses.

Prevent unintended dialogue overlap, keep music and SFX below speech when speech is the priority, and verify the final output actually contains the intended audio stream.

For long-form animation, prefer one continuous master audio timeline.

## 7. Render the actual MP4

Validate:

- codec;
- dimensions;
- FPS;
- pixel format;
- duration;
- audio presence;
- plausible file size;
- successful decode.

These checks tell us the file is technically viable. They do not replace visual review.

## 8. Review what was actually rendered

Inspect the parts a viewer will notice:

- opening and hook;
- every major scene;
- frames before and after cuts;
- dialogue close-ups;
- important effects, actions, and reactions;
- character floor contact;
- effect/source alignment;
- depth and layer order;
- subtitles;
- end card and CTA.

## 9. Repair defects

Fix important visible, audio, or continuity defects before final handoff when feasible.

For long-form work, rerender only the defective scene unless a shared state change requires a wider pass. The point of the scene architecture is to make targeted repair practical.

## 10. Acceptance

For business and one-off work: assistant QA pass + user acceptance.

For episode work: assistant QA and user review both have to pass before the episode becomes `DONE ✅` and continuity-out/canon is updated.

A script completing successfully is not an acceptance state.

## 11. Preserve the production package

For work intended for reuse, publication, or future releases, keep the source snapshot, scene plan, rig/set definitions, render settings, assets, QA notes, and final receipt.

I want later sessions to be able to continue from the accepted production state instead of reconstructing it from chat history.