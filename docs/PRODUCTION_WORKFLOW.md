# Production Workflow

For this repository, the deliverable is the rendered video. Code, scripts, and successful commands are part of the process, but they are not the thing the viewer will see.

The workflow therefore continues through actual MP4 review and repair instead of stopping when rendering technically succeeds.

The broader operating model is documented in `docs/OPERATING_MODEL.md`.

## Local Workspace-era verification

Current ChatGPT sessions should use Local Workspace during the entire render/review loop rather than waiting for the user to discover media defects. Probe and decode-check each candidate, inspect audio continuity, compare against a known-good baseline when available, generate a whole-video contact sheet, inspect declared review points, and inspect exact scene seams.

The same operations are available through `scripts/videoctl.py`. `scripts/productionctl.py` owns production state, deterministic gates, repair history, and the final-user-review transition.

See `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`.

## 0. Determine the maturity state

Before changing an area, decide whether it is still being discovered or is mature enough to operate from established rules.

Use interactive discovery when visual judgment, creative direction, architecture, timing, or measurements are unresolved.

Use established contracts and validation when the relationship is already understood. Do not re-guess solved geometry, release provenance, continuity, render settings, or other formalized constraints.

For a meaningful change to an area covered by a validated baseline, record which baseline is the comparison point before editing.

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

Separate established constraints from provisional creative choices. A scene plan can contain both, but future agents need to know which values are authoritative and which are still being explored.

## 4. Use one shared set geometry

When characters, props, effects, and cameras belong to one set, derive them from that set instead of independently guessing screen positions.

Examples:

- feet → floor anchor;
- portal energy → physical portal inner center/radius;
- held object → hand anchor;
- monitor content → monitor bounds.

See `docs/SCENE_GEOMETRY.md` and `docs/VISUAL_QA_STANDARDS.md`.

This rule came from visible production defects, so treat the relationship as a hard requirement. The exact numeric measurements still have to be validated in rendered output before they become known-good production values.

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

Timing becomes a reusable rule only after the timing relationship is understood and validated. Do not preserve a guessed duration merely because it worked once by accident.

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

When a visual failure repeats, ask whether it reveals an underlying reusable relationship. If yes, formalize the relationship after it is understood instead of only patching that one frame.

## 9. Repair defects

Fix important visible, audio, or continuity defects before final handoff when feasible.

For long-form work, rerender only the defective scene unless a shared state change requires a wider pass. The point of the scene architecture is to make targeted repair practical.

When a validated baseline covers the broken behavior, compare the candidate against that baseline before making broad changes.

## 10. Acceptance

The default review policy is `final_candidate_only`.

Technical failures and assistant-detected visual/audio/continuity defects return to an internal repair loop. Do not ask the user to review those intermediate candidates merely to discover whether the repair worked.

For business, one-off, and episode work, the normal user-facing handoff happens after deterministic QA and assistant review pass. User acceptance is the final gate.

For episode work, technical, assistant, and user gates all have to pass before the episode becomes `DONE ✅` and continuity-out/canon is updated.

A script completing successfully is not an acceptance state.

## 11. Preserve the production package

For work intended for reuse, publication, or future releases, keep the source snapshot, scene plan, rig/set definitions, render settings, assets, QA notes, and final receipt.

Later sessions should be able to continue from the accepted production state instead of reconstructing it from chat history.

## 12. Promote a validated baseline only when useful

Not every accepted video needs a new B-series baseline.

Promote a baseline when the state represents a reusable known-good capability or regression reference. Follow `baselines/README.md` and register the exact evidence in `baselines/registry.json`.

For visual baselines, preserve the exact artifact and require visual + user review. For technical-only baselines, scope the claim narrowly and mark visual review `NOT_REQUIRED` rather than implying visual correctness.

The end state is:

**accepted production → preserve evidence → promote baseline when warranted → reuse/automate the understood parts → keep checking real output**