# Local Workspace Video Workflow

This repository predates the Local Workspace plugin. The old workflow assumed ChatGPT could plan and create files but could not reliably inspect the local runtime, persist long jobs, drive provider websites, or inspect rendered media directly.

That limitation no longer defines production.

The repository is the source of production truth. Local Workspace is the execution, inspection, browser, media-QA, and job-control layer.

## Default production contract

For serious work, use:

**goal → inspect → validate plan → start tracked render job → reconcile job → preserve candidate immutably → deterministic QA → creative-QA evidence → assistant normal-speed review → repair internally → revalidate → final candidate → one user acceptance review → DONE**

The user is not the normal debugging loop.

Do not hand over a candidate merely because rendering succeeded. Technical defects, media corruption, wrong delivery properties, scene-boundary problems, regressions, ordinary visual defects, and repair verification should be handled before user review.

Intermediate user input is appropriate only when a genuinely subjective product/creative decision blocks progress, required evidence/access is unavailable, or the autonomous repair budget is exhausted.

## Production controller

New productions use `templates/production-v2.json` plus `scripts/productionctl.py`.

The manifest records:

- source provenance;
- render argv/cwd/output;
- explicit delivery profile and limits;
- persisted Local Workspace render-job identity/state;
- immutable candidate iteration directory;
- candidate SHA-256;
- technical QA evidence;
- review pack and artifact receipt;
- baseline comparison;
- optional/required candidate-bound creative-QA report and assistant creative review;
- technical, assistant, and user gates;
- autonomous repair-cycle budget;
- blocker/escalation reason;
- exact next action.

Inspect state with:

    python scripts/productionctl.py status path/to/production.json

Typical `next_action` values are:

- `render`
- `start_render_job`
- `reconcile_render_job`
- `record_candidate`
- `technical_qa`
- `build_review_evidence`
- `creative_qa`
- `assistant_review`
- `repair`
- `user_final_review`
- `finalize`
- `human_decision`

A resumed session should use this state instead of reconstructing progress from chat history.

## Render-job persistence and recovery

Before rendering:

    python scripts/productionctl.py render-spec production.json

That command refuses to return a runnable spec unless the production has an explicit output, expected duration, and—when audio is required—an unintended-silence limit.

Start long work through Local Workspace `command_start`. Persist the returned job ID immediately:

    python scripts/productionctl.py rendering production.json --job-id job-...

While the production is `RENDERING`, `status` returns `reconcile_render_job`. Poll the Local Workspace job and reconcile the result:

    python scripts/productionctl.py reconcile-render production.json --state running
    python scripts/productionctl.py reconcile-render production.json --state completed --exit-code 0
    python scripts/productionctl.py reconcile-render production.json --state failed --exit-code 1
    python scripts/productionctl.py reconcile-render production.json --state missing

A successful completed render is copied into the current immutable iteration and becomes the candidate. A failed or missing job routes to repair or, when the repair budget is exhausted, to a human decision.

Do not leave a production in a vague `RENDERING` state with no job identifier.

## Immutable candidate iterations

Every recorded candidate is copied into:

    iterations/iteration-XX/candidate.<ext>

The SHA-256 is recorded in `artifacts.candidate_sha256`.

Technical QA, baseline comparison, receipt, contact sheet, scene-boundary frames, and review-point frames are written under that same iteration directory. When repair begins, the manifest snapshots those paths and gates into history, then opens a new iteration.

Do not overwrite evidence from a previous candidate.

## Artifact integrity gates

A path string is not evidence.

Before assistant PASS, final user acceptance, or a trusted DONE status, the controller verifies:

- candidate file exists;
- candidate bytes still match the recorded SHA-256;
- artifact receipt exists and contains the same SHA-256;
- technical QA evidence exists, passes, and is bound to the same SHA-256;
- review-pack manifest exists, carries the same candidate SHA-256, and points at the current candidate;
- contact sheet, scene-boundary frames, and review-point still/clip evidence referenced by the pack still exist;
- configured baseline-comparison evidence exists and is bound to the same candidate when applicable;
- when `workflow.creative_qa_required` is true, the creative-QA report is bound to the candidate, every generated creative evidence file exists and matches its stored hash, and the assistant creative review is bound to that exact QA report.

If the candidate or required review evidence disappears or changes after review, acceptance fails closed.

## Delivery profiles

The v2 template uses an explicit `h264_web` profile. Serious productions should define at least:

- width/height;
- FPS;
- video codec;
- pixel format;
- expected duration and tolerance;
- whether audio is required;
- audio codec when required;
- silence threshold/minimum duration;
- maximum unintended silence;
- intentional silence intervals;
- baseline-comparison sample rate.

The default template expects H.264/yuv420p and AAC when audio is enabled.

A production may use `custom`, but the concrete codec/pixel/audio fields still have to be stated.

## Deterministic media QA

The repository-native CLI is `scripts/videoctl.py`:

    python scripts/videoctl.py doctor
    python scripts/videoctl.py probe candidate.mp4
    python scripts/videoctl.py decode candidate.mp4
    python scripts/videoctl.py audio candidate.mp4
    python scripts/videoctl.py compare baseline.mp4 candidate.mp4
    python scripts/videoctl.py qa candidate.mp4 \
      --width 1280 --height 720 --fps 24 \
      --video-codec h264 --pixel-format yuv420p \
      --audio-codec aac --duration 480 \
      --max-silence-seconds 1.0
    python scripts/videoctl.py review-pack candidate.mp4 qa/review --scene-plan scene-plan.json

Use repeatable `--intentional-silence START:END` arguments when planned silence would otherwise exceed the limit.

Decode PASS requires both a zero FFmpeg exit code and no FFmpeg error-level output. Audio analysis fails if FFmpeg fails or does not produce valid loudness measurements; an analysis failure must not be interpreted as “zero silence.”

The Local Workspace bridge exposes the same read-only inspection surface:

- `media_probe`
- `media_decode_check`
- `media_frame`
- `media_contact_sheet`
- `media_audio_analyze`
- `media_motion_analyze` — find freeze spans, black spans, scene-cut candidates, and aggregate blur using local FFmpeg
- `media_audio_forensics` — inspect loud windows, clipping, DC offset, and coarse frequency-band energy without a cloud service
- `media_preview_range` — render a small bounded MP4 around a suspicious beat for fast motion/audio review
- `media_compare`

Use `media_motion_analyze` before assistant review when movement quality matters, then create targeted clips with `media_preview_range` around suspicious timestamps instead of judging motion from still frames. Use `media_audio_forensics` for localized loudness/noise investigations before creating production-specific diagnostic scripts. These tools are local and require no paid service.

Baseline comparison samples across the full common runtime by default. It is a regression signal, not a creative-quality score.

## Resource sourcing before local construction

Local capability tests prove what the device can do independently; they do not define the maximum quality of a real production.

Before building a significant asset from scratch, check for existing local material and legitimately reusable free online resources. Verify licensing/provenance, adapt the asset to the production, and create only the missing parts.

Use reliable external audio/image services only when their free capacity is substantial enough for normal work. Never store credentials in the repository.

Do not use an online video-generation model as a silent replacement for the repository's renderer/editing workflow. When a production technique is not converging, research established practitioner tutorials/transcripts and documentation, then implement the learned technique locally.

See `docs/RESOURCE_SOURCING.md`.

## Agent-controlled Blender animation

Character animation must not depend on Angel recording motion or manually operating Blender.

The local Blender path is agent-first:

1. check `blender_status`;
2. write a bounded production script under this repository;
3. start it with `blender_script_start` and persist the returned job ID;
4. poll with `command_poll`;
5. inspect the generated `.blend`, preview frames, and rendered clips through the normal media QA surface;
6. use `blender_render_start` for exact still-render jobs when a scene is already authored.

Prefer free/reliable primitives first: Blender armatures, Rigify when available, NLA tracks, IK/constraints, procedural keyframes, physics, and freely licensed animation/assets. Human mocap/video capture is optional input, never a required production step.

The repository includes `scripts/blender_agent_smoke.py` as a deterministic device/runtime proof. It creates an articulated proxy character, drives one arm with IK, places body motion on an NLA track, saves a blend file, and renders a preview frame. Keep this as a smoke test; production characters should use proper imported meshes/rigs and reusable action libraries rather than the proxy geometry.

On the Pixel/PRoot path, do not rely on one long headless Workbench render process: repeated frames can terminate Blender with SIGSEGV even when individual frames are valid. Build/save the scene once, then use `scripts/render_missing_blender_frames.py` to render only the required missing frames or bounded frame ranges in isolated Blender processes with retries and output verification before FFmpeg assembly.

## Prepare assistant review

Once a candidate exists:

    python scripts/productionctl.py prepare-review production.json

The command:

1. verifies the candidate SHA-256;
2. fails closed if a configured scene plan or baseline is missing;
3. checks dimensions/FPS/codec/pixel format/duration/audio;
4. runs strict decode and audio analysis;
5. applies the unintended-silence policy;
6. writes technical QA bound to the candidate hash;
7. compares the full candidate to the configured baseline when present;
8. reuses the already-computed probe/decode/audio results when building the receipt;
9. creates contact-sheet, scene-boundary, and declared review-point evidence, including short H.264/AAC motion/audio clips around important beats;
10. moves to `ASSISTANT_REVIEW` only when deterministic QA passes.

A technical FAIL routes to `repair`; when the autonomous budget is exhausted it routes to `human_decision`. It does not loop forever on `technical_qa`.

For new v2 productions, `creative_qa_required` defaults to true. After `prepare-review`, build the creative evidence bundle with `scripts/creativeqactl.py`, inspect the phone-scale frames and normal-speed clips, complete the assistant review, then pass both paths to `productionctl assistant-pass`. See `docs/CREATIVE_QA_WORKFLOW.md`.

## Scene plans and review points

New episode scene plans use schema version 2.

Validate before rendering:

    python scripts/validate-scene-plan.py path/to/scene-plan.json

The validator rejects invalid FPS/resolution, duplicate scene IDs, overlaps, non-positive durations, and review points outside their scene.

Important acting/effect/dialogue beats should have explicit `review_points`. Each review point produces both a still frame and a short motion/audio clip; `clip_duration_seconds` may override the 2-second default up to 10 seconds. Use those clips for acting, timing, lip/subtitle synchronization, and audio-transition review instead of inferring motion from stills.

## Long-form assembly

Never assemble every MP4 found in a directory.

Use an explicit ordered assembly manifest, based on `templates/scene-assembly.json`:

    {
      "schema_version": 1,
      "scenes": [
        {
          "id": "scene-001",
          "path": "renders/scenes/scene-001.mp4",
          "expected_duration_seconds": 8.0,
          "duration_tolerance_seconds": 0.15,
          "sha256": null
        }
      ]
    }

Then run:

    python scripts/assemble-scenes.py scene-assembly.json final/master.mp4

The assembler uses only the listed scenes, in the listed order. It rejects duplicate scene IDs/files, missing files, output-as-input collisions, incompatible stream signatures, bad optional hashes, and duration mismatches, then decode-checks the master.

Stale candidates or an old master sitting beside scene files cannot silently enter the assembly.

## Assistant review and repair loop

After `prepare-review`, inspect:

- whole-video contact sheet;
- scene-boundary before/after frames;
- important review-point frames and their short motion/audio clips;
- exact suspicious timestamps;
- audio analysis and intentional-silence policy;
- baseline comparison when relevant;
- continuity and story/marketing truth.

### Dedicated browser playback gate

When the Local Workspace browser runtime is available, sampled frames are not the
last assistant review step. Generate a review page with
`scripts/make_browser_review.py`, open the final candidate in the dedicated browser,
play it from the start at normal speed through the end, and inspect the actual
browser viewport. Revisit suspicious motion at 0.5x and at explicit timestamps.

Record the browser playback state (duration, ended event, decoded/dropped frames)
and the visual observations from the viewport separately. Decode counters prove
that playback happened; they do not prove that the movement, acting, composition,
or cuts are good. A contact sheet does not substitute for continuous playback
when this browser is available. The browser connector does not establish audible
sound, so audio listening must not be claimed from browser playback alone.

If a defect is found:

    python scripts/productionctl.py assistant-fail production.json --notes "..."
    python scripts/productionctl.py repair-start production.json --reason "..."

`repair-start` archives the current iteration and returns the production to `PLANNED` for a fresh tracked render job.

Keep iterating internally while the next step is objectively diagnosable.

## Final user review

The normal user-facing handoff is a candidate that already passed deterministic and assistant review.

Accept:

    python scripts/productionctl.py user-accept production.json

Request refinement:

    python scripts/productionctl.py user-reject production.json --notes "..."

Acceptance re-verifies the candidate/evidence hashes before marking `DONE`. A user rejection returns to the autonomous repair loop; it does not make every subsequent intermediate attempt a user-review event.

## Web-provider workflow

For web-only generation providers, use the dedicated Local Workspace browser runtime for navigation, screenshots, clicks, typing, and downloads.

Provider output enters the same local chain:

**provider output → immutable local candidate → probe/decode → delivery/audio QA → visual review evidence → baseline/continuity comparison → production use**

Do not add provider-specific bridge tools until the provider workflow is stable, reusable, safely authenticated, and has clear job/download semantics.

## Wrong Shift S01E01 legacy migration

S01E01 predates this contract. Historical records show the repaired candidate at `USER_REVIEW`, assistant PASS, user PENDING, with SHA-256 `d9a49d5f...`.

The exact repaired MP4 is not present in the repository/local workspace and an exact-name Drive search did not locate it. The complete renderer is also not preserved.

`shows/wrong-shift/season-01/episode-01/production-v2.json` therefore records a **BLOCKED migration**, while preserving the historical review state in `legacy_import`. New v2 gates remain PENDING until the exact candidate or a reproducible replacement exists and is revalidated.

Do not convert historical text evidence into a fake v2 PASS.

## Finish line

A production is DONE only when:

- plan/source state is valid;
- render job/result is reconciled;
- immutable candidate exists;
- candidate SHA-256 matches;
- expected dimensions/FPS/codec/pixel format/duration pass;
- decode and required audio analysis pass;
- unintended silence policy passes;
- configured scene plan/baseline evidence is available;
- representative and important visual beats are reviewed;
- when required, the hash-bound creative-QA bundle and assistant creative review pass;
- phone-scale frames and normal-speed review clips have been inspected;
- dedicated-browser playback is reviewed when that runtime is available;
- long-form seams are reviewed;
- baseline regression is understood where applicable;
- receipt and QA evidence are bound to the candidate hash;
- assistant review PASS;
- final user acceptance PASS;
- manifest/history are updated;
- repository state is clean and verified.

That is the Local Workspace-era production workflow.
## Local shot development before delivery

Use [the ChatGPT shot workflow](CHATGPT_SHOT_WORKFLOW.md) for renderer-independent preview, inspection, targeted revision, native-frame rendering, and recovery. The executable entry point is `scripts/shotctl.py`; it hands reviewed shots to the existing production controller. The core path remains fully usable without an external generation service; reliable optional resources may augment it and must degrade cleanly when unavailable.

## Generated-image availability is never a production blocker

Built-in or web image generation is an optional visual-quality tier, not a
single point of failure. For shot development, encode the ordered degradation
path with `visual_modes` in the shot workflow. Prefer fresh generated assets
when they have actually been materialized locally, then accepted cached assets,
then a deterministic local render, then an intentional storyboard/animatic
fallback when appropriate.

Do not poll a rate-limited generator in a long loop. Missing generated assets
are treated as unavailable input and the shot runner selects the next complete
mode. The selected mode is hash-bound into shot evidence so a later return to a
higher-quality source cannot silently reuse an older review.