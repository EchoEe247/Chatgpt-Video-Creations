# Chatgpt-Video-Creations

This repository is the production system I use for videos created through ChatGPT sessions. I do not want every video request to become another one-off experiment where the capability has to be rediscovered from scratch. Once a production method is actually understood and accepted, future work should build from it instead of guessing again.

There are two main lanes, and I want them kept separate because they have different goals:

1. **Business / OSS release marketing** — videos that explain and market useful public projects based on the exact release being promoted.
2. **Original animation production** — original scenes, shows, seasons, and episodes built as an actual production system rather than unrelated generated clips.

The existing professional motion-graphics, 2D, and 3D capability baselines are the rendering engines underneath both lanes. They are starting points, not ceilings.

## Operating philosophy

The project now follows a maturity model designed to keep experimentation useful without forcing future agents to rediscover solved constraints:

**think freely → clarify carefully → plan deliberately → build precisely → validate → establish a trusted baseline → automate what is understood → keep checking alignment**

And, at the implementation level:

**experiment → understand → formalize → validate → baseline → operate**

The point is not to turn creative work into a rigid geometry exercise. Creative composition, storytelling, acting, hooks, and visual judgment stay flexible where they genuinely need judgment.

What should become less flexible is repeated guesswork around relationships we already understand: release provenance, continuity, scene geometry, anchors, timing, render settings, and other reusable constraints.

See [`docs/OPERATING_MODEL.md`](docs/OPERATING_MODEL.md).

## Local Workspace runtime

This repository now assumes the Local Workspace plugin is available for normal ChatGPT production work. Long renders use persisted background jobs whose IDs are recorded in the production manifest and reconciled after interruption. Candidate media is copied into immutable iteration directories and bound to SHA-256 before QA.

The repository mirrors native media checks in `scripts/videoctl.py` and tracks autonomous production state with `scripts/productionctl.py`. The default policy is internal technical/assistant QA and repair until a final candidate is ready, followed by one user acceptance review. Acceptance fails closed if the candidate/evidence files are missing or no longer match the reviewed hash. New serious productions use the v2 contract in `templates/production-v2.json`.

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

## Capability baselines and validated baselines

The repository now keeps these concepts separate.

**Capability baselines** tell fresh sessions what production methods and quality levels have already been demonstrated well enough that they should not start from zero.

**Validated B-series baselines** are stronger regression/recovery checkpoints tied to an exact commit, exact artifact, conditions, validation scope, and known limitations.

The older business, 3D, and long-form references remain capability baselines unless a formal registry entry says otherwise.

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

For episodic animation, the episode becomes `DONE ✅` only after both assistant QA and user acceptance pass.

For a formal B-series visual baseline, acceptance goes one step further: preserve the exact artifact, conditions, limitations, and validation receipt so the state is usable later as a real regression reference.
## Local shot development before delivery

Use [the ChatGPT shot workflow](docs/CHATGPT_SHOT_WORKFLOW.md) for renderer-independent preview, inspection, targeted revision, native-frame rendering, and recovery. The executable entry point is `scripts/shotctl.py`; it hands reviewed shots to the existing production controller. No generation API or new service is required.
