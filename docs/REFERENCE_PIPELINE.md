# Phase 4: reference candidate pipeline

Phase 4 closes one controlled path from an action to observables. It uses the
existing internal-circle model as a benchmark because that model already has
independent tests for periodicity, the analytic spectrum, momentum, charge and
the assumed mass map.

This is an engineering and provenance milestone, not a selection of a new
physical theory. Search, finite bounds and empirical comparison remain closed.

## Canonical record and runner

- Candidate record:
  [`schemas/examples/theory_candidate_circle_reference.json`](../schemas/examples/theory_candidate_circle_reference.json)
- Runner:
  [`src/physics_lab/registry/reference_pipeline.py`](../src/physics_lab/registry/reference_pipeline.py)
- Deterministic evidence:
  [`docs/validation/REFERENCE_PIPELINE_CIRCLE_2026-11-13.json`](validation/REFERENCE_PIPELINE_CIRCLE_2026-11-13.json)
- Existing regression evidence:
  [`tests/test_circle_model.py`](../tests/test_circle_model.py)

The candidate is `READY_FOR_DERIVATION` and `selected: false`. Its action is

```text
H = p_xi^2
```

with the explicit chain:

```text
chi(xi + 2*pi*R) = chi(xi)
    -> k*R = n, n in Z
    -> p_n = n*hbar/R
    -> lambda_n = (n*hbar/R)^2
    -> q_n = n*hbar*kappa/R       [ASSUMED Q map]
    -> m_n = sqrt(C*lambda_n)     [ASSUMED mass map]
```

The first four lines are the structural/spectral derivation implemented by
the reference model. The charge operator and mass conversion are explicitly
labelled assumptions. `R`, `hbar`, `kappa` and `C` remain free `INPUT`
parameters; no external datum calibrates them.

The closure audit makes the remaining boundaries machine-readable:

- the vacuum is `NOT_APPLICABLE_BY_SCOPE`, not an uncomputed or selected
  vacuum;
- the integer lattice and discrete spectrum are derived from periodicity;
- this is distinct from field quantization, which remains
  `NOT_PERFORMED`;
- momentum and the eigenvalue are derived forms, while charge is an assumed
  map and mass remains an unresolved assumed map.

## Reproducible command

```bash
PYTHONPATH=src python -c \
  'from physics_lab.registry import write_reference_pipeline_report; write_reference_pipeline_report("docs/validation/REFERENCE_PIPELINE_CIRCLE_2026-11-13.json")'
```

The report uses a display window `n = -2,...,2` only after deriving the full
integer lattice. That window is not a search bound. The report contains no
absolute machine paths and no experimental data.

## What is complete and what is open

Complete:

- action record validated and instantiated;
- PBC-to-integer-lattice derivation;
- analytic spectrum generation;
- momentum, charge and mass observable generation;
- legacy validator execution with zero failures;
- semantic closure audit for parameters, vacuum, quantization and observables;
- portable, deterministic JSON evidence.

Still open:

- the mass map has no derivation from a larger spacetime theory;
- the charge normalization remains free;
- no quantum-field completion is supplied; the vacuum is explicitly outside
  this benchmark's scope rather than silently left ambiguous;
- no empirical comparison is authorized.

Those open items are recorded in the candidate itself rather than silently
converted into claims.
