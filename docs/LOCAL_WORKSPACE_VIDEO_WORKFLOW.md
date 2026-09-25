# Local Workspace Video Workflow

This repository predates the Local Workspace plugin. The old workflow assumed ChatGPT could plan and generate files but could not reliably inspect the local runtime, manage long jobs, interact with provider websites, or review rendered media directly.

That limitation no longer defines the production model.

The repository is the source of production truth. Local Workspace is the execution, inspection, browser, media-QA, and job-control layer.

## Default production contract

For serious work, use:

**goal → inspect → validate plan → render → deterministic QA → assistant visual/audio review → repair internally → revalidate → final candidate → one user acceptance review → DONE**

The user is not the normal debugging loop.

Do not hand over a candidate merely because rendering succeeded. Do not ask the user to repeatedly find technical defects that Local Workspace, media inspection, scene-boundary review, or assistant visual review can detect first.

Intermediate user review is appropriate only when a genuinely subjective creative/product decision blocks further work or when the configured autonomous repair budget has been exhausted.

## Production controller

New productions use `templates/production-v2.json` plus `scripts/productionctl.py`.

The manifest tracks:

- source provenance;
- render argv/cwd/output;
- delivery requirements;
- candidate, receipt, review-pack, baseline-comparison artifacts;
- technical, assistant, and user gates;
- autonomous repair-cycle budget;
- blocker/escalation reason;
- exact next action.

Inspect state with:

    python scripts/productionctl.py status path/to/production.json

The controller returns a machine-readable `next_action`, such as:

- `render`
- `wait_for_render`
- `record_candidate`
- `technical_qa`
- `build_review_evidence`
- `assistant_review`
- `repair`
- `user_final_review`
- `finalize`
- `human_decision`

This prevents a resumed session from guessing where production stopped.

## Autonomous repair policy

The default manifest policy is:

- mode: `autonomous_until_final_review`;
- user review: `final_candidate_only`;
- autonomous repair budget: 4 cycles.

When technical or assistant QA fails, record the failure and repair it without asking the user to review that candidate.

Before each repair cycle, the controller archives the current artifact/gate state into manifest history. A replacement candidate resets technical and assistant gates and is evaluated again.

Escalate only when:

- an unresolved creative/product decision genuinely requires user taste;
- required source material or credentials are unavailable;
- the production contract is contradictory;
- a required tool/runtime cannot be repaired;
- the autonomous repair budget is exhausted.

Use:

    python scripts/productionctl.py assistant-fail production.json --notes "..."
    python scripts/productionctl.py repair-start production.json --reason "..."
    python scripts/productionctl.py block production.json --reason "..."

## Long renders

Render commands are stored as argv arrays in the production manifest.

Retrieve the exact render specification with:

    python scripts/productionctl.py render-spec production.json

Run potentially long renders with Local Workspace `command_start`, not a long synchronous request. Poll the persisted job until completion.

Record the resulting artifact with:

    python scripts/productionctl.py candidate production.json path/to/candidate.mp4

This makes interruption/restart recovery explicit.

## Deterministic QA

The repository-native media CLI is `scripts/videoctl.py`.

Useful commands:

    python scripts/videoctl.py doctor
    python scripts/videoctl.py probe candidate.mp4
    python scripts/videoctl.py decode candidate.mp4
    python scripts/videoctl.py audio candidate.mp4
    python scripts/videoctl.py compare baseline.mp4 candidate.mp4
    python scripts/videoctl.py qa candidate.mp4 --width 1280 --height 720 --fps 24
    python scripts/videoctl.py review-pack candidate.mp4 qa/review --scene-plan scene-plan.json

The Local Workspace bridge exposes matching read-only operations:

- `media_probe`
- `media_decode_check`
- `media_frame`
- `media_contact_sheet`
- `media_audio_analyze`
- `media_compare`

`media_compare`/the CLI comparison provide a bounded sampled SSIM regression signal. It is evidence of pixel-level change, not a creative-quality score.

## Prepare assistant review

Once a candidate exists:

    python scripts/productionctl.py prepare-review production.json

That command:

1. applies the manifest's codec/dimensions/FPS/duration/audio gates;
2. writes `qa/technical-qa.json`;
3. compares against a configured baseline when available;
4. generates the exact artifact receipt and SHA-256;
5. generates a whole-video contact sheet;
6. extracts before/after frames around every scene boundary;
7. extracts explicit scene `review_points`;
8. moves the production to `ASSISTANT_REVIEW` only if deterministic QA passes.

A technical failure goes directly to `REFINEMENT_REQUIRED`, not to the user.

## Scene plans

New episode scene plans use schema version 2 and should include deliberate review points for important beats.

Validate before rendering:

    python scripts/validate-scene-plan.py path/to/scene-plan.json

The validator rejects invalid FPS/resolution, duplicate scene IDs, overlaps, non-positive durations, and review points outside their scene.

A typical scene has:

    {
      "id": "scene-004",
      "start": 42.0,
      "duration": 9.0,
      "purpose": "reveal",
      "review_points": [
        {"at_seconds": 0.5, "label": "entry continuity"},
        {"at_seconds": 4.0, "label": "reveal composition"},
        {"at_seconds": 8.5, "label": "exit state"}
      ]
    }

## Assistant review

After `prepare-review`, inspect:

- the contact sheet;
- important review-point frames;
- scene-boundary before/after pairs;
- exact frames for suspicious moments;
- audio analysis;
- baseline comparison when relevant;
- continuity and story/marketing truth.

If a defect is visible:

    python scripts/productionctl.py assistant-fail production.json --notes "..."
    python scripts/productionctl.py repair-start production.json --reason "..."

Then make the narrowest repair, rerender only what is affected, record the replacement candidate, and repeat QA.

If the candidate passes:

    python scripts/productionctl.py assistant-pass production.json --notes "..."

Only then does the state become `USER_REVIEW`.

## Final user review

The default user-facing handoff is a final candidate that already passed technical and assistant gates.

The user then accepts:

    python scripts/productionctl.py user-accept production.json

or requests a refinement:

    python scripts/productionctl.py user-reject production.json --notes "..."

A rejection returns the production to the autonomous repair loop. It does not justify handing every subsequent intermediate attempt back to the user.

## Provider/browser workflow

For web-only generation providers, use the dedicated Local Workspace browser runtime for structured navigation, screenshots, clicks, typing, and downloads.

Provider output is never trusted merely because the provider reports success. Imported media enters the same local QA path:

**provider output → local artifact → probe/decode → audio QA → contact sheet/review points → baseline/continuity comparison → production use**

Provider-specific core plugin tools should be added only after a provider workflow is stable, reusable, and safely authenticated.

## Long-form scene architecture

Keep independent scene rendering.

Each scene should be replaceable without rerendering unrelated scenes. `scripts/assemble-scenes.py` verifies stream compatibility before concat-copy and decode-checks the assembled master.

Master audio should remain continuous where possible so visual scene replacement does not recreate the type of long-form audio dropout previously found in S01E01.

## Baselines and regression evidence

When a validated baseline exists, record it as `artifacts.baseline_master` in the production manifest.

`prepare-review` then writes a baseline-comparison receipt automatically. Use it to detect unexplained regression; do not interpret SSIM as a creative ranking.

Formal B-series promotion still requires the exact evidence defined by `baselines/README.md`.

## Finish line

A production is not DONE because a command returned zero.

The normal finish line is:

- source/scene plan valid;
- requested master exists;
- delivery properties pass;
- decode passes;
- audio checks pass where required;
- representative frames and important beats reviewed;
- scene seams reviewed for long-form work;
- baseline regression understood when applicable;
- exact artifact receipt preserved;
- assistant gate PASS;
- final user acceptance PASS;
- production package/history updated;
- clean verified commit.

This is the Local Workspace-era production workflow.
