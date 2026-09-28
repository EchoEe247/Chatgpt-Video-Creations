# Outcome Learning Loop

A production that reaches a user-described **respectful** result has crossed an important positive threshold: the exact candidate is worth keeping, worth continuing to work on, and potentially worth releasing later. **Respectful does not mean finished, release-ready, accepted canon, or baseline-worthy**, and it can still contain meaningful work that should be repaired before release.

A clear negative outcome is equally important workflow evidence. A user-described **trash/failed**, **bad**, **medium-bad**, or **unfinished** result triggers failure learning: preserve what failed, identify which earlier gate should have caught it, and prevent technical completion from being mistaken for production quality.

Neither signal is the same as final acceptance, assistant PASS, or a B-series baseline. Both are triggers to learn from the production path while the evidence is still fresh.

The purpose of this loop is to move quality out of one model's hidden reasoning and into a reusable process that Astra, GPT-5.6 Sol, Hermes, or another fresh agent can execute independently.

## Core rule

**Do not learn only from the final artifact. Learn from the sequence that produced it.**

For each decisive outcome, separate:

1. actions that materially improved the result;
2. defects that were caught at the right time;
3. defects that were caught too late and caused avoidable rework;
4. state/evidence that made a cross-session takeover reliable;
5. one-off production details that should *not* become universal rules.

For rejected/weak outcomes also record:

6. the earliest stage where the visible failure was already observable;
7. which green metric/gate failed to represent the actual defect;
8. whether the correct response is repair, rebuild of a stage, or abandonment of the candidate as a baseline.

A stronger model rescuing a weaker or interrupted run is useful recovery evidence. It is not proof that the workflow itself is strong. The workflow is stronger only when a fresh agent can make the same class of good decisions without depending on that rescue.

## Outcome-learning contract

After a respectful or clearly rejected result:

1. Preserve the exact candidate, hashes, QA, plan, source and repair history.
2. Reconstruct the production path from durable evidence, not private reasoning.
3. Record which decisions had visible or measurable effects.
4. Convert recurring relationships into model-independent guidance or validation.
5. Add earlier gates for defects that were found late.
6. Keep thresholds and acceptance criteria unchanged unless independent evidence justifies a contract change.
7. Test the learned workflow in a later fresh session or different agent. Same-agent repetition alone is weak evidence.
8. Promote only the reusable relationship. Do not canonize accidental coordinates, one film's thresholds, or renderer quirks.

Use `templates/outcome-learning.json` for a compact record when a production warrants one.

## 2026-09-28 user-evaluated cinematic status

Use the exact latest/current productions below. Do not substitute stale earlier attempts when applying these lessons.

- **RIDGELINE — A Descent** — latest mountain-bike candidate: **respectful**. It is worth preserving and continuing to improve and may become release-worthy later; the label does not mean the film is finished.
- **VELOCITY — A Highway Study** — latest reviewed highway-driving recreation (`productions/standalone/velocity-recreation`): **respectful**. It is worth preserving and continuing to improve and may become release-worthy later; it is not declared finished.
- **LAX — Final Approach** — current airplane candidate (`productions/standalone/lax-arrival`): **below respectful / currently closer to bad, but potentially salvageable**. The airport environment is visibly incomplete; aircraft direction/kinematics need to read correctly; the flight-to-touchdown transition needs more believable landing-gear/wheel behavior; aviation audio must match the physical phases; and the picture needs to remain visually impressive throughout. If those are solved well, the film can cross into respectful.
- **AETHERFALL — THE LAST LIGHT** (`aetherfall-last-light.mp4`) — Avatar/alien concept candidate: **medium-bad**. Its environment was not as weak as the current LAX environment, but the Avatar-replication concept did not land for the user, the characters needed to be better, and the audio needed improvement. Do not promote it as a target.
- **THE EIGHTH HOUR** — Severance-inspired candidate: **trash / failed**. The preserved audit found a regression to scratch proxy humans/environments, skipped meaningful visual development, a primitive final-render path, and weak audio. Treat it as failure evidence only.

The LAX result adds durable rules:

1. **Motion amount is not motion semantics.** Previs must prove the hero's forward axis, travel vector, screen direction, camera relation and contact phases agree before the expensive render.
2. **Environment asset presence is not environment completion.** Look-dev must prove the actual world density, landmarks/background structure, material integration and depth from representative final cameras.

These failures also show that an internal technical/assistant green state is not a substitute for user-facing quality. A later user rejection remains the authoritative acceptance outcome.

## Independent reproducibility standard

The target is not "another model can continue the same half-finished run."

The stronger target is:

> Given the goal, repository, director brief/execution plan, assets and workflow docs, another capable agent can start independently and reach a similar quality floor using the same production method.

Cross-model handoff still matters, but as a recovery property:

- persisted render jobs are reconciled rather than restarted;
- completed shots are preserved rather than rerendered;
- exact candidate hashes bind QA and review evidence;
- the next action is discoverable from repository state;
- limitations such as unavailable listening or continuous playback remain explicit.

A handoff that succeeds because the incoming model reverse-engineers undocumented choices is not a workflow success.

## Phase gates learned from VELOCITY

The latest reviewed **VELOCITY — A Highway Study** recreation on 2026-09-28 reached the user's respectful threshold through a useful Astra → GPT-5.6 Sol sequence. That means it is worth preserving and continuing, not that it is finished or a promoted realistic/cinematic baseline. The process exposed both strong practices and late checks worth moving earlier.

### What worked and should generalize

| Observed production behavior | Reusable workflow rule |
| --- | --- |
| Renderer/runtime and playback/listening capability were checked before committing to review claims | Start with a capability matrix. Know what can be rendered, measured, viewed, heard and synchronized before promising a modality-specific PASS. |
| Existing renderer/source was inspected before reuse; malformed scale, a mid-shot camera-side switch and missing traffic collision logic were found | Audit inherited production code/assets before copying them into a remake. Preserve the reference and build corrected work separately. |
| A CC0 car kit was found, its license checked, and separate wheel meshes were used | Resource-first production includes license/provenance and structural suitability, not just visual resemblance. |
| Preview renders exposed open sky under the road, bad tire palette, bonnet obstruction, side-camera sightlines and vehicle proportion problems | Use representative preview gates before expensive rendering. A playable preview is not enough; inspect the specific risk views. |
| Hero displacement, wheel rotation, engine/wind behavior and pass-by timing were driven from the same motion model | Important picture and sound events should share one authoritative motion/event clock. |
| Numerical checks found camera paths crossing traffic and moved them into lane gaps | Run spatial/collision/clearance validation before the full render, then visually verify the result. |
| Rendered shots were preserved and later work resumed from completed shots | Render independently and invalidate narrowly. Do not rerender correct work because one shot or finishing stage changes. |
| Exact candidate review used authored points, all cuts, technical QA, hashes and explicit modality limits | Review the encoded candidate, not the source intent. Bind evidence to the candidate hash and keep UNVERIFIED distinct from PASS. |
| The follow-on session repaired the final encode/detail path without rebuilding the 3D production | Diagnose the stage that actually fails. A final-encode defect should not automatically trigger a scene rerender. |
| The late-detail threshold stayed at 0.020 while the candidate was improved to pass it | Repair the production before weakening a revealed acceptance gate. |

### Rework that should move earlier

The screenshots also show several issues detected after more expensive work had already occurred:

- a review timestamp extended past the 120-second master;
- night streetlight pools formed distant terrain bands;
- tire contact shadows and night detail needed repair;
- foreground-car overlap/camera clearance was inspected late;
- the final H.264 path reduced late-shot detail enough to fail a gate;
- some monitoring/review steps were repeated with near-duplicate progress entries.

These become earlier workflow gates rather than merely historical notes.

## Cross-production asset and character lessons

The latest **RIDGELINE — A Descent**, Blender Agent Action V5 and the latest reviewed **VELOCITY — A Highway Study** recreation establish a combined lesson:

| Evidence | Reusable lesson |
| --- | --- |
| RIDGELINE successfully authored the rider, bicycle, route, trees, cameras and motion locally, but the character/world remained visibly procedural | Local scratch construction is a valid fallback and capability proof, not the automatic quality ceiling for a finished character production. |
| Blender Agent Action V5 replaced proxy character/corridor geometry with CC0 Quaternius assets while keeping animation assembly, staging, cameras, lighting, VFX, audio timing, rendering and QA local | Sourcing a stronger noun can raise the visual floor without outsourcing the production verbs. |
| VELOCITY replaced malformed custom car geometry with a CC0 Kenney vehicle whose separate wheel parts could support real wheel transforms | Asset selection must test structural controllability, not only visual resemblance. |
| Mixamo's current Adobe FAQ permits royalty-free character/animation use in films and targets bipedal humanoids, while current Adobe licensing guidance restricts raw-file redistribution | Treat Mixamo as a character-motion provider, keep payloads local, reverify terms at acquisition, and retain local ownership of performance assembly. |

The resulting rule is **source nouns, author verbs**. High-impact make-vs-source decisions now belong in the director brief so a fresh agent cannot silently convert an unresolved asset need into low-quality scratch geometry.

## Reference-study visual-development lessons

Three Blender references reviewed on 2026-09-28 reinforced production relationships worth encoding rather than copying stylistically:

- `https://youtube.com/shorts/hYcQ5gGHxxg` — a strong car asset becomes convincing through look development: material response, reflections, lighting, grounding, camera and finishing matter as much as base geometry.
- `https://youtu.be/4nPSwmwsa7g` — compositing/render-pass workflows demonstrate why a baked beauty frame should not be the only possible finishing representation when depth, emission, masks, reflections or atmosphere need controlled adjustment.
- `https://youtu.be/UXqq0ZvbOnk` — polished Blender narrative work reinforces the value of moving previs before final animation/lighting and of separating blocking/editorial decisions from final pixels.

These references do not become style targets or asset sources by default. The transferable workflow is:

**source/adapt assets → moving previs → representative look-dev → deliberate pass/compositing proof → expensive render → final composite/encode → candidate-bound QA**

The full render should not be the first time the workflow discovers a bad camera move, unreadable blocking, weak material response or an inflexible finishing path.

## Revised serious-video order

For cinematic/local productions, prefer this sequence when applicable:

1. **Capability preflight** — renderer, FFmpeg, media inspection, listening/A/V modality, runtime and fallback status.
2. **Inherited-state audit** — inspect existing renderer/assets/production before reuse; preserve the reference.
3. **Resource/provenance pass** — local assets first, then legitimately reusable free assets, license verification, adaptation plan.
4. **Director/timeline compile** — one master duration and event clock; reject review points, transitions or authored events outside the legal timeline before rendering.
5. **Representative risk-preview pack** — at minimum opening, first acceleration/action beat, side/profile, close mechanical/detail view, POV/obstruction-risk view, peak/high-density view, late-night/lowest-detail view, and closing state when those categories exist.
6. **Numerical scene preflight** — collision, camera clearance, continuity, trajectory, object/contact geometry and other deterministic constraints that can prevent expensive bad renders.
7. **Encode-path proof** — encode one critical high-detail/low-light segment through the intended final codec/filter path and run the same relevant quality metric used on the master. This catches compression/finishing loss before a full encode.
8. **Independent shot render** — tracked jobs, resumable outputs, immutable completed shots.
9. **Narrow invalidation** — repair/rerender only affected shots or stages unless shared state truly invalidates more.
10. **Exact master assembly** — clamp duration, transitions, titles and review timestamps to the compiled master.
11. **Technical QA** — strict decode, format, duration, audio, silence policy and delivery profile.
12. **Candidate-bound creative/experience QA** — every authored point, timed text, all cuts, representative motion clips, audio/A-V checks where the modality genuinely exists.
13. **Stage-local repair** — identify whether the defect belongs to source geometry, animation, lighting, audio mix, assembly, grading, or encoding before changing upstream work.
14. **Final user review** — user sees the strongest internally reviewed candidate, not an avoidable debugging draft.
15. **Outcome learning** — after a decisive user quality outcome, extract the repeatable success relationships or the earlier gate that should have prevented the failure, then add that learning to the shared workflow.

## Representative-preview rule

The full render should not be the first time the workflow sees a known-risk condition.

A representative preview pack should deliberately sample extremes, not just average shots:

- brightest and darkest lighting;
- widest and closest camera distances;
- fastest motion;
- densest traffic/crowding;
- smallest readable text;
- most reflective/material-sensitive surface;
- opening and ending;
- any custom transition or unusual renderer path.

For each risk preview, evaluate the **actual pixels** and any applicable deterministic metric.

## Encode-path proof

Final compression and finishing can create a regression even when source frames pass.

Before a costly master encode, select a short segment that stresses the delivery path—typically low light, fine texture, fast motion, gradients, text, or grain—and run it through the intended filters, codec, pixel format, preset and quality settings.

If the master has a deterministic visual gate, run that same gate or an equivalent segment-level calculation on the encoded proof. Do not infer that source-frame success guarantees delivery-frame success.

## Cross-agent state quality

A production is handoff-ready when a new session can answer from files/state:

- what is the exact goal and current candidate?
- which shots/stages are complete?
- what render job IDs are active?
- what changed since the prior candidate?
- what gates pass/fail and against which hash?
- which review modalities are unavailable?
- what is the exact next action?
- what must *not* be rerun?

Progress prose is useful, but durable state outranks chat narration.

## Avoid process noise

Repeated status checks are sometimes necessary for long jobs, but duplicate analysis should not masquerade as progress.

Agents should:

- use multi-job polling where available;
- avoid rerunning the same inspection unless state changed or a new question is being tested;
- label a repeated check as verification/recheck when intentional;
- prefer one evidence-producing action over several near-duplicate status messages;
- preserve the causal chain: finding → repair → re-render/re-encode → recheck.

## What not to generalize from VELOCITY

Do **not** turn these production-specific facts into universal defaults:

- 120 seconds;
- 960×540 at 24 fps;
- the exact acceleration speeds or distances;
- the 0.020 late-detail floor outside the production that defines it;
- the specific car kit;
- the exact camera placements or traffic spacing;
- the use of H.264 CRF 15 + grain tuning for unrelated films.

The reusable learning is the relationship: test representative risk conditions, bind picture/sound to shared state, preserve resumability, validate safety/continuity early, test the delivery encode, and keep evidence honest.

## Promotion rule

A decisive positive or negative result can justify a workflow lesson immediately. A negative result never justifies baseline promotion; a positive result still does not automatically justify a formal visual baseline.

Promote a baseline only under the normal baseline contract. Validate a workflow improvement when a fresh session or different agent successfully uses it on a later task without needing the original model's undocumented reasoning.

The desired progression is:

**decisive outcome → inspect the path → extract reusable success/failure relationship → encode it → fresh-agent replay → validate → operate**