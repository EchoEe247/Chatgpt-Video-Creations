# Validated Baselines

This directory is the durable registry for **formal known-good project states**.

It is intentionally stricter than `docs/CAPABILITY_BASELINES.md`. Current user quality judgments such as **respectful**, **medium-bad**, or **failed** belong in `productions/quality-status.json`, not here. A production may be respectful and worth continuing without being baseline-promoted.

## Capability baseline vs validated baseline

`docs/CAPABILITY_BASELINES.md` answers:

> What production capability has already been demonstrated well enough that future sessions should not start from zero?

A formal B-series baseline answers:

> At this exact repository state, with this exact artifact and these render conditions, which named behaviors were actually validated and known-good?

The older business/2D/3D reference videos remain useful capability evidence. They are not being retroactively labeled `B1` because the repository does not currently preserve enough exact artifact + commit provenance for that stronger claim.

## Baseline identifiers

Validated baselines use a repository-wide sequence:

- `B1`
- `B2`
- `B3`
- ...

The identifier describes validation history, not a software release number.

## Required evidence

A baseline entry must identify:

- exact repository commit;
- lane and scope;
- exact representative artifact(s);
- artifact SHA-256 when an artifact is part of the claim;
- render/validation conditions;
- capabilities that passed;
- known limitations;
- anything intentionally not validated;
- technical validation result;
- visual validation result or an explicit statement that visual validation is not applicable;
- user review when the baseline claims user-accepted visual behavior;
- a durable validation/QA receipt.

For visual composition baselines, a green unit test by itself is insufficient.

For technical-only baselines, visual review may be `NOT_REQUIRED`, but the scope must make that limitation clear.

## Promotion rule

A candidate becomes a B-series baseline only after the evidence matches the claim.

Do not promote because:

- code changed;
- CI is green;
- an MP4 decodes;
- one representative frame looks acceptable;
- the agent wants a convenient checkpoint.

Promote when the state is useful as a real recovery/regression reference.

## Regression workflow

When a newer candidate breaks behavior that a baseline covered:

**reproduce candidate → compare to baseline → isolate changed variable → repair → rerun validation → review → promote only if warranted**

The old baseline remains historical evidence after a newer baseline exists.

## Current state

`registry.json` currently contains **B1**.

B1 is the accepted 8-second 2D geometry/composition Candidate 002 reference. Its scope is deliberately narrow: shared floor/contact anchors, portal geometry alignment, camera-transform relationships, board-text attachment, and the accepted Vex hair silhouette under the recorded conditions.

B1 does **not** validate long-form animation, audio, business-video behavior, or 3D production. The registry's `next_id` is `B2`.

Future baselines should still be promoted only from an actually validated/accepted state with durable evidence; do not retroactively relabel older capability references merely to fill the sequence.