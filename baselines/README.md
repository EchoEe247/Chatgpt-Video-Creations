# Validated Baselines

This directory is the durable registry for **formal known-good project states**.

It is intentionally stricter than `docs/CAPABILITY_BASELINES.md`.

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

`registry.json` is intentionally empty.

The shared 2D geometry relationships are structurally tested, but the corrected renderer has not yet produced and passed the visual reference needed to establish the first formal visual baseline.

The first B-series baseline should be created from an actually accepted production state rather than assigned retroactively.
