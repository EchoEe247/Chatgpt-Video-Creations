# Chatgpt-Video-Creations

Shared reference and production repository for videos created through ChatGPT sessions.

The purpose of this repository is to preserve the **known-good baseline** for three video lanes so future ChatGPT sessions do not need to rediscover what the user means by a business video, a 2D animation video, or a 3D animation video.

## Canonical video lanes

| Lane | Default interpretation | Current baseline |
| --- | --- | --- |
| Professional / business video | Clean programmatic motion graphics for ads, explainers, product demos, dashboards, social shorts, and business content | Strong and practical |
| 2D animation | Original rigged limited-animation cartoon scene with character acting, dialogue, camera cuts, effects, and audio | Preferred animation baseline |
| 3D animation | Original stylized cel/low-poly 3D scene with real geometry, articulated characters, lighting, camera motion, effects, and audio | Valid 3D baseline; more constrained than 2D |

See [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md) for the exact definitions and quality expectations.

## Default language for future requests

When the user says:

- **"business video"**, **"professional video"**, or asks for an ad/explainer/product video without specifying another style: use the professional programmatic-motion lane.
- **"2D animation video"**: use the current rigged 2D cartoon baseline, not the early moving-PNG prototype.
- **"3D animation video"**: use the current stylized real-3D baseline, not the primitive first 3D prototype.

These are starting points, not permanent ceilings. A specific production can improve the scene design, character rigs, audio, transitions, pacing, lighting, and rendering when useful.

## Repository role

This repo is intended to be used by:

- the primary ChatGPT session coordinating video work;
- fresh ChatGPT sessions that need an immediate handoff;
- other coding/agent sessions that implement or render a video pipeline;
- future production work that needs reproducible scripts, assets, presets, and receipts.

## Current reference samples

The initial capability exploration produced three relevant reference artifacts in the originating ChatGPT conversation. They are **reference baselines, not yet committed media files in this repository**:

1. `programmatic_video_demo.mp4` — professional/business programmatic motion sample.
2. `original_scifi_cartoon_scene_v2.mp4` — current 2D animation baseline.
3. `programmatic_3d_scifi_scene_v2.mp4` — current 3D animation baseline.

Future sessions should rely on the documented characteristics here even when those conversation attachments are not available locally.

## Documentation

- [`docs/CAPABILITY_BASELINES.md`](docs/CAPABILITY_BASELINES.md) — what each lane means, what it can do, and the present limits.
- [`docs/REFERENCE_SAMPLES.md`](docs/REFERENCE_SAMPLES.md) — accepted/rejected exploration samples and the lessons that define the baselines.
- [`docs/PRODUCTION_WORKFLOW.md`](docs/PRODUCTION_WORKFLOW.md) — how to plan, build, render, review, and iterate a real video.
- [`AGENTS.md`](AGENTS.md) — concise operating instructions for ChatGPT/agent sessions entering the repo.

## Operating principle

Do not treat the first render as automatically complete. For real work:

**plan → build → render → review the actual MP4 → identify visible/audio defects → improve → re-render → validate**

The objective is a usable finished video, not merely proof that a renderer executed.
