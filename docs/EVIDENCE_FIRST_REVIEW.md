# Evidence-first review (schema v3)

SECOND EARTH iteration 03 exposed a gap between a technically valid film and a convincing viewing experience. The candidate remains useful proof of local production capability. Its old green gate does not resolve sparse scene content, unreadable secondary labels, repeated color dips, or unmet audio intent.

## What changed

| Failure found | Reusable change |
| --- | --- |
| First point only: 21 sampled points from 44 authored points | Generate every authored point, every timed text midpoint, and a fallback point for otherwise unannotated shots |
| A positive clip cap silently reduced evidence | Default limit is 0 (all); capped bundles list missing point IDs and cannot pass the v3 review |
| Contact-sheet timestamps came from a retimed stream | Extract explicit source frames, label source sampling times, and clamp to available video frames |
| Transition strips could remain inside a long fade | Sample clear context outside both authored shoulders, with six-frame strips and matching clips |
| Low cut distance treated as proof of coherence | Expose color-fade count/ratio and require a rhythm disposition; inspect scene geometry, scale, motion direction and story handoff |
| Text metadata covered only five text items | Declared boxes never certify a complete rendered-text inventory; manual inspection remains required |
| Whole-shot narration margin concealed local collisions | Add 200 ms speech-active margin windows with exact time ranges; results are listening targets |
| Designed silence was not checked in final encoded audio | Measure every designed_silence interval in the master and available named stem |
| Audio criteria could cite a contact sheet | PASS requires explicit listening/audiovisual modality and temporal evidence |
| Story judgments repeated the plan | Require an observed event and intent_match for each exact review point |
| A local repair was treated as film approval | Overall PASS requires a hash-bound completed full-film audiovisual review declaration |
| Motion metrics showed activity while the hero could still read as moving backward | Review subject orientation, world-space travel, screen direction and contact semantics at normal speed; motion magnitude is not motion correctness |
| Environment proof/assets existed while the final world could still look unfinished | Review environment completeness from actual hero/wide/action cameras; asset presence is not production completeness |
| Review playback existed but was inconvenient to revisit | User-facing review pages must expose working seek/scrub/rewind controls before handoff |

## Review honestly

The schema records the method used; it cannot prove that a reviewer actually watched or listened. Do not fabricate observations to satisfy the validator. Playback counters and generated files do not establish perception.

Still inspection can support composition/readability. Motion and pacing require normal-speed playback. Audio continuity and narration clarity require audible listening. A/V synchronization requires audiovisual playback. If the execution surface cannot provide a modality, leave that criterion false, record the limitation, and continue useful implementation and measurement work. This is an evidence limitation, not a request for user permission.

Historical v1/v2 evidence stays readable. Newly generated reports default to v3. Never rewrite old candidate evidence to suggest it was reviewed under the new contract.

## Audio intent

A designed_silence event should state:

- silence_scope: master or stem;
- stem when scope is stem;
- at_seconds and duration_seconds;
- optional silence_threshold_dbfs (default -50 dBFS RMS per 50 ms window).

Unspecified scope is a review target, not an assumed master mute. Check the final encoded master after all mixing and gain processing. Stereo channels are retained to avoid opposite-phase cancellation creating false silence. The threshold is a triage setting, not a universal audibility boundary.

When repairing a missing silence, inspect narration tails first. Shorten/reposition the line or revise the authored timing deliberately; do not blindly cut a final word. Recheck the encoded result and listen to it.

Speech-window margins use the diagnostic stems. They can flag breaths or syllable tails and need listening disposition. A short-window flag is not proof of masking.

SECOND EARTH's polished stem exports branch before master limiting/normalization. Call them pre-master diagnostic components, not exact post-master stems. Hashes preserve analysis inputs but do not establish reconstruction equivalence.

## Commands

    python scripts/creativeqactl.py analyze VIDEO EXECUTION_PLAN OUTPUT \
      --layout LAYOUT --timeline TIMELINE --stems-dir DIAGNOSTIC_STEMS

    python scripts/creativeqactl.py validate-bundle OUTPUT/creative-qa.json

    python scripts/creativeqactl.py validate-review \
      OUTPUT/creative-qa.json OUTPUT/assistant-review.json

For an independently recorded findings document:

    python scripts/make_experience_audit.py \
      OUTPUT/creative-qa.json FINDINGS.json OUTPUT/index.html

The page verifies candidate/evidence bindings, presents exact frames and clips, and distinguishes observed findings from measurement and unreviewed perception.

## Render priorities learned from this candidate

Before an expensive full-shot render, inspect the start, peak event and end state. Ask whether the actual picture communicates the promised event without reading the director brief. For this film, replace the radial bars with connected city structure, expose a readable physical focal object in the server room, and remove delivery debug labels.

Use transitions after fixing scene content. A shared flat color can smooth pixel statistics while leaving the scene languages unrelated. Match shape, scale, screen direction, spatial context or a story event where possible; inspect whether a fade earns its duration.

Do not claim a visual improvement until its revised pixels have been inspected. This audit implements a stronger review workflow; it does not claim to have repaired the entire film.
