# Creative QA Workflow

Current default: **schema v3**. Read [Evidence-first review](EVIDENCE_FIRST_REVIEW.md) for complete review-point coverage, source timestamps, full transition shoulders, authored-silence checks and modality-bound review. The schema-v2 sections below describe the inherited checks; v3 adds the stricter requirements.

Phase 6 adds automated **triage signals** and a stronger evidence bundle before assistant acceptance. It does not replace watching the video at normal speed.

The inherited experience signals were introduced in **schema v2**. Schema v2 keeps the original freeze/motion/camera/layout checks and adds the experience-level review system in [EXPERIENCE_REVIEW_WORKFLOW.md](EXPERIENCE_REVIEW_WORKFLOW.md): interior motion cadence, every-cut transition evidence, visual-style continuity, audio boundary/spectral/stem/pacing checks, A/V sync clips, explicit warning dispositions, and before/after repair comparison.

## Command

Build a creative-QA bundle:

    python scripts/creativeqactl.py analyze VIDEO execution-plan.json review/creative-qa

Optional layout metadata:

    python scripts/creativeqactl.py analyze VIDEO execution-plan.json review/creative-qa --layout layout-qa.json

The bundle contains:

- `creative-qa.json`
- a timestamped contact sheet
- one 360px-wide phone-scale frame for each selected review point
- normal-speed H.264/AAC review clips around those same points
- `assistant-review-template.json`

## Automated signals

### Freeze detection

FFmpeg `freezedetect` runs on the actual candidate. Long low-difference spans are reported with exact timestamps.

A freeze signal is evidence, not an automatic creative verdict. Intentional holds are allowed, but the assistant must explain why the hold reads correctly at normal speed.

### Motion density

The candidate is sampled at low resolution and 4 fps. For each frame transition the workflow measures:

- normalized mean pixel delta;
- ratio of pixels changing by at least the configured threshold.

The same signal is aggregated per execution-plan shot.

This catches the failure mode exposed by the earlier Mercy Engine orbit shot: the renderer can technically animate while too little of the final image changes for the movement to read.

The metric does **not** claim that more motion is better. It only finds shots whose intended motion may be visually too weak.

### Camera-pattern repetition

Camera descriptions from the execution plan are normalized into coarse families such as:

- push
- pull
- orbit
- travel/parallax
- elevation
- drift
- hold
- generic move

The report flags consecutive reuse and a family dominating 40% or more of the film. The assistant then decides whether the repetition is intentional grammar or visual monotony.

### Phone-scale readability

Each selected review point gets a real 360px-wide frame from the candidate.

When a production supplies `layout-qa.json`, the workflow can also verify declared text boxes against:

- normalized title/action-safe margin;
- projected font size at 360px phone width.

This is metadata-assisted verification, not OCR.

If no layout metadata exists, the report explicitly says **manual text review required** rather than pretending that pixel statistics prove readability.

### Composition/text boundaries

Use `templates/layout-qa.json` to record production-owned text overlays:

    {
      "id": "title",
      "start_seconds": 0,
      "end_seconds": 3,
      "bbox_norm": [0.10, 0.10, 0.80, 0.12],
      "font_px": 54
    }

`bbox_norm` is `[x, y, width, height]` in normalized frame coordinates.

This keeps important typography geometry durable and lets agents verify safe-area mistakes before final review.

## Normal-speed evidence

Still frames are insufficient for timing, acting, camera feel, motion readability, or audio-picture synchronization.

For each selected review point Phase 6 therefore creates a normal-speed clip. Assistant creative review must cite generated evidence from the QA bundle rather than claiming to have inspected something unbound to the candidate.

Validate a completed assistant review with:

    python scripts/creativeqactl.py validate-review review/creative-qa/creative-qa.json review/creative-qa/assistant-review.json

The review is accepted as structurally valid only when:

- candidate SHA matches;
- QA-report SHA matches;
- every required criterion has a boolean judgment;
- every criterion has written notes;
- every criterion cites a generated QA artifact;
- failures/defects include a concrete next change.

The five required human/assistant judgments are:

- composition and focal hierarchy;
- phone-scale readability;
- visible motion;
- camera variety;
- normal-speed story read.

## Production-controller enforcement

New `templates/production-v2.json` manifests set:

    "creative_qa_required": true

That makes creative QA part of the production state machine rather than a suggestion.

After deterministic `prepare-review`, a new production reports `creative_qa` as its next action until both of these artifacts exist:

- the exact candidate-bound `creative-qa.json`;
- a completed assistant creative review bound to that QA report.

Assistant PASS then uses:

    python scripts/productionctl.py assistant-pass production.json \
      --creative-qa path/to/creative-qa.json \
      --creative-review path/to/assistant-review.json \
      --notes "..."

Before opening user review, `productionctl` verifies:

- the QA report's candidate SHA-256 matches the immutable candidate;
- the contact sheet, phone frames, and normal-speed clips still exist;
- every evidence file still matches its stored SHA-256;
- the assistant review is bound to the current QA-report SHA-256;
- every required creative criterion has explicit evidence-backed notes;
- no failed criterion or unresolved defect remains.

If any creative evidence is modified or disappears after assistant review, later user acceptance fails closed.

Older v2 productions remain backward compatible: when `creative_qa_required` is absent, runtime normalization treats it as `false`. This avoids rewriting historical acceptance state. A legacy film may still be back-tested with Phase 6, but that does not retroactively change its recorded gate.

## What automation may and may not decide

Automation may identify:

- actual freeze spans;
- weak frame-to-frame motion signal;
- repeated declared camera families;
- declared text outside safe bounds;
- declared text likely too small after phone scaling;
- missing metadata/evidence.

Automation may **not** certify:

- whether a composition is beautiful;
- whether acting feels believable;
- whether motion has meaning;
- whether a camera move feels physical;
- whether the story lands emotionally;
- whether text is readable when no trustworthy layout metadata exists.

Those remain evidence-backed assistant review tasks.

## Mercy Engine back-test

Phase 6 was run against the preserved final Mercy Engine candidate `cc3861…`.

Results:

- freeze spans: **0**
- weak-motion shots under the Phase 6 threshold: **0**
- mean changed-pixel ratio across the film: about **12.8%**
- one consecutive camera-family repetition: **scene-09 → scene-10**, both classified as drift
- layout violations: **0 recorded**, because no durable text-layout metadata exists for this older production
- text/phone certification: **manual review required**
- 12 phone-scale review frames generated
- 12 normal-speed review clips generated

The repaired orbital scene averages about **7.0% changed pixels** at the low-resolution 4 fps signal and no longer registers as frozen.

This back-test does not retroactively claim that Mercy Engine was authored under the Phase 6 system. It demonstrates that the new system can inspect the preserved candidate and surface both useful strengths and unresolved manual review work.