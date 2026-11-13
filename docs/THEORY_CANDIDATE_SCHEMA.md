# Theory-candidate registry

The registry is the first controlled interface between the historical phase
record and a future theory runner. It records one candidate without silently
turning registration into selection, search authorization, or physical
validation.

## Canonical files

- [`schemas/theory_candidate.schema.json`](../schemas/theory_candidate.schema.json): JSON Schema Draft 2020-12, version `theory-candidate-v1`.
- [`schemas/examples/theory_candidate_template.json`](../schemas/examples/theory_candidate_template.json): neutral, unselected template.
- [`src/physics_lab/registry/theory_candidate.py`](../src/physics_lab/registry/theory_candidate.py): standard-library validator and file loader.
- [`tests/test_theory_candidate_registry.py`](../tests/test_theory_candidate_registry.py): contract tests for the gates below.

The template is intentionally not a physical theory. It contains no fields,
action, parameters, vacuum, observables, or external data and has
`search_status: NOT_ACTIVATED`.

## Record contract

| Section | What it records | What it does not claim by itself |
| --- | --- | --- |
| `fields` | Field roles and representations | A complete field content |
| `geometry` | Spacetime, internal space and connections | A selected geometry |
| `action` | Formulation, terms, expression and freeze state | A derived dynamical law |
| `constraints` | Gauge, primary, secondary and consistency constraints | Verified consistency |
| `parameters` | Free, fixed, derived, calibrated and unresolved quantities | A parameter fit |
| `vacuum` | Selection state, stationarity, minima and moduli | A selected vacuum |
| `quantum` | Quantization status and quantum consistency checks | Quantum completeness |
| `observables` | Expressions, dependencies, free parameters and comparison status | A prediction when inputs remain free |
| `provenance` | Sources, derivation steps and decisions | Permission to use experimental data in derivation |
| `authorization` | Explicit gates for search, bounds and comparison | Authorization merely by registration |
| `validation` | Mathematical, reproducibility and provenance audit status | A physical result without a completed comparison |

## Non-negotiable gates

The validator enforces the following controls in addition to the JSON Schema:

1. Repository paths are relative; machine-specific absolute paths are
   rejected.
2. Identifiers are unique within each record collection.
3. A `DERIVED` parameter must expose a formula or dependencies. A derived
   label cannot be used as a hidden inserted value.
4. A `PREDICTED` observable must be derived, expose an expression, and have
   no free parameters.
5. Experimental data cannot be referenced by a `DERIVED` provenance step.
6. Historical sources must be marked immutable.
7. Active search statuses require an explicit `authorization_ref`.
8. Selection is explicit: `selected: true` is valid only with
   `SELECTED_FOR_REFERENCE_PIPELINE`.

The provenance labels distinguish `DERIVED`, `ASSUMED`, `CALIBRATED`,
`INPUT`, and `EXPERIMENTAL`. The last one is comparison-only and cannot leak
back into model derivation.

## Validation from a checkout

```bash
PYTHONPATH=src python -c \
  'from physics_lab.registry import load_theory_candidate; load_theory_candidate("schemas/examples/theory_candidate_template.json"); print("VALID")'
```

The next controlled step is to register one concrete formulation and run it
through derivation, consistency and observable generation. Batch search,
finite bounds and empirical comparison remain closed until that reference
pipeline has its own auditable record.
