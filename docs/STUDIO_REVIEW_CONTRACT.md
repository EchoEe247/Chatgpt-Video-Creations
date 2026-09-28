# Studio Review and Promotion Contract

This contract separates production workflow state from final acceptance authority.

## Authoritative promotion states

`src/core/studio_review.py` owns promotion derivation. There are four authoritative states:

- `REFINEMENT_REQUIRED` — a blocking known defect exists.
- `VERIFICATION_REQUIRED` — no blocking defect is known, but required evidence, modality, binding, or review is incomplete/stale.
- `ASSISTANT_ACCEPTED` — every blocking assistant-side requirement that is applicable is satisfied.
- `USER_ACCEPTED` — assistant acceptance remains valid and the user gate is explicitly accepted.

Legacy `review.assistant` and `review.user` fields are compatibility aliases only. They may never independently grant acceptance. A specialized gate such as cinematic/physical QA can veto a legacy assistant PASS.

## Applicability and criterion state

Each studio criterion is either:

- `APPLICABLE`, with status `PASS`, `FAIL`, or `UNVERIFIED`; or
- `NOT_APPLICABLE`, with a concrete reason and no PASS/FAIL/UNVERIFIED status.

`UNVERIFIED` means required evidence or modality is unavailable, incomplete, stale, or not yet reviewed. It is not a synonym for not applicable.

A blocking `PASS` must cite evidence that has reached `REVIEWED`.

## Evidence lifecycle

Evidence has a monotonic lifecycle:

`PLANNED → GENERATED → DELIVERED → REVIEWED`

Generation does not prove delivery. Delivery does not prove review. The lifecycle may not move backward.

Candidate-bound evidence becomes stale when the candidate SHA changes.

## Historical migration

Historical manifests remain evidence, not something to retroactively declare compliant with this contract.

Runtime migration currently normalizes known historical state labels conservatively:

- `FINAL_CANDIDATE` becomes workflow `VERIFICATION_REQUIRED`.
- legacy assistant labels such as `PASS_WITH_REVIEW_NOTES` and `PASS_WITH_CINEMATIC_REFINEMENT_REQUIRED` become `PENDING` for current promotion purposes.
- a missing historical `delivery.baseline_compare_fps` receives the old default of `2.0` in memory.

The original historical file is not rewritten merely by reading or validating it.

## Promotion rules

Technical failure, a specialized blocking gate failure, an applicable blocking criterion failure, or an explicit assistant/user failure produces `REFINEMENT_REQUIRED`.

Missing required studio review, `UNVERIFIED` blocking criteria, stale candidate bindings, pending technical/assistant gates, or pending specialized verification produce `VERIFICATION_REQUIRED`.

Only the central promotion derivation may produce assistant or user acceptance. `productionctl assistant-pass` checks that derivation before opening user review.

## Operational rule

Never report “PASS” because one subsystem passed. Report the authoritative promotion state plus blocking failures/unverified requirements.

For serious productions, later workflow packages will set `workflow.studio_review_required=true` and populate departmental criteria/evidence. Historical and lightweight manifests remain readable with the default disabled until migrated deliberately.
