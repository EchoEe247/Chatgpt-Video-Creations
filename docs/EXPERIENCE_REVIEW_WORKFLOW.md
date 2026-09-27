# Experience Review Workflow

Current default: **schema v3**. Read [Evidence-first review](EVIDENCE_FIRST_REVIEW.md) for complete review-point coverage, source timestamps, full transition shoulders, authored-silence checks and modality-bound review. The schema-v2 sections below describe the inherited checks; v3 adds the stricter requirements.

This workflow exists because a technically valid video can still feel wrong.

A candidate may decode perfectly, have no frozen frames, and still contain:

- a shot whose motion stutters or changes velocity unnaturally;
- a cut where two render styles do not feel like the same film;
- an abrupt scale, lighting, palette, or density jump;
- a transition that technically works but has no visual handoff;
- narration that is clear in isolation but buried by the bed;
- one voice line with a different low-mid tone or level;
- a music/effects transition that changes loudness or spectral balance too abruptly;
- a synchronized picture/sound event that lands late;
- a repair that fixes one shot while damaging another.

The review system therefore does not treat "QA" as one pass.

## Review stack

A serious candidate goes through these passes:

### 1. Technical validity

First verify the file itself:

- expected duration;
- codec/pixel format;
- dimensions/FPS;
- audio stream;
- strict decode;
- configured loudness/peak/silence policy.

Technical PASS only means the file is healthy enough to review.

### 2. Full-speed story pass

Watch the candidate at normal speed without pausing for frame archaeology.

Judge:

- whether the story can be followed;
- whether important reveals land;
- whether pacing feels intentional;
- whether shots overstay or disappear too quickly;
- whether the viewer's attention knows where to go;
- whether the ending feels earned.

Do not use still frames as a substitute for this pass.

### 3. Motion-quality pass

The v2 creative-QA system analyzes frame-to-frame motion inside each shot, excluding cut/fade shoulders. When a production provides `transition-finish.json`, the exclusion window uses the actual authored transition duration plus guard time rather than a generic fixed pad.

Signals include:

- mean motion energy;
- near-static sample ratio;
- irregular motion-energy "jerk";
- isolated motion spikes.

This is designed to catch animation that technically changes every frame but still feels uneven or unsmooth.

A signal is a review target, not a quality score.

### 4. Transition-coherence pass

Every cut gets two pieces of evidence:

- a four-frame boundary strip;
- a 1.6-second normal-speed transition clip containing both sides of the cut.

The automated pass also records style-distance signals from:

- luminance;
- saturation;
- average RGB;
- edge/detail density.

This directly targets the "this shot does not fit the next scene" failure mode.

A large visual jump can be intentional. If so, the reviewer must say why the cut works and cite the exact transition evidence. It may not be ignored silently.

### Cut continuity versus style shift

The v2 continuity signal intentionally separates two different questions:

- **cut discontinuity** — do the frames immediately on each side of the cut clash in brightness/color/detail strongly enough to feel like a snap?
- **context style shift** — do the surrounding shots use substantially different renderer/style languages even when the cut itself is bridged well?

This distinction matters for mixed local workflows. A physical Blender shot can intentionally lead into a paper/Canvas shot. The goal is not to force every renderer to look identical. The workflow should require an authored handoff so the viewer experiences one film rather than an accidental renderer switch.

Saturation-only differences near black are not treated as cut failures because hue/saturation math becomes visually unstable and unimportant at very low luminance.

### 5. Audio-continuity pass

The master audio is checked across every shot boundary for:

- loudness jumps;
- click/discontinuity risk;
- spectral-centroid jumps.

When stems are available, narration is also checked against score + ambience + effects for:

- voice-to-bed margin;
- per-shot voice-level outliers;
- low-mid tonal outliers;
- speech lead-in before the visual beat;
- speech tail-out before the next cut;
- speech occupancy that leaves too little visual breathing room.

The full candidate also gets a spectrogram for manual tonal review.

When the final mix uses ducking, compression, or other bus processing, QA should consume diagnostic stems emitted by that finishing stage rather than the pre-processing source stems. Otherwise the reported voice-to-bed margin does not describe the audio the viewer actually hears.

This is intentionally broader than a single LUFS number. Two mixes can have the same integrated loudness while one still feels inconsistent.

### Objective effect-onset verification

When a shared A/V timeline event references a deterministic Core Audio Commons effect, the workflow also checks the actual effects stem for the first audible onset around that event.

This produces a measured onset offset in milliseconds and flags missing or >80 ms placement errors. It complements—rather than replaces—the normal-speed perceptual sync clip.

### 6. A/V synchronization pass

The shared A/V timeline is used to create normal-speed clips around authored picture+sound events such as:

- signal arrivals;
- impacts;
- launches;
- hard mutes;
- confirmation ticks;
- reveal cues.

The reviewer checks whether the audio event and picture event feel like one authored moment.

### 7. Warning disposition pass

Schema-v2 assistant review cannot silently ignore automated warnings.

Every warning code must receive an evidence-backed disposition:

- `accepted_intentional` — the signal is real but the result is an intentional creative choice that still works;
- `repair_required` — the signal corresponds to a defect and the candidate may not pass.

A `repair_required` disposition keeps assistant PASS closed.

### 8. Repair-delta pass

After an edit, do not review only the new result in isolation.

Use:

    python scripts/creativeqactl.py compare BEFORE.mp4 AFTER.mp4 execution-plan.json review/repair-compare

The comparison:

- identifies which authored shots materially changed;
- measures visual and audio delta per shot;
- produces side-by-side BEFORE / AFTER clips for the strongest changed shots;
- samples densely enough to detect short edge-only edits such as transition finishing;
- when sound changed, produces sequential BEFORE AUDIO / AFTER AUDIO clips so the mix can be reviewed without guessing from numbers;
- binds the comparison to the hashes of both candidates.

This catches regressions introduced by a repair and helps a new model understand exactly what changed.

### 9. Full-film replay

A repair comparison is not enough.

After the local fix passes its A/B review, replay the complete candidate and regenerate the experience-QA bundle. A shot can improve locally and still damage the rhythm of the whole film.

Only the final candidate gets assistant PASS.

## Required schema-v2 assistant judgments

A schema-v2 creative review contains eleven separate judgments:

1. composition and focal hierarchy;
2. phone-scale readability;
3. visible motion;
4. camera variety;
5. normal-speed story read;
6. motion smoothness;
7. transition coherence;
8. visual-style continuity;
9. audio continuity;
10. narration clarity;
11. A/V synchronization.

Each judgment needs:

- explicit PASS/FAIL;
- written reasoning;
- evidence from the exact candidate-bound QA bundle.

There is intentionally no single "quality score." Averages can hide the exact defect the viewer notices.

## Commands

Build the full experience bundle:

    python scripts/creativeqactl.py analyze       VIDEO       source/execution-plan.json       review/experience-qa       --layout source/layout-qa.json       --timeline source/av-timeline.json       --stems-dir audio       --review-clip-limit 999

Validate its evidence:

    python scripts/creativeqactl.py validate-bundle review/experience-qa/creative-qa.json

Validate the completed assistant review:

    python scripts/creativeqactl.py validate-review       review/experience-qa/creative-qa.json       review/experience-qa/assistant-review.json

Compare a repaired candidate against the prior iteration:

    python scripts/creativeqactl.py compare       iterations/iteration-00/candidate.mp4       iterations/iteration-01/candidate.mp4       source/execution-plan.json       review/repair-compare

## Review behavior for agents

Do not pass a candidate because the metrics are green.

Do not fail a candidate merely because a style or audio metric changes sharply.

Use the signals to decide what to inspect, then make the actual creative judgment from the generated evidence.

For renderer changes in particular, inspect the cut itself. A beautiful Canvas shot and a beautiful Blender shot can still make a bad transition if palette, scale, motion direction, camera energy, or visual density do not hand off coherently.

For audio, listen for continuity, not only compliance. A line can be correctly normalized and still be masked, tonally inconsistent, rushed, or poorly synchronized.

The goal is that the workflow catches the kind of inconsistency a viewer notices before the user has to enumerate it manually.