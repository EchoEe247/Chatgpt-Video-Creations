# Character Production

## Purpose

Character-heavy work should not regress to scratch-built proxy humans merely because local geometry is possible. The production target is the strongest practical character performance under local control.

The default character ladder is:

**reuse a suitable local character → source a legitimately reusable rigged character → source reusable motion/actions → retarget and adapt locally → author transitions/IK/interactions locally → model or rig only what is missing**

Scratch-built proxy geometry remains useful for runtime smoke tests, blocking and diagnostics. It is not the default quality strategy for a finished character shot.

## Source nouns, author verbs

Treat generic production nouns as candidates for reuse or sourcing: a body, rig, jacket, bicycle, car, corridor, tree, weapon, material, footstep or walk cycle.

Keep the production verbs under local direction: runs, hesitates, looks, reaches, aims, pedals, crashes, reacts, accelerates, reveals, cuts, lights, mixes and resolves.

An external mesh or action is a raw production input. It does not own the performance or the film.

## Make-vs-source decision

Before building a high-impact character asset from scratch, record an `asset_strategy` requirement in the director brief.

Prefer sourcing when a licensed resource materially improves quality or saves meaningful production time and can be adapted within the runtime budget.

Prefer local authorship when the element is production-specific, adaptation would cost more than construction, suitable licensing cannot be established, or the locally authored behavior itself is the creative value.

Structural suitability matters as much as visual resemblance. Character checks may include:

- usable humanoid skeleton and stable bone naming;
- clean skinning/deformation at shoulders, hips, knees and elbows;
- separate or controllable props/accessories where interaction requires them;
- compatible scale/orientation and manageable polygon/material cost;
- enough rig control for hand placement, gaze and contact poses;
- animation/root-motion behavior that can be retargeted predictably.

## Mixamo

Adobe Mixamo is a preferred first-pass source for bipedal humanoid characters, auto-rigging and reusable animation clips when the current terms fit the production.

As verified against Adobe's Mixamo FAQ on 2026-09-28:

- Mixamo is currently available free with an eligible Adobe ID and does not require a Creative Cloud subscription;
- Adobe states its characters and animations may be used royalty-free in personal, commercial and nonprofit projects, including films;
- the auto-rigger and animation library target bipedal humanoids;
- current Adobe guidance excludes Enterprise/Federated IDs and China-coded accounts;
- current Adobe licensing guidance prohibits redistribution of raw Mixamo character/animation files as standalone assets.

Terms can change. Reverify the current Adobe terms at acquisition time. Keep downloaded Mixamo payloads local unless current terms explicitly permit redistribution; track source, retrieval date, usage and modifications in production provenance. Never commit restricted raw payloads merely because the final rendered video may be distributed.

The `provider.mixamo` catalog entry is discovery metadata and does not satisfy a concrete `asset_strategy` requirement by itself. After choosing/downloading a character or action, bind the production to the specific asset/provenance record before rendering.

Mixamo is an animation ingredient, not an automatic directing system. After acquisition, local production still owns retargeting, root-motion policy, action selection, NLA/action blending, timing, transition poses, hand/foot contacts, IK, interactions, staging, cameras, lighting, effects, rendering, editing and QA.

## Performance assembly

A generic clip such as `run` or `walk` is a motion primitive. Build the actual performance from authored beats, for example:

**run → decelerate → plant → turn → raise weapon → acquire target → fire → recoil → recover**

Use NLA/action blending for reusable motion, then layer local keyframes/constraints/IK where a shot needs exact contact or intent. Do not force a stock clip through a story beat when a short authored transition pose would read better.

Human capture is optional input, never a dependency. Agent-controlled Blender remains the default execution path.

## Local authorship that remains required

Even when every visible character mesh starts from a free asset, the workflow normally authors locally:

- casting/character selection for the shot;
- scale, proportions and material adaptation;
- retargeting and animation blending;
- custom poses, timing and reactions;
- hand/foot/prop contacts and IK;
- blocking and world-space continuity;
- camera grammar and framing;
- lighting and atmosphere;
- particles/VFX and interaction effects;
- dialogue/audio synchronization and sound design;
- final rendering, compositing, edit and QA.

This is why a locally rendered production may legitimately contain external assets without claiming every polygon was modeled locally.

## Authorship/provenance terminology

Use precise language in production records:

- **externally sourced asset** — a mesh, rig, action, texture, audio file or other input acquired under verified terms;
- **externally generated service output** — content produced by an external generation service;
- **locally authored asset** — created in this repository/workspace;
- **locally adapted asset** — external/local input materially modified for the production;
- **locally animated** — performance/timing assembled or authored locally;
- **locally rendered** — final picture frames calculated by the local renderer;
- **locally assembled** — edit/composite/audio master produced locally.

Do not collapse these into the misleading claim that every component was created from scratch locally.

## QA

Character review must use motion evidence, not still frames alone. Inspect at normal speed for:

- foot sliding and ground contact;
- root-motion discontinuities;
- T-pose or bind-pose flashes;
- limb inversion, clipping and bad deformation;
- hands missing controls/props;
- head/gaze direction contradicting the beat;
- abrupt action transitions;
- floating characters;
- animation playing backward or at implausible speed;
- camera cuts hiding rather than solving animation defects.

A technically valid FBX/action import is not a character-performance PASS.