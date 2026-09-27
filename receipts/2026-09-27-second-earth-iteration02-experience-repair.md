# SECOND EARTH — iteration 02 experience-review repair

Date: 2026-09-27

## Trigger

Angel reviewed iteration 01 and reported that the film had good material but also visible inconsistencies: some parts did not feel smooth and some shots/elements did not feel like they belonged in the surrounding scene. Angel explicitly asked for a significant upgrade to both visual and audio reviewing/editing rather than manually enumerating every defect.

The production controller recorded that user review as FAIL and opened repair cycle 2.

## Workflow repair before film repair

The review system was upgraded first so the edit would be evidence-driven.

Experience Review v2 now separates:

- in-shot motion smoothness;
- immediate cut continuity;
- broader renderer/style shift;
- every-cut visual evidence;
- audio boundary continuity;
- narration-vs-bed/tone/pacing;
- objective authored-effect A/V onset alignment;
- before/after repair comparison.

The A/B comparator was also corrected after the first implementation missed edge-only edits at 1 fps. It now samples at 8 fps and records mean / p95 / maximum visual deltas so short transition repairs are visible to QA.

Visual continuity was corrected to distinguish actual cut discontinuity from broader context style difference. Saturation-only changes near black are no longer treated as visible cut failures.

## Film changes

A production-owned transition-finishing layer now runs before final assembly.

It preserves shot duration and only touches evidence-justified boundaries.

Continuity bridges now cover:

- 01→02
- 02→03
- 03→04
- 06→07
- 07→08
- 13→14
- 15→16
- 16→17
- 17→18
- 18→19
- 19→20

The bridge colors are chosen from the destination/source visual language (near-black, cool-dark, or warm paper) rather than applying one global transition.

Shot 21 was separately repaired so the final thesis inherits shot 20's opening exposure/saturation and grades down over ~0.85 s instead of cutting immediately to a much darker treatment.

## Audio findings

The expanded audio pass did not justify a remix.

Evidence on the exact candidate:

- integrated loudness: -17.18 LUFS
- true peak: -2.02 dBFS
- unintended silence: 0
- audio cut warnings: 0
- narration mix/tone/pacing warnings: 0
- voice-to-bed margin across shots: approximately 9.8–17 dB
- authored procedural effects checked: 5
- effect-onset sync offsets: 0 ms, +38 ms, 0 ms, +0.06 ms, -0.06 ms
- A/V sync offset warnings: 0

The audio master was therefore preserved. The workflow now has stronger evidence for deciding when audio should be edited instead of changing it merely because a visual repair happened.

## Final candidate

SHA-256:

`025c7fcf2ec101a6c892ed8d821fb7b6683822b7b61bb499724aa318e5a91bbd`

Delivery:

- 150.000 seconds
- H.264
- 1280×720
- 24 fps
- yuv420p
- AAC stereo
- 48 kHz
- strict decode PASS

Schema-v2 creative summary:

- freeze: 0
- weak motion: 0
- immediate cut discontinuity: 0
- audio transition warnings: 0
- narration mix warnings: 0
- A/V sync offset warnings: 0
- layout violations: 0
- style-shift review targets: 4
- cadence review targets: shots 17/18

The style/cadence targets were inspected and explicitly accepted as intentional with evidence. The assistant review validates 11/11 criteria and the creative bundle validates 131 evidence files.

Production state:

- technical gate: PASS
- assistant gate: PASS
- user gate: PENDING
- status: USER_REVIEW

No online video-generation model was used.
