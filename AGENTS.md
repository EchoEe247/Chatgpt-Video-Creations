# AGENTS.md

This file is the operating handoff for fresh ChatGPT or agent sessions working in this repository.

## Fresh-session video bootstrap is mandatory

Before planning or rendering a serious video, call Local Workspace `video_workflow_bootstrap` with the user's goal. It resolves `workflow/CURRENT.json`, selects the current lane docs, refreshes/checks upstream Git state, detects dirty/stale workflow files, verifies the active Local Workspace bridge against the declared minimum version/required tools/stable capability IDs, and returns a deterministic workflow receipt.

Read the returned `required_docs` before committing to the production plan. New production manifests created from `templates/production-v2.json` require that receipt to be bound with `python scripts/workflowctl.py bind <production.json> --lane <lane>`. `productionctl render-spec` and `productionctl rendering` fail closed on a stale or missing binding.

Do not substitute memory, an older chat handoff, or a stale local document for this bootstrap. If `bridge_compatibility.compatible=false`, stop before production and update/restart Local Workspace or select the required tool profile; do not work around a missing required capability with an older equivalent tool. An intentional workflow experiment must be explicitly treated as discovery mode rather than accidental drift.

## Local Workspace is the default execution layer

This repository predates Local Workspace, but current sessions should not operate as if the old limitation still exists.

Use Local Workspace directly for repository inspection, edits, Git, processes, logs, browser automation, and long-running render jobs. For 3D character/environment work prefer the typed `blender_status`, `blender_script_start`, and `blender_render_start` path; agent-authored animation must not require Angel to perform or record motion. For media QA prefer the typed `media_probe`, `media_decode_check`, `media_frame`, `media_contact_sheet`, `media_audio_analyze`, `media_motion_analyze`, `media_audio_forensics`, `media_preview_range`, and `media_compare` tools. Use `scripts/videoctl.py` as the repository-native equivalent and CI fallback. Use `scripts/productionctl.py` for production state, persisted render-job identity, immutable candidate iterations, hash-bound gates, repair cycles, and restart-safe next-action recovery.

For web resource acquisition or approved external services, use the dedicated Local Workspace browser runtime when appropriate. Do not add provider-specific core bridge tools until the workflow is stable, reusable, safely authenticated, and materially useful.

Read `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md` before broad production-runtime changes.

## Resource-first production

Do not default to rebuilding useful assets from scratch. For each serious video goal, first check whether existing local assets or legitimately reusable free resources can solve part of the problem faster or at higher quality.

Use:

**goal → local asset check → free-resource search → license/provenance check → adapt/refine → create missing pieces → assemble/animate locally → QA**

This includes meshes/rigs, animation libraries, environments, props, textures/materials, HDRIs, VFX, SFX/music, fonts/LUTs, and other reusable production material.

External online video-generation models are not a replacement for this workflow. Do not outsource the requested video to one and call the result a repository improvement. Reliable external audio/image resources may be used when their free capacity is practically useful and the production remains controlled here.

If a technique is weak or repeated local experiments are not converging, research practitioner workflows (including YouTube transcripts/tutorials, official docs, and production breakdowns), extract the method, and implement it cleanly rather than continuing a blind loop.

Read `docs/RESOURCE_SOURCING.md` before substantial asset acquisition or external-service integration.

For high-impact characters, vehicles, environments and similar production assets, use the director brief `asset_strategy` instead of silently deciding to scratch-build. The default shorthand is **source nouns, author verbs**. Read `docs/CHARACTER_PRODUCTION.md` for character-heavy work; Mixamo is a provider candidate for bipedal humanoid rigs/actions under current verified terms, but restricted raw payloads stay local and terms are rechecked at acquisition time.

Before downloading or rebuilding common resources, query the durable asset control plane:

- `python scripts/assetctl.py status`
- `python scripts/assetctl.py search <term>`
- `python scripts/assetctl.py list --core`
- `python scripts/assetctl.py scan-local`

`assets/catalog.json` is portable source/license/compatibility metadata. `assets/core-manifest.json` defines the intentionally small Core Commons. Machine-specific installed state lives in ignored `assets/local-state.json`; bulk payloads do not belong in Git by default. Code engines, camera/transition helpers and procedural audio systems count as reusable assets just like meshes, textures and WAV files.

## Canvas hand-drawn renderer

For hand-drawn, illustrative, print, or lightweight stylized 2D shots, use the integrated Canvas lane documented in `docs/CANVAS_HANDDRAWN_RENDERER.md`.

Stable entry points:

- `python scripts/canvas_handdrawn_adapter.py doctor`
- `python scripts/canvas_handdrawn_adapter.py preview <film.html> --grid 18`
- `python scripts/canvas_handdrawn_adapter.py render <film.html>`

The runtime is selectively vendored from an MIT-licensed upstream source with the upstream notice preserved. Do not copy its demo art; build original production content on the reusable engine.

## Standard renderer adapters

Before implementing a shot, run `python scripts/rendererctl.py doctor` and read `docs/RENDERER_ADAPTERS.md`.

Use the stable `shotctl` adapter contract rather than embedding environment-specific renderer commands in each production. Renderer argv may use `{repo}` for the repository root and `{request}` for the exact generated shot request.

Current Pixel floor: Python, Canvas, Blender, and FFmpeg are locally ready. Three.js/WebGL is standardized but currently degraded because headless Chromium does not expose a WebGL context; use the declared Blender/Canvas fallbacks when they preserve the intended shot instead of pretending WebGL succeeded.

## Preview-driven shot development

For local video quality improvements, read `docs/CHATGPT_SHOT_WORKFLOW.md`.
Use `scripts/shotctl.py` and `templates/shot-workflow.json` for reusable shot
previews, source-bound frame caching, explicit assistant visual findings, and
native motion before handing a finished shot to `productionctl`. Choose the
renderer from the desired look; do not equate a blockout or playable MP4 with
finished visual quality. Preview review is performed by ChatGPT, not a request
for user permission. Preserve observed limitations and verify the actual repair.
The core shot workflow remains usable without any generation API. Optional reliable resources may augment it, but unavailable services must fall back cleanly to cached or local rendering.

## Creative QA before assistant acceptance

Before handing a serious video to the user, run `scripts/creativeqactl.py analyze` against the exact candidate and its current execution plan, then read both `docs/CREATIVE_QA_WORKFLOW.md` and `docs/EXPERIENCE_REVIEW_WORKFLOW.md`.

New reports use schema v3; read `docs/EVIDENCE_FIRST_REVIEW.md`. All authored points and timed text checks are required, observations must describe rendered events, and perceptual PASS requires the appropriate inspection modality. Missing audible access cannot be converted into an audio PASS from metrics. Contact-sheet labels now use explicit source times. Historical v1/v2 evidence remains readable.

Schema-v2 review is multi-pass rather than "look at a contact sheet and approve." It includes phone-scale frames, normal-speed shot clips, interior motion-cadence analysis, every-cut transition strips/clips, visual-style continuity signals, master-audio boundary checks, narration-vs-bed/pacing analysis when stems exist, a full spectrogram, and authored A/V sync-event clips.

Automated signals are triage evidence, not aesthetic verdicts. Every schema-v2 warning must receive an evidence-backed `accepted_intentional` or `repair_required` disposition. A repair-required warning blocks assistant PASS. After a repair, use `creativeqactl.py compare` to inspect BEFORE/AFTER deltas, then regenerate/review the complete candidate; a local A/B improvement is not enough by itself.

The assistant must cite only evidence generated for the exact candidate. Missing text-layout metadata means manual readability review is required; never convert missing evidence into a fake automated pass.

Acceptance authority now lives in `src/core/studio_review.py`; read `docs/STUDIO_REVIEW_CONTRACT.md`. Specialized QA failures can veto legacy assistant PASS fields. `NOT_APPLICABLE` and `UNVERIFIED` are distinct, and evidence is not review-complete until it reaches `REVIEWED` in the PLANNED → GENERATED → DELIVERED → REVIEWED lifecycle. Status/reporting must use the derived promotion state rather than any one subsystem gate.

Read `docs/CONTROLLED_STUDIO_VALIDATION.md` before controlled/fresh-session workflow validation. The user's withheld issue is a final holdout and must not be used to tune detectors or thresholds before benchmark findings are frozen.

For productions with `workflow.studio_review_required=true`, final screening is mandatory before assistant acceptance. Record all departmental lenses, still/sampled/continuous/auditory/synchronized-A/V requirements separately, full candidate coverage for continuous modalities, opening/ending review, authored-point coverage, and any suspicion-driven second pass. Never use sampled strips as continuous-video coverage or audio metrics as proof of hearing. `productionctl assistant-pass` requires a candidate-bound `--studio-review` JSON for these productions.

## Model-independent directing

For serious narrative, cinematic, launch, music, or explainer work, read `docs/DIRECTOR_SPEC_WORKFLOW.md` and create a production-specific director brief from `templates/director-brief.json` before expensive rendering.

After the brief is explicit, compile it with `scripts/directorctl.py` and treat the resulting `execution-plan.json` as the operational handoff. Read `docs/DIRECTOR_EXECUTION_PLAN.md`. Do not silently guess missing renderer, timing, asset provenance, or shot intent; fix the director brief and recompile.

Before final shot implementation, compile a shared audiovisual timeline with `scripts/timelinectl.py` and read `docs/AUDIO_TIMELINE_WORKFLOW.md`. Important picture and sound events should reference one authoritative time/event instead of independently typed offsets. Keep narration/dialogue, score, ambience, and effects separable when practical.

The goal is to keep quality in the workflow rather than in one model's hidden reasoning. Externalize story spine, visual/camera/audio/editing grammar, hero shots, shot-level visible events, continuity constraints, review points, and forbidden patterns into durable files. A stronger model may improve the plan, but its useful decisions are not considered a workflow improvement until another agent/session can execute them successfully.

Reference strong public work for pacing, camera grammar, transitions, audio structure, and other transferable methods, but do not copy protected characters, dialogue, unique compositions, or other expressive elements. Treat reference analysis as decomposition into production rules.

## Angel wording integration

For Angel-owned project communication, use `EchoEe247/Chatgpt-Angel-wording-refinement` as the wording/refinement authority.

Keep the boundary clear:

- this repository defines what `Chatgpt-Video-Creations` is, how production works, its accepted capability baselines, validated baselines, creative rules, QA gates, and project state;
- `Chatgpt-Angel-wording-refinement` defines how Angel-owned documentation, GitHub communication, marketing copy, captions, announcements, project explanations, and other project-facing wording should be refined.

For routine work, load that repository's `prompts/SESSION_BOOTSTRAP.md`. For important or ambiguous wording, also use its full system spec, the relevant context profile, and meaning-preservation rules.

Default to Angel-refined, with Angel-professional for serious technical/business material and Angel-direct for casual/social communication.

Do not apply Angel's voice to fictional character dialogue by default. Characters follow their own show/character voice unless a character is intentionally designed around Angel's speaking style. The wording system governs the surrounding Angel-owned project communication.

Project truth always outranks wording style.

## Existing production authority

This repo already has accepted production capability baselines. Do not spend a new session proving that professional motion graphics, rigged 2D animation, stylized real-3D animation, or independent-scene long-form assembly are possible. That work has already been done.

At the same time, do not confuse those qualitative capability baselines with formal B-series validated baselines. A B-series baseline needs exact commit/artifact/conditions and evidence matching the claim. See `baselines/README.md`.

## Maturity model

Use the repository's operating progression:

**experiment → understand → formalize → validate → baseline → operate**

The corresponding work philosophy is:

**think freely → clarify carefully → plan deliberately → build precisely → validate → establish a trusted baseline → automate what is understood → keep checking alignment**

Read `docs/OPERATING_MODEL.md` before making a broad architectural or automation change.

Do not formalize a coordinate, safe zone, scale, timing rule, camera preset, or other constraint merely because it would be convenient to have a number. Formalize what is understood and reusable. Leave unresolved visual/creative choices interactive until evidence is strong enough.

## Outcome learning after a respectful result

When the user describes a result as respectful—broadly good with remaining work mainly in refinements/details—treat that as a workflow-learning trigger, not merely praise and not automatic final acceptance.

Read `docs/OUTCOME_LEARNING_LOOP.md`. Reconstruct which durable actions produced the result, which defects were found too late, and which state made takeover/recovery reliable. Move reusable relationships into the shared workflow and add earlier gates for avoidable late discoveries. Do not canonize one production's coordinates, thresholds, asset choices, or encoder settings just because they worked there.

A workflow improvement is not considered validated merely because the same strong model can repeat it or another model can finish its half-completed run. The target is independent reproducibility: a fresh Astra, GPT-5.6 Sol, Hermes, or other capable agent should be able to start from the goal + repository + durable production contracts and make the same class of good decisions without undocumented reasoning from the prior model. Use `templates/outcome-learning.json` when a compact learning record is warranted.

## Agent autonomy

Long local-agent loops are appropriate only when the repository is mature enough for the task.

Before operating autonomously for an extended loop, confirm:

- clear project goal and lane;
- explicit task scope/non-goals;
- established architecture for the affected area;
- useful acceptance criteria;
- validation that can catch the relevant failures;
- known-good comparison point when regression risk matters;
- clear change boundaries;
- stop/escalation conditions.

Within that scope, use:

**inspect → implement → validate → diagnose → fix → revalidate → assistant review → document receipt → continue**

Keep iterating internally while the next step is objectively diagnosable. Do not use the user as a substitute for media inspection, technical QA, scene-boundary checks, baseline comparison, or ordinary defect diagnosis.

State must be evidence-bound. Do not mark assistant PASS, USER_REVIEW, or DONE merely because artifact paths are populated. Verify the candidate exists, matches its recorded SHA-256, and that the technical receipt/review evidence is bound to that same hash. A changed or missing candidate invalidates acceptance.

Persist Local Workspace render job IDs immediately. A fresh session seeing `RENDERING` must reconcile that exact job rather than starting another render or waiting generically.

Escalate only if an unresolved product/creative decision genuinely requires user taste, required evidence or access is unavailable, the production contract conflicts with itself, a required runtime cannot be repaired, or the configured repair budget is exhausted.

## What this repository is for

`Chatgpt-Video-Creations` supports two main goals:

1. release-grounded business / OSS marketing videos;
2. original animated shows, seasons, episodes, and scenes.

Those goals share rendering and QA infrastructure, but they should not be treated as the same creative workflow.

Before serious production, read this file and the workflow document for the lane you are using.

## Business / OSS lane

For public-project marketing, the point is not to create a promo just because a repository exists. Resolve what is actually intended for users and which exact release the video is describing.

When the project belongs to the OSS Shipping System portfolio:

- resolve marketing eligibility from the canonical OSS registry;
- verify the exact current release from authoritative project state;
- record the project, canonical release, prior release, exact tag/commit, public URL or package, and source snapshot date;
- show the release version visibly in the video;
- describe only features and behavior supported by that release;
- when a newer release is being marketed, explain the meaningful change from the previous canonical release;
- keep material limitations visible when they matter to truthful use.

Do not market a repository merely because it is public.

A product release number is not a B-series validated baseline identifier. See `docs/BUSINESS_RELEASE_MARKETING.md` and `baselines/README.md`.

## Original animation lane

For a new show, do not jump directly into Episode 1. The season needs enough direction that the first episode already understands what later episodes may need from it.

Establish first:

- research and inspiration synthesis;
- an original premise and identity;
- show bible and world rules;
- recurring character bible;
- visual and audio identity;
- season arc and ordered episode map;
- story/dialogue foundation;
- continuity and canon tracking.

After the season foundation is ready, production narrows to one episode at a time:

**episode plan → validated scene plan → independent scene renders → deterministic QA → assistant visual/audio/continuity review → autonomous repair/re-QA loop → final user review → canon update → DONE ✅**

The user is the final acceptance gate, not the normal debugging loop. Do not hand the user intermediate candidates containing defects that can be diagnosed and repaired through Local Workspace. Ask for an intermediate decision only when a genuinely subjective creative choice blocks progress or the autonomous repair budget is exhausted.

Do not start the next episode while the current one still needs refinement.

See `docs/ANIMATION_SHOW_WORKFLOW.md` and `docs/CONTINUITY_SYSTEM.md`.

## Long-form rendering

A long runtime is not a reason to lower the entire animation baseline.

Use independently rendered scenes, preserve scene handles and continuity state, inspect and replace defective scenes individually, then assemble them against a continuous master timeline. Assembly must use an explicit ordered scene manifest; never concatenate every MP4 found in a directory. If one scene fails, fix that scene unless a shared asset or continuity change genuinely affects the others.

See `docs/LONG_FORM_SCENE_ARCHITECTURE.md`.

## Shared scene geometry is mandatory

Do not give elements unrelated guessed screen coordinates when they belong to the same physical set.

The set should define the geometry and anchors. Then:

- characters use foot/ground anchors;
- portal energy inherits the portal frame center, inner radius, and orientation;
- held props inherit hand anchors;
- screen content inherits screen bounds;
- camera shots derive their transforms from the same set/world coordinates;
- depth and layer order are explicit when the shot needs them.

A character floating above the floor, or a portal effect visibly offset from its frame, is a production defect and should be fixed before acceptance.

The current structural geometry contract is documented in `docs/SCENE_GEOMETRY.md`. Important: the example coordinates in `templates/set-anchors.json` are synthetic/unvalidated. Do not treat them as production truth just because the validator passes.

## MP4 QA

For serious renders, do not stop at successful code execution.

At minimum:

1. verify codec, pixel format, dimensions, FPS, duration, audio codec/stream, strict decode, and configured silence policy;
2. inspect representative frames throughout every scene;
3. inspect frames immediately before and after scene boundaries;
4. inspect important effects, actions, reactions, and short motion/audio review clips for dialogue/acting beats;
5. verify floor/contact anchoring and source/effect alignment;
6. verify subtitle and dialogue timing;
7. fix important visible or audio defects before handoff when feasible.

The final MP4 is the deliverable.

A structural geometry test can prove that two elements share a transform. It cannot prove that the chosen floor or portal measurements are visually correct. Match the validation method to the claim.

## Baseline promotion

Do not create a new B-series baseline simply because a change merged or CI passed.

For a visual baseline, require the exact representative artifact, technical validation, visual review, user review, render conditions, known limitations, and a receipt. Register it under `baselines/registry.json` only after those conditions are satisfied.

When a newer candidate regresses behavior covered by an older baseline, compare against the older known-good state instead of rediscovering the problem from scratch.

## Originality

Research existing media when it helps with structure, pacing, genre expectations, subject matter, or creative understanding. Use that research to synthesize something original.

Recurring characters, names, worlds, dialogue, visual identity, and story logic should belong to the new production. A reusable or monetizable show should not become a disguised clone of another show.

## Production package locations

Business releases:

`productions/business/<repo>/<release>/`

Animation productions:

`productions/shows/<show>/seasons/season-XX/episodes/episode-YY/`

Use the templates under `templates/` as starting points instead of rebuilding package structure manually.