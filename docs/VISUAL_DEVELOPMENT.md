# Visual Development: Previs, Look-Dev, and Compositing

## Purpose

Serious 3D production should not discover basic camera, timing, material, lighting or compositing problems during the expensive final render.

Use:

**director brief → assets → previs → look development → compositing strategy → final animation/render → composite → QA**

These stages are evidence gates, not decorative documentation.

## Previs

Previs is a cheap moving proof of the film before final-quality rendering. It should use the intended shot order, approximate timing, camera positions/moves, subject blocking and screen geography. Primitive geometry and low-cost materials are acceptable because the purpose is editorial/spatial validation.

A required previs is approved only after a reviewable artifact exists and the session has checked the intended risks, normally:

- shot timing and viewer reads;
- actor/vehicle blocking;
- camera direction and shot scale;
- screen direction/geography;
- cause/reaction spacing;
- transitions and cuts;
- obvious collisions/occlusion;
- whether hero shots deserve their render budget.

Do not spend final shading/render time fixing a problem that a gray-box moving previs would have exposed.

## Look development

Look-dev proves how representative production assets behave under the intended visual conditions before a full sequence render.

For serious 3D, representative frames should stress the conditions most likely to fail:

- hero material response;
- brightest and darkest lighting;
- reflections/specular behavior;
- contact shadows and grounding;
- atmosphere/depth;
- environment integration;
- skin/cloth/paint/metal response as applicable;
- final-scale detail and readability;
- at least one intended delivery/grade context when finishing materially changes the image.

A successful import is not look-dev approval. A character or car may be structurally correct yet still look synthetic because its materials, reflections, contact, lighting or environment integration are weak.

## Compositing strategy

Every new Blender shot should deliberately choose one of:

- `beauty_only` — the final beauty render is sufficient; document this intentionally;
- `multipass` — render separate passes/AOVs for downstream control;
- `hybrid` — beauty plus selected utility/effect passes;
- `unresolved` — blocker for a Blender shot;
- `not_applicable` — non-Blender path.

Use multipass/hybrid only when it buys meaningful control. Do not produce AOVs as ritual overhead.

Canonical names understood by the execution-plan validator are `beauty`, `depth`, `normal`, `vector`, `diffuse_direct`, `diffuse_indirect`, `glossy_direct`, `glossy_indirect`, `emission`, `shadow`, `mist`, `ambient_occlusion`, `object_index`, `material_index`, `cryptomatte_object`, and `cryptomatte_material`. Production-specific shader AOVs use an `aov:<name>` identifier.

Common useful passes include:

- beauty/combined;
- depth/Z;
- object or material masks / Cryptomatte-equivalent IDs;
- diffuse/direct/indirect components where supported and useful;
- glossy/specular;
- emission;
- shadow/contact;
- mist/volume;
- normal/vector data when a downstream effect actually needs them;
- production-specific FX layers.

The exact pass list depends on renderer support and the shot. The director brief records the desired passes and the reason for them.

## Why multipass matters

A pass-based shot can allow local finishing changes without rerendering expensive animation/geometry, for example:

- rebalance hero reflections;
- reduce or strengthen emission/streetlights;
- deepen contact shadows;
- use Z/mist for atmosphere and depth separation;
- isolate a hero character/vehicle for grading;
- composite smoke/particles independently;
- adjust background/foreground contrast separately;
- repair a finishing issue without invalidating correct animation.

This is not a promise that every correction can happen in compositing. Broken geometry, bad animation, wrong light placement or missing interactions must be fixed upstream.

## Pixel/runtime rule

The local device budget matters. Prefer a small, purposeful pass set over a feature-film-style dump of every possible AOV.

For expensive Blender work:

1. author/save the scene;
2. prove a representative look-dev frame;
3. prove the chosen pass set on one representative frame/short range;
4. confirm files decode/read correctly and the compositor can reconstruct the intended result;
5. only then render the full expensive range.

Use EXR or another high-fidelity intermediate when the production genuinely needs pass data; do not convert utility passes to lossy delivery media before compositing.

## Runtime proof

The repository includes a bounded local proof for this capability:

    python scripts/rendererctl.py multipass-smoke

It creates a tiny Eevee scene, enables the supported common pass flags, renders a multilayer EXR, and writes a JSON receipt under `.runtime/renderer-doctor/blender-multipass/`. Run it after meaningful Blender/runtime changes; it is a capability smoke, not a quality benchmark.

## Compositor ownership

The local workflow owns the final composite. Depending on the shot this may use Blender's compositor, Python/image tooling, or FFmpeg for deterministic assembly/temporal finishing.

The renderer adapter's normal preview contract still returns inspectable RGB frames. Production-specific Blender scene scripts may additionally write pass/AOV outputs declared by the shot's compositing contract. Keep those artifacts beside the production and preserve enough metadata to reproduce the composite.

## Contract in the director brief

Top-level `visual_development` records the previs and look-dev decisions/status/artifacts. A new serious brief begins unresolved; expensive execution is not ready until required gates are approved or explicitly marked not required.

Each shot may declare:

```json
"compositing": {
  "mode": "hybrid",
  "passes": ["beauty", "depth", "hero_mask", "emission"],
  "goals": ["depth atmosphere", "hero isolation", "streetlight control"],
  "output": "composite/final-shot.exr",
  "notes": ""
}
```

For legacy briefs, missing visual-development/compositing declarations are warnings rather than retroactive hard failures. They are not a precedent for new work.

## Review rule

Previs validates movement/editing/spatial intent. Look-dev validates representative pixels. Compositing proof validates controllable finishing. Final candidate review validates the encoded film.

Passing one stage never implies the later stage passes.