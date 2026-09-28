# VELOCITY — A Highway Study / Recreation

**User quality status (latest reviewed highway-driving candidate): respectful.** The user-facing film title is **VELOCITY — A Highway Study**. This latest recreation is worth preserving and continuing to improve; potentially releasable later, but not declared finished or promoted as a realistic/cinematic baseline.

A 120-second, 20-shot local 3D driving film. This is a separate recreation; the original VELOCITY and its frozen audit have not been altered.

## Playback

On Angel's device: http://127.0.0.1:8884/

Master: `final/velocity.mp4`. Identity: `final/sha256.txt`.
Source download: `source-package.zip`.

## Production

Native 960×540, 24 fps, 2,880 rendered frames. H.264/yuv420p, AAC stereo at 48 kHz, fast-start MP4.
The same continuous speed profile drives integrated world displacement, wheel rotation, synthesized engine and wind. The world covers the complete 4.13 km drive without traffic recycling. Two fixed lane flows and opposing traffic have independent persistent trajectories. The center lane remains open; no lane changes are claimed.

A licensed CC0 Kenney model is spatially adapted once, with fixed approximately 4.65 × 1.90 × 1.35 m dimensions, 2.72 m wheelbase, and 0.34 m wheel radius. The adapted mesh is shared by every camera. This is stylized low-poly rendering, not photorealistic rendering.

## Reproduce inside this repository

Dependencies: the existing hermes-ubuntu runtime with Python, NumPy, Pillow, ModernGL/EGL/llvmpipe, plus local FFmpeg and repository QA scripts.

1. Compile the director brief with `scripts/directorctl.py compile`.
2. Run `source/render_3d.py` in hermes-ubuntu. It renders each shot independently and resumes completed shots. Remove affected completed shot files only when intentionally rerendering changed source.
3. Run `source/build_audio.py` in Termux.
4. Run `source/finish.py` in Termux to assemble, title, encode and run technical QA.
5. Run `source/verify_motion.py` and `source/collect_review.py`.
6. Run `serve.py` to serve the range-enabled review page on port 8884.

The package depends on this repository's workflow scripts; it is not a standalone video editor.

## Evidence and acceptance

See `review/final-review.md`. Technical measurements and sampled visual evidence cannot establish continuous viewing, listening, or perceptual A/V synchronization. This route explicitly lacks audio input and continuous-video perception, so those requirements remain UNVERIFIED and the production cannot receive an assistant perceptual PASS.

## Assets

See `source/provenance.json` and `assets/Kenney-License.txt`. No driving footage, online AI video, generated still-image slideshow, or repeated video segment is used. Audio is synthesized locally. Diagnostic stems are pre-master components.