# Director Spec Workflow

This workflow exists so finished quality does not depend on whichever frontier model happens to be driving the session.

The production model may improve the plan, renderer, or review, but the **directing decisions must be externalized into durable files** that a weaker model, Hermes, or a later ChatGPT session can execute and audit.

## Core rule

For serious narrative, cinematic, launch, music, or explainer work, do not jump from a one-sentence idea directly into rendering.

Use:

**reference decomposition → director brief → storyboard/shot grammar → audio plan → renderer choice → scene production → motion/audio review → targeted repair → final QA**

The brief is a production contract, not decorative documentation.

## Reference decomposition

When a reference film or strong public example is available, study the technique rather than copying its protected expression.

Extract reusable production properties such as:

- story spine and emotional turn points;
- shot duration distribution and pacing changes;
- what visibly changes inside each shot;
- camera position, lens feel, movement, inertia, framing correction, and intentional imperfection;
- palette progression and contrast hierarchy;
- typography behavior and title-safe regions;
- transition motivation;
- foreground/midground/background separation;
- visual density and negative-space rules;
- music structure, dialogue/narration timing, silence, effects, and transition cues;
- the relationship between audio beats and cuts;
- what the reference deliberately avoids.

Do not copy characters, dialogue, logos, unique compositions, or other expressive elements merely because a reference is being studied.

## Director brief

Create a production-specific director brief before expensive rendering. Start from `templates/director-brief.json`.

The brief should answer:

1. **What is the audience supposed to feel and understand?**
2. **What changes over time?** A film needs progression, not a slideshow of competent frames.
3. **What happens on screen in every shot?** Camera travel alone is not automatically meaningful motion.
4. **What is the visual grammar?** Palette, framing, depth, texture, typography, lighting, animation style.
5. **What is the camera grammar?** Static, dolly, orbit, handheld simulation, parallax, focus/exposure behavior, or deliberate stillness.
6. **What is the audio grammar?** Narration, score, ambience, effects, silence, and synchronization rules.
7. **How are cuts motivated?** Action, sound, shape, movement, reveal, contrast, or narrative beat.
8. **Which shots carry the story?** Identify the hero shots that deserve extra render/review budget.
9. **What is forbidden?** Generic idle particles, decorative motion without narrative purpose, unreadable text, accidental freeze spans, repetitive camera moves, and visual motifs that drift without explanation.

## Asset-needs decomposition before renderer

After the story/visual grammar is clear, identify high-impact production nouns before expensive construction. Put them in the director brief `asset_strategy` and intentionally choose `reuse_local`, `source_free`, `author_local`, `hybrid` or `unresolved`.

Do not silently interpret an empty shot `assets` list as permission to build a major character, vehicle or environment from scratch. The high-impact make-vs-source decision belongs above the shot implementation.

For sourced/hybrid needs, specify structural requirements, license requirements and the adaptation plan. For locally authored/hybrid needs, state what is intentionally being created locally. The compiler carries this into the execution plan and exposes unresolved requirements as blockers.

Use **source nouns, author verbs**: acquire a suitable rig/car/material when that saves time and raises quality; locally direct the performance, motion, staging, camera, lighting, timing and edit.

## Previs, look-dev, and compositing decisions

For serious 3D work, the director brief must decide whether moving previs and representative look-dev are required. New templates start these decisions unresolved so a fresh session cannot jump directly to expensive rendering by omission.

Previs proves timing, blocking, camera grammar and screen geography. Look-dev proves representative materials, lighting, reflections, contact and environment integration. These are different questions and need different evidence.

For Blender shots, declare `compositing.mode`. Use multipass/hybrid only when the named AOVs solve a real finishing need; use `beauty_only` intentionally when extra passes would add cost without useful control.

See `docs/VISUAL_DEVELOPMENT.md`.

## Storyboard before renderer

The storyboard is a directorial artifact, not just a list of timestamps.

For each shot record:

- start/end or duration;
- narrative purpose;
- visible event;
- camera state and movement;
- subject movement;
- depth layers;
- dominant palette/value range;
- transition in/out;
- audio cue;
- continuity dependencies;
- renderer/asset needs;
- review point(s);
- failure modes to inspect.

A shot may be quiet, but if nothing changes, that stillness must be intentional and supported by composition/audio.

## Time the viewer, not the code

Before locking a shot, list the **reads** the viewer must understand in order.

A read is one piece of information or emotion the eye has to find and register: a new object, a cause, a reaction, a reveal, a choice, or a change of state.

Rules:

- stage one primary read at a time;
- lead the eye before an important action with gaze, motion, framing, light, or sound;
- separate cause and reaction when both matter;
- fast physical actions may be brief, but their meaning needs anticipation and/or a hold;
- subtle, small, distant, or unfamiliar information needs more screen time than obvious central action;
- once the reads have landed, do not pad the shot merely to hit a predetermined duration.

This is especially important for generated animation: the agent already knows what the code is supposed to mean, while the viewer sees the event once at normal speed.

## Scene is not the same thing as shot

A long-form production may keep 10–20 second **scene packages** for rendering/recovery, but those packages should not automatically become 10–20 second unbroken shots.

Dynamic story-led work often benefits from several shorter shots inside one scene package. Use the story, music, action and visual idea to choose duration. As a starting heuristic, many energetic shots can live around 1.5–6 seconds, with longer holds reserved for moments that earn stillness.

Each shot should have one immediately readable focal event. Vary shot scale and camera behavior across the sequence; do not make every scene feel like the same 15-second camera move with different geometry.

## Deterministic frame rendering

When practical, make each frame a deterministic function of absolute timeline time plus stable seeded randomness.

This enables:

- parallel and out-of-order frame rendering;
- exact resume after interruption;
- reliable re-render of only damaged ranges;
- reproducible contact sheets and comparisons;
- no real-time capture stutter;
- safe multi-agent work on separate chapters/shots.

Avoid hidden mutable animation state that requires rendering every prior frame to reconstruct the current one. If hand-drawn jitter or noise is desired, seed it predictably from time/object identity so the look remains lively without becoming non-reproducible.

## Audio is planned with the picture

Do not bolt audio on after the visual cut is locked.

For story-led work, establish narration/dialogue timing and broad musical structure before final scene timing. This allows visual actions, reveals, transitions, and cuts to land on meaningful beats.

Keep separate stems when practical:

- narration/dialogue;
- score;
- ambience;
- effects.

Final mastering happens after scene timing is stable, but timing decisions should already account for the audio.

## Renderer is a consequence of the shot

Do not force every shot through one engine.

Choose the cheapest local path that can achieve the intended look:

- Canvas/SVG/Pillow for graphic, illustrative, typographic, schematic, or stylized 2D work;
- Three.js/WebGL for real-time spatial, particle, camera, or shader-heavy work;
- Blender for authored 3D assets, controlled lighting, rigging, physically coherent camera moves, and rendered geometry;
- FFmpeg for compositing, transitions, temporal effects, reframing, and deterministic assembly;
- free licensed assets when they materially improve the shot.

The target is not technical purity. The target is a coherent film produced under local control.

## Motion must carry information

Every scene should distinguish between:

- **narrative motion** — changes what the viewer learns or feels;
- **subject motion** — character/object action;
- **camera motion** — changes viewpoint;
- **environmental motion** — atmosphere, traffic, particles, light;
- **decorative motion** — visual energy with little semantic value.

Prefer narrative and subject motion. Camera/environmental motion support them. Decorative motion should not be used to disguise a static scene.

When a live-camera feel is desired, describe the physical camera situation rather than adding arbitrary shake. Camera position, operator constraints, inertia, delayed reframing, focus behavior, and exposure response should come from a plausible physical setup.

## Model-independent handoff

The production should remain understandable after the directing model disappears.

A fresh agent should be able to recover:

- the director brief;
- the storyboard/scene plan;
- source/provenance;
- asset licenses;
- render commands;
- exact candidate hash;
- QA evidence;
- assistant findings;
- repair history;
- known limitations;
- current next action.

Do not rely on hidden conversation context for critical creative constraints.

## Cross-model learning rule

A stronger model may be used as a research subject or temporary director, but its useful behavior should be converted into reusable repository knowledge.

When a strong result appears:

1. identify the specific decisions that improved it;
2. separate transferable method from model-specific luck;
3. encode the method into the brief/template/tooling/checklist;
4. reproduce the method with a different agent/session;
5. keep it only if quality survives the handoff.

A workflow improvement is not established until another agent can use it.

## Quality review

Technical QA is necessary but not sufficient.

Before user review, inspect:

- whether the story reads without explanation;
- whether every scene has a clear job;
- whether hero shots justify their screen time;
- whether motion is visible at final scale;
- whether the camera grammar repeats too much;
- whether composition survives on a phone-sized display;
- whether audio transitions feel intentional;
- whether narration and visual information compete;
- whether the film has escalation, contrast, and release;
- whether the ending changes the meaning of what came before;
- whether any scene looks like filler.

Use motion clips, not only stills, for motion judgments.

## Current lesson from the Opus 5.5 wave

Recent high-quality code-rendered examples reinforce several useful practices:

- write a specific storyboard/director document before coding scenes;
- make every shot contain an intentional visible event;
- keep character/design/palette rules stable across independently built segments;
- motivate cuts with action, sound, or transformation;
- render deterministically frame-by-frame instead of relying on real-time capture;
- synchronize audio and image structurally rather than adding music at the end;
- use parallel scene work only behind a shared central directing spec;
- review generated stills/clips and revise before final assembly.

Those are workflow properties. They should survive whether the active director is ChatGPT, Astra, Opus, Hermes, or another capable agent.