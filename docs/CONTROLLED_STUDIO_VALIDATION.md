# Controlled Studio Validation

Package H validates the workflow without using the user's withheld production issue as tuning data.

## Two separate validations

The workflow intentionally separates:

1. **Controlled media benchmark** — opaque fixtures, seeded defects, clean controls, concealed answer key, frozen findings, then scoring.
2. **Operational fresh-session handoff** — verifies that a new agent can discover the production profile, run preflight, understand the authoritative promotion contract, operate a persisted review bundle, and preserve modality semantics.

Operational success is not evidence that the fresh agent perceived media correctly. Perception scores and operability scores remain separate.

## Controlled benchmark lifecycle

Use:

```text
python scripts/studiovalidate.py freeze --output .runtime/studio-validation/<run>
python scripts/studiovalidate.py freeze-findings --package <run>/benchmark-package.json --findings <run>/findings.json --contamination PARTIALLY_BLINDED
python scripts/studiovalidate.py score --package <run>/benchmark-package.json
```

`freeze` creates six opaque six-second media fixtures. Public filenames are random IDs. The neutral package publishes only the allowed defect taxonomy and instructions. The answer key is stored outside repository/workspace roots under local state and is not returned in the package.

Seed set:

- one clean control;
- sustained picture freeze;
- brief transition discontinuity;
- low-readability timed text;
- 60 Hz tonal/hum defect;
- 500 ms picture/sound synchronization offset.

The answer key defines severity, required modality, expected interval, and localization tolerance before review begins.

## Findings format

`findings.json` contains:

```json
{
  "unavailable_modalities": ["auditory"],
  "fixtures": {
    "<opaque fixture id>": {
      "findings": [
        {
          "code": "freeze",
          "severity": "high",
          "start_seconds": 2.0,
          "end_seconds": 3.0,
          "claim_type": "perceived",
          "notes": "..."
        }
      ]
    }
  }
}
```

Do not guess unavailable modalities. Expected defects whose required modality is explicitly unavailable are counted separately as `unavailable_expected`, not false negatives.

## Freeze-before-reveal rule

`freeze-findings` records the package SHA, findings SHA, contamination classification, context exposure, unavailable modalities, and exact submitted findings under local state. A second different submission for the same benchmark is rejected.

`score` refuses to read/reveal the hidden answer key until frozen findings exist and still match the package hash.

## Scoring

The report includes:

- true positives;
- false negatives;
- false positives;
- expected defects excluded because the modality was unavailable;
- precision and recall over scorable expected defects;
- clean-control false-alarm rate;
- median localization error;
- exact and within-one severity agreement.

Localization tolerances are frozen by taxonomy before audit. Findings outside tolerance do not count as localized detections.

## Blindness labels

- `BLINDED` — prior findings, repair history, answers, and related memory/context are demonstrably absent.
- `PARTIALLY_BLINDED` — a fresh or isolated evaluator was used, but complete exclusion of prior contextual exposure cannot be proven.
- `NOT_BLINDED` — prior findings or implementation answers were visible to the evaluator.

When uncertain, use `PARTIALLY_BLINDED`.

## User-held final issue

The user-held VELOCITY issue is explicitly excluded from benchmark generation, answer keys, detector thresholds, and repair logic. The score report keeps it as `NOT_REVEALED_NOT_SCORED`.

Only after benchmark findings are frozen may a future audit compare its independent VELOCITY findings to that holdout. A miss is recorded as a miss; the workflow is not retroactively tuned before the receipt is preserved.

## Operational handoff

Generate the neutral handoff package with:

```text
python scripts/studiovalidate.py handoff --output <path> --bridge-commit <sha> --video-commit <sha>
```

A fresh operational evaluator receives no controlled-benchmark answer key. It is scored independently on exact tool discovery, studio preflight, promotion-contract understanding, persisted review-bundle operation, and correct sampled/continuous/audio-perception semantics.

Score the fresh-session operability report separately:

```text
python scripts/studiovalidate.py score-handoff --package <handoff.json> --report <operational-report.json>
```

The operational report must bind the exact bridge/video commits and record PASS/FAIL plus evidence for tool discovery, preflight, promotion-contract understanding, persisted bundle operation, and modality/coverage semantics. The score explicitly sets `perception_score_included=false`.

## Package H validation receipt

Controlled benchmark `studio-61a2c207182816a3` used package SHA-256 `ce33564d45e42592c6a1b57010f635653b57277fc88af02b2f2f173ac182b78b`. A fresh Hermes collaboration running GPT-6 Luna received only the opaque benchmark directory. Because it ran on the same device/runtime and total prior-context isolation cannot be proven, the run is classified **PARTIALLY_BLINDED**.

Findings SHA-256 `e6ee7b7bcb9c447ffb56bfdfda68d9c9e19c7e400b6e4ae57649d8527fb33e44` was frozen before answer-key scoring. Result: **0 TP, 3 FN, 2 FP, 2 unavailable expected**, precision 0.0, recall 0.0, clean-control false-alarm rate 0.0. Auditory and synchronized-A/V were declared unavailable rather than guessed.

This failed benchmark is preserved as validation evidence and is not used to retroactively tune the benchmark. The user-held production issue remains `NOT_REVEALED_NOT_SCORED`.
