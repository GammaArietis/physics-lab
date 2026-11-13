# Laboratory architecture

The repository has two coupled layers: a reusable Python laboratory and a
phase-controlled scientific record.

## Python packages

| Package | Responsibility |
| --- | --- |
| `core` | Models, parameters, observables, results and provenance rules |
| `geometry` | Continuous, discrete and compact geometric structures |
| `dynamics` | Hamiltonians, Lagrangians and eigenproblems |
| `physics` | Physical constructions, phase engines and phase artifacts |
| `theory_kernel` | Grammar, enumeration, closure, equivalence and frontier phases |
| `models` | YAML loading and executable example models |
| `reporting` | Human-readable reports and scorecards |
| `validation` | Validation runners and consistency checks |
| `registry` | Versioned theory-candidate records, provenance gates and isolated comparison |

The root `tests/` directory tests the public and phase-level behavior. The
`examples/` directory contains input models and phase examples.

## Phase artifacts

Phase artifacts are JSON and related files stored next to the phase code under
`src/physics_lab/physics/*_artifacts/`. This is intentional: many phase
modules load prior records through `Path(__file__)` and relative artifact
paths, and later phases verify hashes of earlier artifacts.

Therefore the first cleanup pass does not move those directories. A future
artifact-store refactor must introduce a single path-resolution layer and
update the integrity tests before changing their location.

## Scientific data flow

```text
model input
    -> structure and geometry
    -> derived quantities with provenance
    -> phase grammar and closure checks
    -> authorized finite search
    -> frontier and human decision
```

The flow is deliberately not a theory selector. A valid mathematical model is
not automatically a physical realization, and an experimental comparison is
kept separate from model derivation.

## Candidate registry

`schemas/theory_candidate.schema.json` is the canonical record format. The
`registry` package validates that format without an optional third-party
dependency and applies the laboratory-specific semantic gates. The neutral
template is registered but unselected, has no physical claim, and leaves
search and empirical comparison unauthorized.

The registry is therefore a typed boundary, not a theory generator. A future
runner must consume one registered record, produce derivation steps and
observables, and write its own validation evidence before batch execution is
allowed.

Phase 4 provides that runner for one internal-circle benchmark. It validates
the record, instantiates the existing Hamiltonian model, runs the spectral
derivation, evaluates observables, and emits a portable evidence record. The
runner rejects selection, search activation and experimental sources at its
boundary.

Phase 6 consumes that evidence only after derivation. The isolated comparison
engine accepts an immutable `EXPERIMENTAL_DATA` record and a separate
authorization; it rejects fitting, calibration, parameter updates and
experimental values inside the model report. The comparison result is a
downstream observation, never a new model input.

Phase 7A adds a campaign layer above the single-candidate runner. Its manifest
defines candidate references, timeouts, checkpoint/resume, deduplication and
failure isolation. The readiness audit validates these controls without
executing a candidate or activating selection, search, bounds or empirical
comparison.

## Repository layout

```text
src/physics_lab/     executable package and phase records
tests/               automated tests
examples/            YAML inputs and small model examples
docs/                current state, architecture and history
docs/history/        chronological reports, preserved as historical files
docs/decisions/      decision documents
docs/layout/         canvas/layout files used by the original workflow
```
