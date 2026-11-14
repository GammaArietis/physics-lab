# Phase 6: isolated experimental comparison

Phase 6 adds the final comparison boundary without turning experimental data
into a model input. The comparison receives a completed JSON model report and
an immutable comparison-only dataset after derivation has finished.

## Canonical files

- [`schemas/experimental_comparison.schema.json`](../schemas/experimental_comparison.schema.json): dataset contract.
- [`schemas/examples/experimental_comparison_template.json`](../schemas/examples/experimental_comparison_template.json): empty, immutable template.
- [`src/physics_lab/registry/experimental_comparison.py`](../src/physics_lab/registry/experimental_comparison.py): validator and comparison engine.
- [`docs/validation/EXPERIMENTAL_COMPARISON_GATE_2026-11-13.json`](validation/EXPERIMENTAL_COMPARISON_GATE_2026-11-13.json): deterministic evidence for the current circle candidate.
- [`schemas/examples/experimental_dataset_h2_harmonic_oscillator_control.json`](../schemas/examples/experimental_dataset_h2_harmonic_oscillator_control.json): frozen H₂ comparison-only dataset.
- [`docs/validation/EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json`](validation/EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json): target-blind scope-control result for the oscillator baseline.

The gate requires a separate authorization record with:

- `status: AUTHORIZED` or `COMPLETE`;
- a non-empty `authorization_ref`;
- `target_blind: true`;
- `fitting: false`, `calibration: false` and `parameter_updates: false`.

The dataset must be immutable, explicitly marked `EXPERIMENTAL_DATA`, carry a
source digest, and use the role `comparison-only`. The engine compares only
observables marked `DERIVED` with no free dependencies. An observable with
free parameters, an assumed map, or no model counterpart is reported as
blocked; it is never silently fitted or calibrated.

The current circle candidate is intentionally not promoted to an empirical
claim. Its momentum and eigenvalue observables retain free inputs, while its
charge and mass maps are assumed. The phase-6 evidence therefore records a
blocked comparison and proves that the isolated gate does not mutate the
derivation report or update any parameter.

The first real dataset has now exercised the gate with the known-physics
oscillator. It uses independent H₂ vibrational line measurements and returns
`OUTSIDE_UNCERTAINTY` for the ideal gap ratio. Because H₂ is not an exact
harmonic oscillator, this is recorded as a scope-control result rather than a
direct validation or falsification claim for the ideal baseline. A
scope-matched empirical dataset remains open.
