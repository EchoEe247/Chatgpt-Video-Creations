# Chatgpt-Video-Creations

This repository is the production system I use for videos created through ChatGPT sessions. I do not want every video request to become another one-off experiment where the capability has to be rediscovered from scratch. Once a production method is actually understood and accepted, future work should build from it instead of guessing again.

There are three main lanes, and I want them kept separate because they have different goals:

1. **Business / OSS release marketing** — videos that explain and market useful public projects based on the exact release being promoted.
2. **Original animation production** — original scenes, shows, seasons, and episodes built as an actual production system rather than unrelated generated clips.
3. **Cinematic production** — standalone realistic/cinematic shorts and studies where physical motion, environment completeness, camera language, look development, audio and final visual impact need a stricter film-production path.

The existing professional motion-graphics, 2D, stylized-3D and long-form references are capability foundations, not universal visual-quality targets. In particular, the stylized 3D baseline does not establish an accepted realistic/cinematic quality bar.

## Operating philosophy

The project now follows a maturity model designed to keep experimentation useful without forcing future agents to rediscover solved constraints:

**think freely → clarify carefully → plan deliberately → build precisely → validate → establish a trusted baseline → automate what is understood → keep checking alignment**

And, at the implementation level:

**experiment → understand → formalize → validate → baseline → operate**

The point is not to turn creative work into a rigid geometry exercise. Creative composition, storytelling, acting, hooks, and visual judgment stay flexible where they genuinely need judgment.

What should become less flexible is repeated guesswork around relationships we already understand: release provenance, continuity, scene geometry, anchors, timing, render settings, and other reusable constraints.

The maturity sequence is deliberately evidence-driven. **Reproducible is not the same as understood, technically valid is not the same as accepted, and automated is not the same as mature.** Formalize stable facts early; promote a creative production method into a trusted baseline only after its output quality has actually been demonstrated and accepted. Failed or mediocre films are learning evidence, not capability milestones.

A user-described **respectful** result is an intermediate production-quality threshold, not a synonym for finished or release-ready. It means the exact candidate is worth keeping, worth continuing to improve, and potentially worth releasing later. The current latest examples are **RIDGELINE — A Descent** and the latest reviewed **VELOCITY — A Highway Study** recreation. Neither label means no further work is needed.

See [`docs/OPERATING_MODEL.md`](docs/OPERATING_MODEL.md).

## Resource-first production

The production system is not limited to what can be modeled, animated, textured, or recorded from scratch on the phone. Before rebuilding a useful asset, check whether a legitimately reusable free resource already solves part of the goal.

The default order is:

**goal → existing/local assets → free external resources → license/provenance verification → adaptation/refinement → create only what is missing → local assembly/animation → QA**

External assets can include rigs, animation clips, environments, props, textures/materials, HDRIs, VFX, SFX/music, fonts, LUTs, and other reusable production pieces.

External online video-generation models do **not** replace the repository's production workflow. Reliable external audio/image resources are acceptable when their free usage is genuinely useful and the workflow still owns the production. When a technique is weak, research practitioner workflows and tutorials rather than brute-forcing the same failed approach.

For user-facing work, the director brief first declares a fail-closed **quality floor**. Final cinematic 3D cannot waive required previs/look-dev, use final proxy assets, or replace the entire spatial production with a programmatic renderer. See [`docs/QUALITY_FLOOR.md`](docs/QUALITY_FLOOR.md).

For serious 3D work, the director brief also records **previs → look-dev → compositing** gates so final rendering is not the first place camera/blocking, materials/lighting, or finishing strategy are tested. See [`docs/VISUAL_DEVELOPMENT.md`](docs/VISUAL_DEVELOPMENT.md).

Previs and final review must also prove **motion semantics**, not merely that pixels move: a vehicle/character must travel in the intended physical direction, its local forward axis and screen motion must agree, and the camera must not create a backward-motion read. Look-dev/final review must prove **environment completeness at the intended camera distances**; a technically valid spatial scene that still reads as an unfinished blockout is not final-quality evidence.

For high-impact assets, the director brief records a make-vs-source `asset_strategy`: **source nouns, author verbs**. Generic characters/vehicles/materials/actions are candidates for licensed reuse; acting, movement, staging, cinematography, lighting, effects, edit and storytelling remain under local production control. Character-heavy work follows [`docs/CHARACTER_PRODUCTION.md`](docs/CHARACTER_PRODUCTION.md), including the Mixamo bipedal-humanoid path and its restricted raw-file redistribution rule.

See [`docs/RESOURCE_SOURCING.md`](docs/RESOURCE_SOURCING.md).

## Local Workspace runtime

This repository now assumes the Local Workspace plugin is available for normal ChatGPT production work.

For a fresh video session, the first production action is `video_workflow_bootstrap`. The canonical pointer is `workflow/CURRENT.json`; the bootstrap checks upstream freshness, resolves the relevant lane documents, and returns a deterministic receipt. The cinematic lane now includes the generated compact brief `workflow/cinematic-brief.md`; read that first for the current operating picture, then consult the canonical source documents as the task requires. New v2 production manifests require the workflow receipt before rendering, so a session cannot silently fall back to stale workflow knowledge. Use `scripts/workflowctl.py bind` to bind the current receipt to a production manifest. Long renders use persisted background jobs whose IDs are recorded in the production manifest and reconciled after interruption. Candidate media is copied into immutable iteration directories and bound to SHA-256 before QA.

The repository mirrors native media checks in `scripts/videoctl.py` and tracks autonomous production state with `scripts/productionctl.py`. The default policy is internal technical/assistant QA and repair until a final candidate is ready, followed by one user acceptance review. Acceptance fails closed if the candidate/evidence files are missing or no longer match the reviewed hash. Final-screening IDs must resolve to reviewed candidate/modality-bound evidence, rejected studio-review attempts are validated before immutable publication, approved previs/look-dev/proof files are hash-bound, and render dispatch requires fresh Local Workspace bridge compatibility evidence. New serious productions use the v2 contract in `templates/production-v2.json`.

See `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`.

## Cross-project wording authority

For Angel-owned project communication, this repository uses `EchoEe247/Chatgpt-Angel-wording-refinement` as the wording/refinement authority. It does not replace this repo's technical truth; it controls how Angel-owned documentation, marketing copy, captions, announcements, and public project communication are refined.

Fresh ChatGPT sessions should load that repository's `prompts/SESSION_BOOTSTRAP.md` for routine wording work. Important or ambiguous public/technical/business wording should also use its full system spec, meaning-preservation rules, and the relevant profile.

Fictional character dialogue is separate. Characters follow their own show/character voice unless a production intentionally defines otherwise.

## Business / OSS release marketing

For business work, the point is not to make a generic promo for a repository just because it is public. I want the video tied to something users can actually use and to the exact version where the shown behavior exists.

The preferred source-of-truth flow is:

**OSS Shipping System → marketing-eligible public product → exact release/tag/commit → release facts/changelog → production snapshot → render → QA → distribution**

The release version should be visible in the video. If somebody sees the marketing later, they should be able to tell which version is being demonstrated instead of assuming every feature shown still maps to whatever the newest release happens to be.

When a newer release is worth marketing, create new/update marketing for that release and explain what materially changed from the previous canonical release. Do not rewrite history by silently replacing old release packages.

See [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md).

## Original animation production

For original animation, I do not want to improvise Episode 1 first and only afterward figure out what the show or season is supposed to become. A show should have enough structure behind it that Episode 1 already knows what later episodes may need from it.

The working flow is:

**research/vision → show bible → season arc → episode map → story/dialogue foundation → Episode 1 production → deterministic QA → assistant review → autonomous repair/re-QA → final user acceptance → accepted canon → Episode 2**

Episodes are produced one at a time. The user is the final acceptance gate, not the normal defect-finding loop. An episode is not accepted canon just because the MP4 rendered successfully; deterministic QA, assistant review, and final user acceptance all have to pass first.

See [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) and [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md).

## Cinematic production

Cinematic work is currently a **discovery/validation lane**, not a solved visual-quality baseline. The repo should preserve what is already understood—provenance, spatial continuity, motion semantics, previs/look-dev separation, review evidence, candidate hashes, audio/video synchronization and reproducible execution—without pretending that those controls alone guarantee an impressive film.

The quality target must be learned from actual user-reviewed productions. A method should not move into `baseline → operate` just because it renders reliably or passes technical QA. The machine-readable source of current user quality state is [`productions/quality-status.json`](productions/quality-status.json); prose may explain those outcomes, but it must not silently invent a different current status. The latest **RIDGELINE — A Descent** and latest reviewed **VELOCITY — A Highway Study** recreation are respectful work worth continuing; they are not declared finished. **LAX — Final Approach** is paused on v11 as a salvageable-but-below-respectful aviation case. It is worth resuming when the user specifically wants airplane flight/approach/landing work, not as background work; its exact resume state and remaining defects are recorded in [`docs/LAX_FINAL_APPROACH_HANDOFF.md`](docs/LAX_FINAL_APPROACH_HANDOFF.md). **AETHERFALL — THE LAST LIGHT** and **THE EIGHTH HOUR** remain non-promoted failure/weak-result evidence.

The working cinematic flow is:

**goal → source/adapt useful assets → moving previs → representative look-dev → prove motion/environment risks → final spatial render → audio/finishing → encoded-candidate review → user quality judgment → learn → only then consider baseline promotion**

See [`docs/QUALITY_FLOOR.md`](docs/QUALITY_FLOOR.md), [`docs/VISUAL_DEVELOPMENT.md`](docs/VISUAL_DEVELOPMENT.md), and [`docs/OUTCOME_LEARNING_LOOP.md`](docs/OUTCOME_LEARNING_LOOP.md).

## Capability baselines and validated baselines

The repository now keeps these concepts separate.

**Capability baselines** tell fresh sessions what production methods and quality levels have already been demonstrated well enough that they should not start from zero.

**Validated B-series baselines** are stronger regression/recovery checkpoints tied to an exact commit, exact artifact, conditions, validation scope, and known limitations.

The older business, stylized-3D, and long-form references remain capability baselines unless a formal registry entry says otherwise. The stylized 3D reference proves production capability only; it is not an accepted realistic/cinematic visual baseline.

Current user-evaluated cinematic production status is intentionally more specific:

- **RIDGELINE — A Descent** — latest mountain-bike candidate: **respectful**; worth preserving and continuing, not declared finished.
- **VELOCITY — A Highway Study** — latest reviewed highway-driving recreation: **respectful**; worth preserving and continuing, not declared finished.
- **LAX — Final Approach** — paused v11 airplane candidate: **below respectful / salvageable**. Direction/orientation and major ground/environment failures were materially improved, and 22–65 s was rebuilt for pacing/camera movement, but the user still found motion insufficiently smooth and the film still needs higher native temporal sampling, early-ground cleanup, touchdown/control-surface physics, environment/lighting polish and stronger aviation audio. Preserve it for future airplane flight/landing requests; see [`docs/LAX_FINAL_APPROACH_HANDOFF.md`](docs/LAX_FINAL_APPROACH_HANDOFF.md).
- **AETHERFALL — THE LAST LIGHT** — Avatar/alien concept candidate: **medium-bad**; in the user review at the time, its environment was stronger than the then-current LAX candidate, but the concept/Avatar replication did not land, character quality needed improvement, and audio needed improvement.
- **THE EIGHTH HOUR** — Severance-inspired candidate: **trash / failed**; failure evidence only.

None of those labels alone promotes a realistic/cinematic baseline. There is currently no accepted realistic/cinematic visual baseline.

The repository now has **B1**, a narrowly scoped validated 2D geometry/composition baseline with exact commit, artifacts, hashes, conditions, technical validation, visual validation, user acceptance, and a durable receipt. Do not generalize B1 beyond the behaviors named in `baselines/registry.json`.

See [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md) and [`baselines/README.md`](baselines/README.md).

## Long-form production

Long-form work should not become lower-quality animation just because the final runtime is longer. The better approach is to keep the richer scene-level quality and assemble the final video from independently rendered scenes.

**master plan → scene renders → scene QA/fixes → continuity check → explicit ordered assembly manifest → assembly → master audio → final QA**

That also means a bad Scene 6 can normally be replaced without rerendering Scenes 1–5 and 7–12 unless a shared asset or continuity change genuinely affects them.

See [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md).

## Spatial consistency is a hard requirement

One issue I specifically do not want repeated is visual elements being positioned independently when they are supposed to belong to the same physical set.

Characters, props, effects, and cameras should derive from one shared scene/set coordinate system:

- character feet anchor to the floor plane;
- portal energy inherits the physical portal frame center and radius;
- held props inherit hand anchors;
- camera crops transform the same world/set anchors instead of introducing unrelated screen coordinates.

So if a character is visibly floating above the floor, or a green portal effect is offset from the gray/black portal frame it belongs to, that is not a small cosmetic issue. It is a QA failure that should be fixed before the video is treated as done.

That relationship now has reusable code behind it under `src/core/geometry.py` and `src/animation_2d/layout.py`, with regression tests under `tests/test_geometry.py`.

The important distinction is that the **relationship** is formalized, while the exact production lab measurements are still provisional until they pass an actual corrected render and review. The example numbers under `templates/set-anchors.json` are structural fixtures, not known-good production coordinates.

See [`docs/SCENE_GEOMETRY.md`](docs/SCENE_GEOMETRY.md) and [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md).

## Repository map

- [`AGENTS.md`](AGENTS.md) — operating handoff for fresh ChatGPT/agent sessions.
- [`docs/VISION.md`](docs/VISION.md) — what this repository is for and why the two production lanes stay separate.
- [`docs/OPERATING_MODEL.md`](docs/OPERATING_MODEL.md) — discovery → formalization → validation → baseline → operation, including agent autonomy gates.
- [`docs/PRODUCTION_WORKFLOW.md`](docs/PRODUCTION_WORKFLOW.md) — shared build, render, review, repair, and acceptance flow.
- [`docs/OUTCOME_LEARNING_LOOP.md`](docs/OUTCOME_LEARNING_LOOP.md) — converts decisive positive or negative quality outcomes into model-independent workflow lessons and fresh-agent replay requirements.
- [`docs/BUSINESS_RELEASE_MARKETING.md`](docs/BUSINESS_RELEASE_MARKETING.md) — version-grounded OSS/business marketing.
- [`docs/ANIMATION_SHOW_WORKFLOW.md`](docs/ANIMATION_SHOW_WORKFLOW.md) — show, season, and episode lifecycle.
- [`docs/CONTINUITY_SYSTEM.md`](docs/CONTINUITY_SYSTEM.md) — accepted canon and episode-to-episode state.
- [`docs/LONG_FORM_SCENE_ARCHITECTURE.md`](docs/LONG_FORM_SCENE_ARCHITECTURE.md) — independent scene rendering and assembly.
- [`docs/SCENE_GEOMETRY.md`](docs/SCENE_GEOMETRY.md) — formalized 2D coordinate/anchor relationships and currently provisional measurements.
- [`docs/VISUAL_QA_STANDARDS.md`](docs/VISUAL_QA_STANDARDS.md) — spatial alignment, composition, acting, and final visual gates.
- [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md) — accepted production capability baselines and limits.
- [`baselines/`](baselines/) — formal B-series known-good registry and promotion rules.
- [`docs/REFERENCE_SAMPLES.md`](docs/REFERENCE_SAMPLES.md) — what earlier production tests proved, failed, or established.
- [`docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`](docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md) — Local Workspace execution, media QA, provider automation, and artifact-review workflow.
- [`docs/RESOURCE_SOURCING.md`](docs/RESOURCE_SOURCING.md) — free-asset sourcing, make-vs-source decisions, licensing/provenance, external-service reliability, and learn-before-brute-forcing policy.
- [`docs/CHARACTER_PRODUCTION.md`](docs/CHARACTER_PRODUCTION.md) — character/rig/action sourcing ladder, Mixamo constraints, local performance authorship, and character QA.
- [`docs/QUALITY_FLOOR.md`](docs/QUALITY_FLOOR.md) — final-vs-prototype classification, renderer/asset/development minimums, on-disk proof enforcement, and mandatory final studio/audio review.
- [`docs/VISUAL_DEVELOPMENT.md`](docs/VISUAL_DEVELOPMENT.md) — moving previs, representative look-dev, Blender AOV/pass strategy, compositor proof, and pre-render gates.
- [`docs/FINISHING_ENGINE.md`](docs/FINISHING_ENGINE.md) — conditional multipass/hybrid finishing path, measured local Phase 0 feasibility, pass readback, protection/risk rules, and the next Render Bundle boundary.
- [`assets/`](assets/) — portable asset catalog, Core Commons manifest, license/provenance metadata, and machine-local install-state contract.
- `scripts/assetctl.py` — validate/query the asset catalog and detect known local payloads before downloading or rebuilding resources.
- [`docs/DIRECTOR_SPEC_WORKFLOW.md`](docs/DIRECTOR_SPEC_WORKFLOW.md) — model-independent directing contract: reference decomposition, story/visual/camera/audio grammar, shot events, and cross-model handoff.
- [`docs/DIRECTOR_EXECUTION_PLAN.md`](docs/DIRECTOR_EXECUTION_PLAN.md) — compiles the director brief into hash-bound shot timing, renderer lanes, asset provenance, audio/transition cues, QA requirements, and blockers.
- [`docs/AUDIO_TIMELINE_WORKFLOW.md`](docs/AUDIO_TIMELINE_WORKFLOW.md) — shared picture/audio event clock, four-stem plan, Core Audio Commons, synchronization, and master-audio QA.
- [`docs/RENDERER_ADAPTERS.md`](docs/RENDERER_ADAPTERS.md) — stable Python/Canvas/Three.js-WebGL/Blender/FFmpeg shot contracts, Pixel runtime doctor, fallback lanes, and recovery behavior.
- [`docs/CREATIVE_QA_WORKFLOW.md`](docs/CREATIVE_QA_WORKFLOW.md) — freeze/motion-density/camera-pattern/layout signals, phone-scale frames, normal-speed clips, and hash-bound assistant creative review.
- [`docs/EXPERIENCE_REVIEW_WORKFLOW.md`](docs/EXPERIENCE_REVIEW_WORKFLOW.md) — motion smoothness, every-cut continuity, visual-style fit, audio/stem/pacing QA, A/V sync evidence, warning dispositions, and before/after repair review.
- [`docs/CANVAS_HANDDRAWN_RENDERER.md`](docs/CANVAS_HANDDRAWN_RENDERER.md) — integrated MIT Canvas2D hand-drawn renderer, Pixel adapter, provenance, and local validation.
- [`templates/director-brief.json`](templates/director-brief.json) — reusable director brief starter for serious narrative/cinematic productions.
- [`templates/`](templates/) — business release, show, season, episode, and production starters.
- [`productions/`](productions/) — expected layout for real production packages.
- [`scripts/`](scripts/) — lightweight validation and assembly helpers.
- `scripts/videoctl.py` — reproducible probe, decode, audio, frame, contact-sheet, baseline comparison, QA, receipt, and review-pack CLI.
- `scripts/productionctl.py` — restart-safe production state, persisted render jobs, immutable iterations, hash-bound QA gates, repair history, escalation, and final-review control.
- `templates/scene-assembly.json` — explicit ordered long-form assembly input; the assembler never sweeps a directory for arbitrary MP4s.
- [`src/`](src/) and [`presets/`](presets/) — reusable rendering framework boundaries.
- [`tests/`](tests/) — regression checks for reusable production primitives.

## What counts as done

For me, the deliverable is the **finished MP4**, not the fact that a script ran without crashing.

For serious work the standard is:

**inspect → understand → make the precise change → test/render → diagnose failures → fix → retest → review → establish the next trusted state**

Technical success is useful evidence, but the final rendered result is what gets accepted.

Internal green QA never overrides a negative user review. If the user calls a candidate failed, bad, unfinished, or otherwise below the requested quality bar, preserve that outcome honestly, do not promote it as a baseline, and route the reusable defect into the workflow before the production is resumed.

For episodic animation, the episode becomes `DONE ✅` only after both assistant QA and user acceptance pass.

For a formal B-series visual baseline, acceptance goes one step further: preserve the exact artifact, conditions, limitations, and validation receipt so the state is usable later as a real regression reference.
## Local shot development before delivery

Use [the ChatGPT shot workflow](docs/CHATGPT_SHOT_WORKFLOW.md) for renderer-independent preview, inspection, targeted revision, native-frame rendering, and recovery. The executable entry point is `scripts/shotctl.py`; it hands reviewed shots to the existing production controller. The core path works without an external generation service, while optional reliable resources can augment it through explicit fallbacks.