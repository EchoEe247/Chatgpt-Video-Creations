# Experience Review v2 — visual/audio continuity upgrade

Date: 2026-09-27

## Trigger

Angel reviewed SECOND EARTH and reported a useful failure mode that the earlier final-review gate did not capture well enough:

- parts of the video are good;
- some shots do not feel smooth;
- some visual elements do not feel like they belong in the same scene/film;
- review needs a significant upgrade for both picture and sound rather than relying on Angel to enumerate defects manually.

The workflow was upgraded around that failure mode rather than patching one isolated shot.

## New review architecture

The creative-QA report is now schema v2.

It keeps the earlier:

- decode/freeze checks;
- motion density;
- camera-family repetition;
- phone-scale frames;
- layout checks;
- normal-speed shot clips.

It adds:

### Interior motion smoothness

Motion cadence is evaluated inside each shot while excluding cut/fade shoulders.

Signals include:

- motion-energy jerk;
- isolated motion spikes;
- near-static sample ratio.

The cut shoulders are excluded because the first version of this detector over-reported intentional transitions as in-shot stutter.

### Every-cut transition review

Every scene boundary now gets:

- a four-frame boundary strip;
- a 1.6-second normal-speed transition clip.

The workflow also records luma, saturation, average-color and edge/detail changes around the shot pair.

This targets the exact "these two things do not feel like the same scene/film" failure class.

### Audio continuity

Every cut is checked for:

- short-term loudness jump;
- sample discontinuity/click risk;
- spectral-centroid jump.

When stems exist, narration is analyzed against score + ambience + effects for:

- voice-to-bed margin;
- voice level outliers;
- low-mid tonal outliers;
- speech lead-in;
- speech tail-out;
- speech occupancy / lack of breathing room.

A full-candidate spectrogram is also generated.

### Authored A/V sync evidence

The shared A/V timeline now drives dedicated normal-speed clips around picture+sound events such as signal arrivals, launches, impacts, mutes and confirmation cues.

### Mandatory warning dispositions

Schema-v2 review cannot silently ignore an automated warning.

Each warning code must receive an evidence-backed disposition:

- `accepted_intentional`
- `repair_required`

Any `repair_required` disposition blocks assistant PASS.

### Repair A/B review

Added:

    python scripts/creativeqactl.py compare BEFORE AFTER execution-plan.json OUTPUT_DIR

It identifies materially changed authored shots and renders BEFORE/AFTER side-by-side clips for the strongest deltas.

A repair therefore has two review obligations:

1. prove the local edit is actually better;
2. regenerate/review the complete final candidate so local improvement does not hide a global regression.

## Required assistant criteria

Schema-v2 assistant review now requires eleven independent judgments:

1. composition;
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

There is deliberately no aggregate quality score.

## SECOND EARTH back-test

The same final SECOND EARTH candidate that passed the earlier Phase 7C gate was re-run through the new experience-level system.

After removing cut/fade shoulders from the motion-cadence calculation, the refined result is:

- freeze spans: 0
- weak-motion shots: 0
- camera-family repeats: 0
- interior motion-cadence warnings: 0
- audio-transition warnings: 0
- narration-mix warnings: 0
- layout violations: 0
- **visual-transition review targets: 6**

Flagged boundaries:

- shot-01 → shot-02
- shot-02 → shot-03
- shot-03 → shot-04
- shot-15 → shot-16
- shot-17 → shot-18
- shot-18 → shot-19

The generated transition strips visibly explain why this matters. Examples include strong jumps from:

- dark procedural graphics → bright physical 3D;
- physical 3D → paper/hand-drawn city;
- bright paper city → dark orbital procedural graphics;
- dark timeline graphics → bright paper control diagram;
- bright paper control diagram → dark procedural exchange graphics.

Those are not automatically defects, but they are exactly the cuts the new workflow now forces the reviewer to inspect and explicitly disposition.

This is important because the previous final gate could report "0 freezes / 0 weak motion / 0 camera repeats" while still missing a film-level coherence problem that a viewer notices immediately.

## Repair comparison proof

The new A/B repair comparator was tested against SECOND EARTH iteration 00 → iteration 01.

It independently identified exactly eight materially changed authored shots:

- shot-20
- shot-11
- shot-10
- shot-12
- shot-13
- shot-21
- shot-03
- shot-14

That matches the actual repair set from Phase 7C and produced side-by-side review clips for those changes.

## Audio review policy

Numeric audio compliance is no longer considered sufficient.

The automated layer finds likely boundary/mix/tone/pacing problems and generates evidence. Final audio judgment still requires listening/forensics at normal speed.

When Local Workspace is running the media-capable production profile, agents should use the typed audio/media review tools in addition to the repository report for flagged regions.

A model may not mark narration clarity or A/V synchronization PASS solely because LUFS, true peak, or silence checks are green.

## Files added/changed

- `src/core/experience_qa.py`
- `src/core/creative_qa.py`
- `scripts/creativeqactl.py`
- `tests/test_experience_qa.py`
- `docs/EXPERIENCE_REVIEW_WORKFLOW.md`
- `docs/CREATIVE_QA_WORKFLOW.md`
- `AGENTS.md`
- `README.md`
- `scripts/README.md`

## Validation

- focused experience/creative QA tests: 11 passed
- complete repository suite: 111 passed
- SECOND EARTH schema-v2 experience audit: completed successfully; 131 evidence files verified
- SECOND EARTH iteration-00 → iteration-01 A/B comparison: completed successfully
- historical user acceptance was not fabricated or changed

## Consequence

Under the upgraded standard, SECOND EARTH should not be treated as "done because the old assistant gate was green."

Angel's user gate was already still PENDING. The new review system now provides concrete transition evidence for the kind of inconsistency Angel noticed and will block future schema-v2 assistant PASS until those warnings are explicitly accepted as intentional or repaired.