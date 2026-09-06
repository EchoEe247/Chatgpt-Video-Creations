# Baseline Validation Receipts

Create one immutable receipt for each promoted B-series baseline.

A baseline receipt should record:

- baseline ID;
- exact repository commit;
- lane and scope;
- exact artifact reference(s) and SHA-256;
- render/validation conditions;
- tests/checks executed;
- visual review summary when applicable;
- user review result when visual acceptance is claimed;
- validated capabilities;
- known limitations;
- intentionally unvalidated areas;
- comparison baseline when this supersedes an earlier known-good state.

The receipt supports `baselines/registry.json`; it does not replace the registry entry.

Do not create a baseline receipt for a candidate that has not actually passed the promotion gate.
