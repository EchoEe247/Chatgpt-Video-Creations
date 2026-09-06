# Production Workflow

The deliverable is the rendered video, not the code that happened to render it.

## 1. Choose the operating lane

### Business / OSS release marketing

Resolve the exact user-facing product and release first. Use `docs/BUSINESS_RELEASE_MARKETING.md`.

### Original animation

If this is a new show, complete show/season planning before episode rendering. Use `docs/ANIMATION_SHOW_WORKFLOW.md`.

### One-off animation / scene

Use the established 2D or 3D capability baseline directly, with normal scene planning and QA.

## 2. Brief

Establish objective, audience, platform/aspect ratio, target duration, hook, message/story beat, CTA when applicable, source assets and audio needs.

For release marketing also record exact release/version provenance.

For episodes also load continuity input.

## 3. Master plan before scenes

Define scene timestamp ranges, camera/framing, action, dialogue/text, audio cues, transitions, continuity state and purpose.

For long-form work, this master timeline exists before individual scene renders.

## 4. Shared scene/set geometry

Sets should define floor planes and named anchors. Characters/effects/props use those anchors rather than independent guessed screen positions.

Hard examples:

- feet → floor anchor;
- portal energy → physical portal inner center/radius;
- held object → hand anchor;
- monitor content → monitor bounds.

See `docs/VISUAL_QA_STANDARDS.md`.

## 5. Render architecture

### Business

Prefer programmatic motion graphics for text, UI, screenshots, charts, product demonstrations and release callouts.

### 2D

Use rigged/part-based characters with independent mouth/eyes/head/limbs, reusable set definitions, effects and camera shots. Do not regress to moving one static PNG per character.

### 3D

Use actual geometry, perspective camera, parallax, spatial props/characters, lighting/shading and articulated parts.

### Long-form

Render scenes independently at the richer baseline and assemble later. See `docs/LONG_FORM_SCENE_ARCHITECTURE.md`.

## 6. Deterministic audio

Generate/obtain voice clips, measure real durations, schedule talking/subtitle windows from those durations, prevent unintended overlaps, keep SFX/music below dialogue and verify final audio stream.

For long-form animation, prefer one continuous master audio timeline.

## 7. Render actual MP4

Validate codec, dimensions, FPS, pixel format, duration, audio presence, plausible size and successful decode.

## 8. Review the actual video

Inspect:

- opening/hook;
- every major scene;
- before/after each scene cut;
- dialogue close-ups;
- important effects/actions/reactions;
- character floor contact;
- effect/source alignment;
- depth/layer ordering;
- subtitles;
- end card/CTA.

## 9. Repair

Fix important visible/audio/continuity defects before final handoff when feasible. In long-form work, rerender only defective scenes unless shared state changed.

## 10. Acceptance

Business/one-off work: assistant QA pass + user acceptance.

Episode work: assistant QA + user review must both pass before `DONE ✅` and continuity-out/canon update.

## 11. Preserve production package

Keep source snapshot, scene plan, rig/set definitions, render settings, assets, QA notes and final receipt when the work is intended for reuse or publication.
