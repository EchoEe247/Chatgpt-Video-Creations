# ChatGPT shot iteration on the phone

The improvement is a reusable working loop for ChatGPT: make a creative choice,
render cheap evidence, inspect it, record a specific correction, and render the
changed version. `shotctl` runs locally through Local Workspace. It does not call
a model, a generation service, or an API. ChatGPT remains the creative decision
maker. No user approval is required for ordinary preview or repair work.

## Start with the visible result

Before choosing a renderer, state the intended look, audience, scene purpose,
action beats, and visible acceptance conditions. Use the existing tools that fit
the requested result: edited local footage, 2D animation, motion graphics, or 3D.
Do not select Blender just because it is available. A blockout is useful for
testing movement and composition; it is not a finished visual style by default.

Before authoring missing art/geometry, follow `docs/RESOURCE_SOURCING.md`: reuse suitable local or legitimately free external assets when they materially help the shot, adapt them, and declare every dependency in `sources`. Scratch-building remains the fallback, not the default proof exercise.

For each shot, define a short intent and concrete criteria such as readable
silhouette, complete subject framing, grounded feet, a clearly visible reaction,
or a prop attached to the correct hand. Add motion-only criteria separately.
Keep an explicit list of unresolved visual limitations. Codec success cannot
clear a creative defect. A sampled still cannot establish motion quality.

## Commands

Copy `templates/shot-workflow.json` beside a production's files and replace its
example scene/adapter paths. The Blender script argv must use an absolute device path because proot can change its working directory. Paths in `sources` and `work_dir` are relative to the
manifest. Renderer argv runs with the manifest directory as cwd; `{request}` is
replaced with an absolute request JSON path. It is not shell-expanded.

```sh
python scripts/shotctl.py status path/to/shots.json
python scripts/shotctl.py preview path/to/shots.json --shot shot-01 --timeout 180
python scripts/shotctl.py review path/to/shots.json --shot shot-01 --stage preview --review-file preview-review.json
python scripts/shotctl.py motion path/to/shots.json --shot shot-01 --timeout 300
python scripts/shotctl.py review path/to/shots.json --shot shot-01 --stage motion --review-file motion-review.json
```

Start long commands with Local Workspace `command_start`, immediately preserve
the returned job ID in the production work notes, and resume with `command_poll`.
Do not start duplicate work after an interruption. The render lock serializes
work within the manifest's `work_dir`; use a shared work directory if multiple
manifests must share the same device render slot. Avoid concurrent heavy jobs
outside this runner on the Pixel as well.

## Inspect and revise

The output includes `contact-sheet.png`, exact PNG frames, `evidence.json`, and
`review-template.json`. Use `media_frame` with the contact-sheet PNG to bring it
into ChatGPT's visual context, then inspect detailed frames where needed. The
motion stage produces `candidate.mp4` and technical QA. Use native media tools
for motion analysis and targeted frame sequences/preview clips. If the dedicated
Local Workspace browser is available, generate a local review page with
`scripts/make_browser_review.py`, play the motion candidate at 1x through the end,
inspect the live viewport, and revisit suspicious beats at 0.5x. The review page
must expose working controls and seeking/scrubbing so a reviewer can rewind or jump
to exact timestamps without replaying the full candidate. Only then make a
continuous-motion judgment. If audiovisual playback is unavailable, say what was
actually inspected; do not claim listening or continuous playback from stills and
statistics.

Copy the review template to a separate review file and record each judgment,
specific observations, and the evidence filenames actually inspected. Failed
criteria need a concrete `next_change`; defects remain visible in `status`.
ChatGPT writes these reviews itself. They are evidence-backed assistant judgments,
not automatically computed visual scores or user approval requests.

Change the source scene, shot settings, or adapter to fix the cause, rerun the
preview, and inspect the new evidence. A source change creates a new version
directory and invalidates the old review. Previous defects and reviews remain
in their original directories; read those when deciding whether a repair worked.
Use narrow repairs rather than rebuilding the entire production.

## Rendering and recovery

- Preview renders the beginning, quarter points, ending, and explicit review times.
- Motion renders every output frame at the requested FPS. The Blender adapter
  evaluates real scene subframes; it does not use optical flow or repeated-frame
  upconversion. This removes interpolation artifacts, not underlying rig defects.
- Preview frames are reused by the motion stage at the same resolution.
- Sources, shot settings, and the runner determine the version. Declare **all**
  external assets, textures, linked scenes, and adapter scripts in `sources`.
  If the runtime changes, change a `settings.runtime_tag` so cached renders from
  the old runtime are not reused. Undeclared dependencies cannot be detected.
- Frame hashes and PNG decode/dimensions are checked before reuse. Partial valid
  output survives a failed or timed-out render; missing/corrupt frames rerender.
- Preview timing produces an explicitly approximate full-render estimate. If
  the estimate is too expensive, shorten the shot or simplify the scene. Do not
  silently downgrade a requested delivery or turn motion into a slideshow.
- The phone template uses one frame per renderer process (`batch_size: 1`); the generic runner defaults to eight for other local renderers (`batch_size` may be 1–32). Eight-frame Blender batches still crashed during device validation, so use the one-frame setting on this runtime. This bounds accumulated renderer state on the phone. Completed batches are checkpointed immediately; even a zero-exit wrapper is rejected if its frames are missing.
- Rendering has a finite total timeout, and timed-out process groups are terminated.
  No renderer remains running after a completed command.

The built-in Blender adapter opens a saved `.blend` and supports resolution,
time-range, FPS, engine, and optional camera-lens overrides. Other local renderers
can consume the same JSON request and write one `<frame:06d>.png` per requested
frame into `output_dir`. They must honor the declared size and frame times.

## Production handoff and audio

This is the shot development stage before `productionctl`, not a replacement
for its immutable delivery candidates, master audio, scene assembly, QA, or final
user acceptance. `productionctl_handoff` means the shot has passed its specified
assistant criteria; it does not mean the finished production is DONE.

Shot motion files are intentionally silent. Keep dialogue, music, and effects
as separate stems in the master edit so a loud or resonant sound can be isolated
without recreating voices or visuals. The shot runner itself does not call an
audio API. The master production may use a configured reliable audio/voice
service when its free capacity is practically useful, following
`docs/RESOURCE_SOURCING.md`. Final master audio still requires the existing
loudness/silence checks, targeted audio forensics, and honest listening limits.

## Scope of the initial validation

The on-device comparison uses the existing corridor blockout to exercise a real
framing correction and native motion. It is a workflow regression example, not a
claim of finished character design, convincing acting, or film-level rendering.
No new B-series visual baseline is promoted without user acceptance.

The scripts/image_sequence_shot_adapter.py adapter reuses local PNG frames in the declared source order. It validates dimensions and image integrity, requires one PNG per output frame, and copies exact bytes without interpolation. This supports inexpensive editorial corrections after a costly render; record intentional cuts explicitly in the shot intent and review points.

## Visual-source fallback ladder

A shot may define an ordered `visual_modes` list instead of one top-level
`sources` / `renderer` pair. The runner selects the first mode whose declared
source files are present locally and records `selected_visual_mode` in the
render request and evidence.

Use the order as a graceful-degradation contract, for example:

1. `generated` — fresh ChatGPT/provider keyframes already materialized into the production;
2. `cached` — previously accepted generated assets for the same character/set/look;
3. `local-blockout` — deterministic Blender/2D local render;
4. `storyboard` — intentionally simplified local animatic assets.

Generation availability is not guessed by the runner. A generation mode becomes
available only when its expected assets actually exist. If generation is
rate-limited or unavailable, the workflow therefore moves immediately to the
next complete local mode instead of waiting, retrying indefinitely, or failing
the whole production. When a higher-priority asset later appears, the selected
mode changes and the shot fingerprint changes, invalidating stale review/cache
evidence automatically.

Each mode must declare all files that materially affect its output. Do not label
an interpolated/cached fallback as native generated output; the evidence must
state the selected mode.
