# Local Workspace Video Workflow

This repository originally predated the Local Workspace MCP/plugin runtime. The current operating model should therefore use Local Workspace as the default execution and verification surface instead of treating ChatGPT as a text-only planner that hands off opaque shell work.

The repository remains the source of production truth. Local Workspace is the execution and inspection layer.

## Current execution model

Use this sequence for serious video work:

goal → inspect authoritative project state → create/update production package → render scenes → assemble master → technical QA → visual/audio QA → repair → re-QA → create receipt/review pack → user review → accepted baseline/canon → clean commit

Do not skip from "render command exited 0" to "done".

## Local Workspace capabilities to use

### Repository and runtime control

Use typed workspace, Git, command, process, and log tools for inspecting repository state, editing files, running short checks, starting long renders as persisted jobs, polling them, reading bounded logs, and committing only after the requested result has been verified.

Renders that can exceed the synchronous command ceiling should use the persisted background-job path.

### Media-native inspection

The Local Workspace bridge now has a media inspection layer designed for this repository:

- media_probe — normalized FFprobe metadata.
- media_decode_check — full decode verification.
- media_frame — inspect a specific timestamp as a native PNG.
- media_contact_sheet — inspect representative frames across a complete video.
- media_audio_analyze — integrated loudness, true peak, loudness range, and silence intervals.

These are read-only tools. They do not rewrite media.

The repository also has the same operations through scripts/videoctl.py, so QA remains reproducible outside ChatGPT and in CI.

## Repository-native media commands

Check the local runtime:

    python scripts/videoctl.py doctor

Inspect a master:

    python scripts/videoctl.py probe output/master.mp4
    python scripts/videoctl.py decode output/master.mp4
    python scripts/videoctl.py audio output/master.mp4

Apply delivery gates:

    python scripts/videoctl.py qa output/master.mp4 --width 1280 --height 720 --fps 24 --duration 480 --max-silence-seconds 1.0

Create a review packet:

    python scripts/videoctl.py review-pack output/master.mp4 review-packs/s01e01 --scene-plan shows/wrong-shift/season-01/episode-01/scene-plan.json

A review pack contains the exact artifact receipt and SHA-256, technical stream/decode/audio evidence, a timestamped whole-video contact sheet, optional before/after frames for each planned scene boundary, and a machine-readable manifest.

The review pack is evidence for review. It does not replace watching or visually inspecting important beats.

## Production package v2

New serious productions should start from templates/production-v2.json.

The v2 package records lane and production identity, authoritative source provenance, render entrypoint and scene plan, expected delivery properties, candidate-master path, receipt/review-pack paths, and assistant/user review state.

Validate it with:

    python scripts/validate-production-v2.py path/to/production.json

A production cannot be marked DONE under the v2 contract unless both assistant and user review are PASS and the master, artifact receipt, and review pack are recorded.

## Long-form rendering

Keep the independent-scene architecture.

Use command_start for long scene renders. Each scene should be independently inspectable and replaceable. Before stream-copy assembly, scripts/assemble-scenes.py now verifies that scene video/audio stream signatures are compatible. The final assembled master is decode-checked automatically.

If scene formats differ, do not force concat-copy. Normalize the incompatible scene deliberately, then rerun assembly.

## Visual QA with Local Workspace

The fastest useful loop is:

1. media_probe and media_decode_check.
2. media_audio_analyze.
3. media_contact_sheet.
4. Inspect exact timestamps with media_frame.
5. Inspect frames immediately before/after every scene boundary.
6. Fix the smallest responsible scene or audio bus.
7. Repeat the same evidence checks.
8. Create the artifact receipt/review pack.

For animation, structural geometry tests still matter, but they do not replace frame-level visual inspection.

## Web-based video generation providers

Local Workspace now has a dedicated browser runtime with structured snapshots, screenshots, clicks, typing, tabs, and a user-visible viewer. That is the preferred automation path for a provider that only exposes a web UI.

Do not add provider-specific browser automation to the core bridge merely because one provider is being tested. Keep provider workflows in this repository until they are stable and clearly reusable.

A provider-specific typed plugin tool is justified only when the provider is expected to remain part of the production stack, authentication can be handled safely, job submission/status/download semantics are understood, the wrapper reduces repeated brittle browser automation, and there is a real validation path for returned media.

Until those conditions exist, use browser automation plus repository-side import and QA.

## Generated-asset ingestion

Any externally generated clip should enter the same local QA pipeline before use:

provider output → save under production package → media probe → decode → visual frame/contact-sheet review → audio review when applicable → scene compatibility check → production use

Do not trust a provider success message as proof that the returned clip matches requested duration, frame rate, resolution, audio, or visual content.

## Pixel / Android boundary

Video production normally does not need Android Display 0 control.

If an Android/device-level playback check is useful, use the safe isolated-display tools. Do not inject touches into the user's primary display as part of ordinary video QA.

## Artifact policy

Candidate artifacts can be large. Do not blindly commit every render.

For normal candidates preserve deterministic render source/recipe when available, exact filename, SHA-256, media receipt, review pack, and relevant QA notes.

A formal B-series baseline should additionally preserve the exact representative artifact or another durable, unambiguous artifact location as required by the baseline policy.

## Finish-line evidence

A video task is complete only when the requested deliverable exists and the evidence matches the claim.

For a normal finished MP4 that means, at minimum, expected codec/container/dimensions/FPS/duration, clean decode, expected audio with no unexplained silence/dropouts, representative visual inspection across the full runtime, scene-boundary inspection for assembled long-form work, exact artifact hash, assistant review, and user review when the production contract requires it.

That is the standard the Local Workspace-era repository should enforce.
