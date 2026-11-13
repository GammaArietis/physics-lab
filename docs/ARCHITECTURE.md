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
