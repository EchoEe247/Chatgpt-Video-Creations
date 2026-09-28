# Audio Commons and Unified A/V Timeline

Phase 4 makes sound and picture share one durable clock instead of being aligned by hand after the visuals are finished.

## Core rule

A meaningful beat should have one authoritative time.

The timeline stores that time in three equivalent forms:

- seconds;
- video frame index;
- audio sample index.

At 24 fps / 48 kHz, an event at 91.15 seconds is represented as:

- `91.15s`
- frame `2188`
- audio sample `4,375,200`

Both picture and sound can therefore target the same event ID without manually retyping offsets.

## Commands

Compile a timeline from an execution plan:

    python scripts/timelinectl.py compile production/execution-plan.json production/av-timeline.json

Merge production-specific events:

    python scripts/timelinectl.py compile production/execution-plan.json production/av-timeline.json --events production/av-events.json

Validate source hashes and event coordinates:

    python scripts/timelinectl.py validate production/av-timeline.json

Inspect timeline status:

    python scripts/timelinectl.py status production/av-timeline.json

Resolve one exact beat:

    python scripts/timelinectl.py event production/av-timeline.json scene-07.narration-start

If the execution plan or custom event source changes, the compiled timeline becomes stale and validation fails until it is recompiled.

## Event model

Each event can target one or more of:

- `picture`
- `audio`
- `qa`

Audio events may additionally declare a stem:

- `narration`
- `score`
- `ambience`
- `effects`

Typical event kinds include shot starts, narration entries, reveals, impacts, score changes, ambience changes, transitions, deliberate silences, and QA anchors.

The execution-plan compiler already supplies shot boundaries, visual events, audio cues, transitions, and review anchors. `av-events.json` adds finer production-specific timing such as exact narration start, a music hit 0.4 seconds before a cut, or a sound effect tied to a visual impact.

## Core Audio Commons

The permanent local audio layer is intentionally small.

Build/rebuild it with:

    python scripts/audioctl.py build-commons

Verify installed bytes against the tracked hashes:

    python scripts/audioctl.py commons-status

The current procedural fallback pack contains six 48 kHz stereo primitives:

- UI tick;
- soft impact;
- air whoosh;
- short riser;
- low pulse;
- signal chime.

These are not meant to replace production sound libraries. They guarantee that a basic transition/effect cue can be produced locally and deterministically with no external dependency.

For richer sound, search the asset catalog first. Kenney remains a preferred CC0 source for small broadly reusable packs. Freesound is cataloged as **per-file license filtered**; automatic/Core acquisition should accept CC0 only unless a production explicitly handles attribution. Sonniss stays catalog/on-demand because raw redistribution is restricted.

## Audio QA

Use:

    python scripts/audioctl.py qa MEDIA

Default master policy:

- target loudness: -16 LUFS;
- tolerance: ±4 LU;
- true-peak ceiling: -1 dBFS;
- maximum silence: 2 seconds unless the production marks the silence as intentional.

Productions may choose a different target when the creative/delivery context requires it, but the target should be explicit.

This QA supplements `videoctl.py`; it does not replace decode, codec, silence-interval, or final candidate gates.

## Stems

Plan separately when practical:

- narration/dialogue;
- score;
- ambience;
- effects.

The timeline is the synchronization authority. Stems remain independent until mix/master so narration can be repaired without regenerating music, ambience can be changed without touching dialogue, and effects can be mixed against exact picture beats.

## Mercy Engine back-test

The preserved Mercy Engine execution plan now compiles into:

`productions/standalone/mercy-engine/source/av-timeline.json`

The back-test contains 62 unified events:

- 35 audio-targeted;
- 47 picture-targeted;
- 15 QA-targeted;
- 12 explicit narration-start events.

Its actual final MP4 passes the Phase 4 audio QA at the production-specific target used for the film:

- integrated loudness: -17.02 LUFS;
- true peak: -2.5 dBFS;
- unintended silence: 0 seconds.

This is a back-test of the new timing/QA architecture, not a claim that the old film was originally authored from the new timeline.

## Quality-floor final audio gate

New user-facing production manifests require studio review by default. When a final quality-floor production has `delivery.audio_required=true`, `productionctl` refuses final execution if `workflow.studio_review_required` is disabled.

The final studio screening must preserve the distinction between audio measurement and auditory perception. For audio-required delivery, auditory and synchronized-A/V modalities are required by the studio-review contract; objective loudness/spectrum/silence checks cannot replace actual listening.

See `docs/QUALITY_FLOOR.md`, `docs/STUDIO_REVIEW_CONTRACT.md`, and the auditory perception gate in `docs/LOCAL_WORKSPACE_VIDEO_WORKFLOW.md`.
