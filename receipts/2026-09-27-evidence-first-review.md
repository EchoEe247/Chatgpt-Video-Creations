# SECOND EARTH independent audit and workflow upgrade

Date: 2026-09-27
Execution: direct Local Workspace; one ChatGPT agent, no delegated model or paid generation.

## Scope and evidence

Audited the exact iteration-03 candidate:
`653ee90a00f49393edac5938770befe244a4cfe3fbb33592753287b7513e9912`.

Inspected all 21 prior phone-scale frames, targeted later reveals/text, and the four expanded renderer-transition strips. Read the execution plan, renderers, finishing implementation, audio builder and prior review. No continuous playback or audible listening is claimed.

The video proves a working local 150-second, 21-shot, multi-renderer production chain. The audit found sparse city staging, unreadable physical detail in the dark server view, tiny untracked supporting labels, repeated color-fade finishing, and unresolved authored silence. The main messages and final thesis are readable in the targeted frames.

## Implemented workflow changes

- Schema v3 is now the default.
- Every authored point and timed text midpoint is included: 44 + 5 = 49 on this film, versus the old 21.
- Evidence caps disclose omissions and block v3 acceptance.
- Each point requires a rendered-event observation and intent comparison.
- Review criteria require appropriate inspection modalities; stills/metrics cannot support audio or motion PASS.
- Full-film audiovisual review must be explicitly recorded before overall PASS.
- Contact-sheet labels now use source sampling times; extraction handles short videos and avoids JPEG range incompatibility with PNG intermediates.
- Transition evidence extends beyond full authored fade shoulders.
- Color-fade usage is visible: 12 of 20 boundaries on this candidate.
- Text metadata no longer implies that every rendered label was checked.
- Narration QA checks 200 ms active-speech windows; 14 shots now contain listening targets that whole-shot averages hid. These are not confirmed audible masking defects.
- Designed-silence QA checks the encoded stereo master and named diagnostic stem. Stereo retention avoids false silence from phase cancellation.
- Source timeline/layout/transition/stem hashes are recorded.
- Duplicate warning dispositions are rejected.
- A reusable audit-page builder presents findings beside exact frames/clips and verifies candidate/evidence bindings.
- The benchmark status test now uses the controller's canonical statuses, including the legitimate refinement state.

## Audio findings

Stereo master measurements:

| Event | Interval | RMS | Peak | Loudest 50 ms RMS |
| --- | --- | --- | --- | --- |
| Boundary drop | 84.70–85.15 s | -44.61 dBFS | -34.51 dBFS | -42.86 dBFS |
| Final silence | 149.30–150.00 s | -37.30 dBFS | -13.29 dBFS | -27.14 dBFS |

The timeline's silence scope is unspecified; the builder does not execute designed_silence events. The effects stem is silent at the boundary, while the combined master is not below the configured -50 dBFS review threshold. The closing interval contains a much stronger residual, including the narration tail. Decide master/stem scope explicitly and preserve final words before repairing the envelope.

Polished stems branch before final limiting and normalization. They are diagnostic pre-master components, not proven exact post-master stems.

## Validation and delivery

- All 187 generated evidence artifacts validated against stored hashes.
- Audit page returned HTTP 200.
- Original video supports byte ranges: HTTP 206.
- Exact original candidate SHA preserved.
- Full unit/integration suite: **124 passed in 50.56 seconds** on the final code state.
- Expanded audit metrics preserved in `receipts/2026-09-27-second-earth-independent-audit.json`.
- Ranked findings: `productions/standalone/second-earth-benchmark/source/iteration03-independent-audit.json`.
- Reproduction entry points: `creativeqactl.py analyze` and `make_experience_audit.py`.
- Full instructions: `docs/EVIDENCE_FIRST_REVIEW.md`.

Current production state: REFINEMENT_REQUIRED; assistant FAIL, technical PASS, user PENDING. Prior iteration media and v2 evidence are preserved. This run improved the workflow and completed an independent audit; it did not produce a repaired fourth iteration or claim an audible quality verdict.

Review page: http://127.0.0.1:8880/review/experience-qa-v3/index.html
