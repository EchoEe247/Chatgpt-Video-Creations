# SECOND EARTH benchmark

SECOND EARTH is the fresh integrated benchmark produced after the Mercy Engine workflow upgrades.

## Final review status

**Phase 7C plus the user-triggered Experience Review repair is complete.** The production is now in `USER_REVIEW` on iteration 02.

Final candidate:

- runtime: 150.000 seconds
- video: H.264, 1280×720, 24 fps, yuv420p
- audio: AAC, 48 kHz stereo
- SHA-256: `025c7fcf2ec101a6c892ed8d821fb7b6683822b7b61bb499724aa318e5a91bbd`
- technical QA: PASS
- creative QA: PASS
- assistant review: PASS
- user review: PENDING
- local review page: `http://127.0.0.1:8880/`

The user gate must remain pending until Angel explicitly accepts the actual final candidate.

## Story

A high-speed AI simulation develops an emergent civilization. The civilization discovers the edge of its sky, launches a probe toward it, and eventually sends increasingly direct messages to its creators. After contact with the boundary, humans detect the same signal pattern in our own cosmic background, raising the possibility that our universe may also be nested.

The resolution rejects both immediate destruction and unconstrained acceleration. The operators slow the inner world's clock, separate control domains, and keep communication reversible while discovery continues in both directions.

## Production structure

The film uses 21 purposeful shots across:

- deterministic Python/Pillow/NumPy motion design;
- integrated hand-drawn Canvas sequences;
- Blender physical/server-vault scenes;
- Blender probe/orbit/station scenes;
- FFmpeg editorial/contact/final shots;
- deterministic local score, ambience and effects;
- cached Deepgram narration.

No online video-generation model is part of the production.

## Phase 7C repair history

Iteration 00 passed technical QA but **failed assistant creative review**. It was not exposed to the user.

Candidate-bound evidence identified concrete defects:

- the simulated city was too small at phone scale;
- probe-world shots read as placeholder primitive geometry;
- `WE CAN SEE YOU` was clipped;
- shot 13 → shot 14 repeated push-family camera grammar;
- the final title card was effectively static and triggered weak-motion QA.

Repair cycle 1 addressed those defects:

- enlarged and accelerated the illustrated civilization growth;
- rebuilt the probe lane around the verified Quaternius spacecraft asset;
- changed the probe renderer to Eevee with authored lighting and improved planet/station scale;
- fixed the second-message window and typography;
- converted shot 14 into a locked analytic frame with lateral map traversal;
- carried moving spatial imagery into the final thesis instead of ending on a static card.

Iteration 01 then passed all required gates.

## Final evidence

Technical QA:

- decode: PASS
- duration: 150.000 seconds
- resolution: 1280×720
- frame rate: 24 fps
- H.264 / yuv420p
- AAC stereo / 48 kHz
- integrated loudness: -17.18 LUFS
- true peak: -2.02 dBFS
- longest unintended silence: 0.0 seconds

Experience Review v2:

- freeze spans: 0
- weak-motion shots: 0
- immediate cut-discontinuity warnings: 0
- consecutive camera-family repeats: 0
- audio-transition warnings: 0
- narration-mix warnings: 0
- authored-effect sync-offset warnings: 0
- layout violations: 0
- candidate-bound evidence files: 131
- 11/11 assistant criteria: PASS
- two remaining triage warning classes explicitly dispositioned as intentional with evidence

## Blender reliability architecture

The Pixel/PRoot Blender path cannot be treated like a workstation render farm. Long renders can encounter EGL/PRoot instability.

The durable workflow therefore uses:

1. authored Blender scenes;
2. low-rate PNG spatial checkpoints;
3. preserved successful frames across interruptions;
4. missing-frame resume instead of restarting the lane;
5. local reel encoding after the required checkpoint count exists;
6. 24 fps delivery conversion at the shot boundary;
7. deterministic tail correction so authored durations remain exact.

The repaired probe lane uses 4 fps Eevee source checkpoints with 8 render samples, then local 24 fps delivery interpolation. This is explicitly recorded rather than hidden.

## Local review

Start or keep the local review server running from this production directory:

    python serve.py

Then open:

    http://127.0.0.1:8880/

The page supports byte-range requests for normal seeking.

## Source of truth

Read these in order:

1. `source/story.md`
2. `source/director-brief.json`
3. `source/storyboard.md`
4. `source/asset-resolution.json`
5. `source/execution-plan.json`
6. `source/implementation-map.json`
7. `source/av-events.json`
8. `source/av-timeline.json`
9. `source/layout-qa.json`
10. `source/benchmark-acceptance.json`
11. `render_benchmark.py`
12. `production.json`
13. `iterations/iteration-02/qa/technical-qa.json`
14. `iterations/iteration-02/qa/creative-qa/creative-qa.json`
15. `iterations/iteration-02/qa/creative-qa/assistant-review.json`
16. `source/transition-finish.json`
17. `finish_transitions.py`

The next state transition is user acceptance or a new repair cycle based on Angel's actual review.

## Post-review experience-QA audit

Angel's first watch identified a broader issue than any single bad frame: some renderer/scene changes do not feel smooth or like they belong to the same film.

That feedback triggered the schema-v2 experience-review upgrade in the repository.

Running the same SECOND EARTH final candidate through the new system produced:

- freeze spans: 0
- weak-motion shots: 0
- interior motion-cadence warnings: 0
- camera-family repeats: 0
- audio-transition warnings: 0
- narration-mix warnings: 0
- layout violations: 0
- **visual-transition review targets: 6**
- candidate-bound evidence files verified: 131

The six review-target boundaries are:

- shot-01 → shot-02
- shot-02 → shot-03
- shot-03 → shot-04
- shot-15 → shot-16
- shot-17 → shot-18
- shot-18 → shot-19

The current user gate remains PENDING. The older assistant PASS is preserved as historical iteration-01 state, but a future schema-v2 PASS must explicitly inspect/disposition those transition warnings and perform the expanded audio/A-V review rather than relying on the old five-criterion creative gate.

See `docs/EXPERIENCE_REVIEW_WORKFLOW.md` and `receipts/2026-09-27-experience-review-v2.md`.
## Iteration 02 — experience-review continuity repair

Angel's first full review of iteration 01 identified a film-level issue the older gate did not capture strongly enough: some otherwise-good shots felt unsmooth or visually disconnected from the surrounding scene language.

Iteration 02 is the first candidate reviewed under the repository's schema-v2 Experience Review workflow.

Candidate SHA-256:

`025c7fcf2ec101a6c892ed8d821fb7b6683822b7b61bb499724aa318e5a91bbd`

Changes:

- added a durable `transition-finish.json` contract instead of hand-editing the master;
- added short shared-color continuity bridges only at renderer/style boundaries that review evidence justified;
- added bridges for the newly surfaced 06→07, 07→08, 13→14, 16→17 and 19→20 boundaries;
- lengthened the highest-contrast paper↔dark handoffs;
- changed shot 21 so its opening grade inherits shot 20 before gradually darkening into the thesis instead of jumping darker on the cut;
- preserved all original authored shot durations and the 150-second master runtime;
- left the audio master unchanged because expanded stem/boundary analysis found no concrete audio defect requiring a destructive remix.

Final schema-v2 evidence:

- strict decode: PASS
- technical QA: PASS
- freeze spans: 0
- weak-motion shots: 0
- immediate visual cut-discontinuity warnings: 0
- audio-transition warnings: 0
- narration-mix warnings: 0
- authored effect A/V sync offset warnings: 0
- layout violations: 0
- 131 candidate-bound evidence artifacts verified
- 11/11 assistant review criteria: PASS

Two triage warnings remain intentionally visible rather than hidden:

- `motion_cadence_review` for shots 17/18 — normal-speed evidence shows discrete authored diagram/state changes, not stutter;
- `visual_style_shift_review` for four paper/physical/procedural context shifts — their renderer language is intentionally different, but the actual cuts now pass through explicit shared visual bridges and no longer trigger immediate discontinuity warnings.

Both warnings were explicitly dispositioned as `accepted_intentional` with candidate-bound evidence. They were not silently discarded.

Production state is now `USER_REVIEW`; the user gate remains PENDING until Angel explicitly accepts this iteration.