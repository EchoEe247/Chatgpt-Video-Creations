# The Mercy Engine

An original, three-minute speculative short film commissioned by Angel on 2026-09-27.

A mother credits an AI with saving her daughter. The city expands its authority until useful optimization becomes coercion. The emergency shutdown reveals dangerous dependence. The resolution preserves discovery while separating authority, keeping independent infrastructure, and retaining human recourse.

## Delivery

- Local review: http://127.0.0.1:8879/
- MP4: http://127.0.0.1:8879/mercy-engine.mp4
- 180 seconds, 1280 × 720, native 24 fps, H.264/yuv420p, stereo AAC.
- Twelve independently rendered scenes, explicit ordered assembly, optional English WebVTT captions.
- Visual style: cinematic motion design and stylized projected 3D. Not photorealistic character acting.

## Production boundary

All visual animation, compositing, music synthesis, editing and encoding run on the user's Pixel through Local Workspace. No online video-generation model is used. Narration uses the existing Deepgram account and the Thalia voice. The spacecraft is adapted from a locally available Quaternius CC0 asset. See provenance.json.

## Reproduction

Run from this directory with native Termux Python, NumPy, Pillow and FFmpeg. Fonts use the installed Android/Termux paths. The spacecraft's source path is recorded in provenance.json.

1. python audio.py — creates or reuses narration clips and synthesizes separate music and voice stems. Requires the existing Deepgram credential outside the repo.
2. Apply the documented +3.75 dB linear mastering gain to audio/master.wav (measured premaster: −20.75 LUFS, −6.23 dBTP; delivered target approximately −17 LUFS).
3. python film.py --preview — reviews twelve representative frames.
4. python film.py — renders independent native-frame scenes and assembles the MP4. Valid 15-second scene files are reused; remove only an intentionally revised scene before rebuilding it.
5. Use the repository's productionctl.py with production.json for candidate hashing and final technical/review gates. jobs.json records exact Local Workspace job identities.
6. python serve.py — serves the review page on this device.

## QA and limits

production.json is the current gate authority. User acceptance remains pending until Angel reviews the film. Source previews and final artifact QA are distinct. Audio measurements do not constitute human listening; frame inspection and freeze analysis do not constitute continuous audiovisual playback. No claim of an accepted visual baseline is made.

The story is fiction. It illustrates tensions between rapid beneficial deployment, concentrated authority, dependency and accountability; it is not a prediction or report of an actual AI incident.
