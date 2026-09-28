# Resource Sourcing and External Tool Policy

## Default rule

Do not build every production asset from scratch when a legitimate free resource can move the requested video toward its goal faster or better.

The default production order is:

**goal → inspect existing local assets → search for useful free external resources → verify license/usage → adapt/refine for the shot → create only what is missing → animate/assemble locally → QA → deliver**

A scratch-built path remains valuable for capability testing and for work where no suitable resource exists. It is not an artificial ceiling on production quality.

## Make-vs-source contract

Use the shorthand **source nouns, author verbs**.

Generic nouns such as characters, vehicles, trees, props, materials, HDRIs, buildings, footsteps, engine recordings and reusable locomotion clips should be checked for suitable existing/local or free licensed resources before substantial scratch construction.

The production verbs remain locally directed: acting, accelerating, reacting, reaching, aiming, pedaling, revealing, camera movement, lighting changes, timing, cutting, compositing and story progression.

For high-impact assets, record the decision in the director brief `asset_strategy`. Use one of:

- `reuse_local` — use an already available catalogued asset;
- `source_free` — acquire a fitting licensed resource;
- `author_local` — intentionally create it locally;
- `hybrid` — combine sourced material with substantial local construction;
- `unresolved` — explicit blocker; do not quietly replace this with scratch work.

A sourced/hybrid requirement is not resolved until an asset is selected, provenance is deterministic and an adaptation plan exists. `author_local`/hybrid requirements must state what remains locally authored.

Provider catalog entries are discovery routes, not concrete production assets. A requirement such as a hero character remains unresolved if it names only `provider.mixamo`; after acquisition, record the specific selected asset/provenance so the plan binds to what will actually render.

Structural suitability matters as much as resemblance. A car that cannot expose its wheels, or a character that cannot support the needed contacts/rig behavior, may be a worse production asset than a simpler but controllable alternative.

See `docs/CHARACTER_PRODUCTION.md` for the character-specific ladder.

## What counts as a useful external resource

Reusable resources may include:

- character meshes and rigs;
- animation clips and mocap libraries;
- environments, sets, props, vehicles, and creatures;
- textures, materials, decals, HDRIs, and Blender node setups;
- VFX elements, particles, smoke, flashes, explosions, and overlays;
- sound effects, ambience, music, and Foley;
- fonts, LUTs, reference packs, and production templates;
- educational material that teaches a production technique;
- reliable external audio/image services when their free capacity is practically useful.

Prefer resources that remove work without locking the production into a fragile service.

## License and provenance

Before incorporating an external asset into a reusable or public production, verify the usage terms.

Prefer, in roughly this order:

1. public domain / CC0;
2. permissive licenses;
3. royalty-free or free-use licenses compatible with the intended production;
4. attribution-required resources when attribution is practical and acceptable.

Do not assume that "free download" means free to redistribute, modify, monetize, or publish.

When provenance matters, record at least:

- source URL;
- asset title;
- creator/provider;
- license or usage terms;
- date retrieved;
- local production path;
- modifications made;
- required attribution, if any.

If the license cannot be established, treat the asset as reference only rather than silently shipping it in a public/reusable deliverable.

## Adapt instead of merely dropping assets in

Downloaded assets are raw production inputs, not finished direction.

Typical adaptation includes:

- retargeting animation to the production rig;
- simplifying geometry for the phone/runtime budget;
- changing materials, textures, colors, or proportions;
- refining topology or rig constraints where needed;
- matching lighting and camera language;
- editing timing to fit the scene beat;
- layering local effects and sound design;
- removing unnecessary parts;
- converting formats;
- creating missing transition poses or custom props.

Use the resource to save time, then make it serve the production.

## External services: reliability standard

An external service is useful when its free capacity is large enough that ordinary production work is not constantly blocked by quota exhaustion.

Good examples are services where the current account has substantial free credits or a durable free tier and repeated calls consume only a small fraction of that capacity.

Do not architect the workflow around a "free" API or website that provides only a few generations, requires frequent account cycling, or predictably becomes unusable after a trivial amount of work.

Credentials remain outside the repository. Never commit API keys or access tokens.

## Online video-generation boundary

An online video-generation model is not a substitute for this repository's production workflow.

Do not take a prompt, send it to an external video generator, download the result, and describe that as an improvement to this system.

The repository remains responsible for planning, asset selection, animation/editing, compositing, audio, QA, continuity, and the final production.

External video-generation output may be used only when a request explicitly calls for it or when a production contract deliberately defines it as one input. It is not the default renderer and must not quietly replace local production work.

## Image generation

Image generation can be useful for:

- concept/look development;
- hero/key frames;
- environment plates;
- textures and references;
- limited-motion shots;
- missing visual assets.

It is optional. The shot workflow must continue through cached assets or local rendering when image generation is unavailable.

See `docs/CHATGPT_SHOT_WORKFLOW.md` for the visual-mode fallback ladder.

## Learn before brute-forcing

When a production technique is weak or the session is stuck, research how competent practitioners already solve the problem before spending long cycles guessing.

Useful sources include:

- YouTube tutorials and transcripts;
- Blender/FFmpeg/documentation;
- animation and VFX breakdowns;
- production writeups;
- open-source examples;
- technical forum discussions.

Extract the technique, understand why it works, then implement the equivalent cleanly in this workflow.

Do not copy someone else's finished creative work or reproduce protected material merely because a tutorial demonstrates it. Learn the method.

## Stop conditions for sourcing

Stop searching and build when:

- a suitable licensed resource has been found;
- additional search is unlikely to materially improve the shot;
- adaptation cost has become larger than creating the missing piece locally;
- available resources conflict with the production's originality or license requirements.

Asset search is a means to a better/faster result, not another loop.

## Authorship terminology

Keep provenance language precise:

- externally sourced asset;
- externally generated service output;
- locally authored asset;
- locally adapted asset;
- locally animated;
- locally rendered;
- locally assembled.

A production can be locally animated/rendered/assembled while legitimately using external meshes, textures, actions or recordings. Do not imply every polygon or sample was created locally when it was not.

## Production-package expectation

Serious reusable productions should keep a small provenance record for external assets beside the production package. The exact format may vary, but it should be sufficient for a future session to answer:

- where did this come from?
- may we still use it?
- what did we change?
- what local file depends on it?

The goal is to make external resources an advantage without turning them into hidden technical or legal debt.