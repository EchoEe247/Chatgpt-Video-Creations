# Mercy Engine capability reference — 2026-09-27

This receipt preserves the current long-form local-video quality reference before the asset/workflow implementation begins.

## Artifact identity

- Production: `productions/standalone/mercy-engine`
- Final local artifact: `mercy-engine.mp4`
- Candidate iteration: `iterations/iteration-02/candidate.mp4`
- SHA-256: `cc3861face6952415974df4474bf5c66653cbe9b2d0b46ca5fb69ec8c5bb0920`
- Runtime: 180 seconds
- Delivery: 1280×720, 24 fps, H.264/yuv420p, stereo AAC
- Visual production: local Python/NumPy/Pillow plus local asset use; no online video-generation model
- Audio: locally synthesized score plus Deepgram narration as recorded in production provenance

## Verified state

The production controller records technical PASS and assistant PASS against the exact candidate hash above. The final orbit repair produced visible ship/camera/environment movement and the targeted freeze scan passed.

Angel's subsequent review described the film as proof that the local workflow can be taken seriously and as a significant move toward the desired video quality. That feedback establishes this film as the current **capability reference for direction**, but this receipt deliberately does **not** promote it to a formal B-series baseline or rewrite its production user gate.

## What this reference demonstrates

- a coherent three-minute original story can be produced locally;
- long-form work can use independently rendered/repaired scenes;
- native 24 fps 720p delivery is practical on the current device workflow;
- stylized projected 3D, motion graphics, typography, original score and narration can form one coherent film;
- targeted scene repair is preferable to rerendering the whole production.

## Known limitations to beat

- scene packages are too uniformly long and often behave like one 15-second shot;
- shot density and camera grammar need more variation;
- visual transformation between scenes can be more ambitious;
- character acting is not a demonstrated strength of this production;
- audio-picture synchronization should become a shared timeline rather than mostly post-assembly timing;
- the next benchmark should exercise multiple renderer lanes and a reusable asset commons.

## Durable source snapshot

The repository tracks a compact source snapshot under `productions/standalone/mercy-engine/source/` containing the final renderer, audio builder, story, scene plan, director brief, shot metadata, and captions. Generated MP4s/renders/review images remain local and are identified by the candidate hash above rather than committed as bulk Git payload.

## Preservation rule

Do not overwrite this artifact or reinterpret it as proof of capabilities it did not exercise. Future benchmarks compare against these documented strengths and limitations. Formal B-series promotion still requires its own exact acceptance conditions and user gate.