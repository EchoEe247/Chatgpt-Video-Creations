# SECOND EARTH iteration 03 — continuity + audio polish receipt

Date: 2026-09-27

## Trigger

Angel's first review of SECOND EARTH identified a failure class broader than any single bad frame: parts of the film looked good individually but some transitions/render languages did not feel smooth or cohesive, and the review process needed a comparable upgrade for audio.

The workflow was upgraded first, then the film was repaired under that stronger gate.

## Final candidate

- SHA-256: `653ee90a00f49393edac5938770befe244a4cfe3fbb33592753287b7513e9912`
- runtime: 150.000 seconds
- video: H.264 / 1280×720 / 24 fps / yuv420p
- audio: AAC / 48 kHz / stereo
- strict decode: PASS
- production iteration: 03
- production state: `USER_REVIEW`
- technical gate: PASS
- assistant gate: PASS
- user gate: PENDING

## Visual continuity repair

The repair did not force Canvas, procedural graphics and Blender to become one visual style. Instead it distinguishes:

- an actual bad cut;
- an intentional context/style shift.

Continuity finishing now adds authored bridge frames at the boundaries that needed them while preserving every shot's original duration and the complete 150-second timeline.

Final schema-v2 signals:

- freeze spans: 0
- weak-motion shots: 0
- interior motion-cadence warnings: 0
- immediate visual cut-discontinuity warnings: 0
- camera-family repeats: 0
- layout violations: 0

Four context-level style shifts remain:

- shot 02 → 03
- shot 03 → 04
- shot 17 → 18
- shot 18 → 19

These are semantic renderer changes between physical reality, the illustrated inner world and procedural/cosmic analysis. Their actual cuts are bridged and pass immediate-cut analysis. The single `visual_style_shift_review` warning is therefore explicitly dispositioned as `accepted_intentional` with transition-strip evidence.

## Motion-review correction

The earlier motion detector could treat an authored transition fade as in-shot stutter.

Motion QA now reads `transition-finish.json` and excludes each shot's actual incoming/outgoing transition duration plus guard time. This removed false positives on shots 17/18 without weakening interior motion checks.

A regression test now covers this behavior.

## Audio polish

The original mix was already technically clean, so the repair avoided destructive re-EQ or voice replacement.

A gentle narration-aware finish was added:

- score + ambience duck about 3 dB on average while speech is active;
- inactive passages change by only about 0.2 dB on average;
- effects receive a lighter sidechain treatment;
- final loudness remains about -17 LUFS;
- sample peak remains about -2.1 dBFS.

The polishing stage now emits the exact ducked bed/effects diagnostic stems used by the master, so QA measures the final mix components instead of pre-processing source stems.

Final polished-stem analysis:

- audio-transition warnings: 0
- narration-mix warnings: 0
- authored-effect A/V sync offset warnings: 0
- measured voice-to-bed margin: roughly 12–21 dB across the 21 shots

## Repair A/B review upgrade

The repair comparator now samples densely enough to detect short transition-edge edits.

When sound changes, it also creates sequential:

- BEFORE AUDIO
- AFTER AUDIO

review clips, in addition to the existing visual side-by-side evidence.

This makes audio repair review concrete rather than relying only on LUFS or waveform statistics.

## Evidence

The final creative-QA bundle verified 131 candidate-bound evidence artifacts, including:

- phone-scale frames;
- normal-speed shot clips;
- every-cut four-frame transition strips;
- every-cut transition clips;
- A/V sync-event clips;
- full-film spectrogram;
- motion/camera/layout/audio metrics.

All 11 schema-v2 assistant criteria PASS:

1. composition
2. phone-scale readability
3. visible motion
4. camera variety
5. normal-speed story read
6. motion smoothness
7. transition coherence
8. visual-style continuity
9. audio continuity
10. narration clarity
11. A/V synchronization

## Repository validation

- focused Experience/Creative QA tests: PASS
- complete suite: **113 passed**
- final candidate decode acceptance: PASS
- user acceptance was not fabricated; the user gate remains PENDING

## Review URLs

- review page: `http://127.0.0.1:8880/`
- direct MP4: `http://127.0.0.1:8880/final/second-earth.mp4`
