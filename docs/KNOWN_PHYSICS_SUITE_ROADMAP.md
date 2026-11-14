# Known-physics suite roadmap

Status: registered 14 November 2026.

## Purpose

The laboratory will cover known physics as a collection of explicit,
reproducible baselines. A baseline is not a new theory claim and is not
automatically an empirical validation. It is an executable record that keeps
the mathematical model, assumptions, parameters, observables and tests
separate.

Coverage is intentionally staged. No finite catalog can literally contain
every physical system, approximation or material model. The target is a
canonical coverage of the main frameworks, with controlled scope and an
explicit record of what remains outside each baseline.

## Completed baselines

- Quantum harmonic oscillator: action, canonical quantization, vacuum, exact
  spectrum and parameter-free gap ratio.
- Free real scalar field: Klein–Gordon action, canonical field
  quantization, Fock vacuum, periodic mode spectrum and parameter-free
  squared-frequency ratio in the declared 1+1-dimensional scope.

The circle model remains an internal structural reference and is not counted
as a known-physics baseline.

## Implementation order

| Wave | Families | First executable targets | Gate |
| --- | --- | --- | --- |
| K1 | Classical and nonrelativistic mechanics | Free particle, Kepler problem, particle in a one-dimensional box | Exact equations, boundary conditions, conserved quantities and regression tests |
| K2 | Quantum mechanics | Coulomb/hydrogen spectrum, spin-1/2 Pauli system, angular momentum algebra | Hilbert-space scope, operators, ground state and parameter-free ratios |
| K3 | Classical and relativistic fields | Maxwell vacuum, Newtonian gravity, Einstein-Hilbert vacuum | Gauge or diffeomorphism constraints, field equations and controlled observables |
| K4 | Free relativistic quantum fields | Dirac field, Proca field, quantized Maxwell field | Canonical or covariant quantization, constraints, vacuum and mode spectrum |
| K5 | Controlled interacting theories | Scalar phi-four theory, classical Yang–Mills, structural Standard Model | Renormalization or truncation scope stated explicitly; no hidden calibration |
| K6 | Statistical and condensed-matter controls | Ising lattice, harmonic lattice and phonons, ideal Bose/Fermi gas | Finite-size or thermodynamic-limit convention and uncertainty provenance |
| K7 | Cosmology and gravitation | FRW background and perturbations, Schwarzschild vacuum | Geometric assumptions, constraint closure and observable scope |

These waves are a coverage plan, not an authorization to search or rank
theories. Each target enters the campaign only after its record and runner
pass the admission requirements below.

## Admission requirements for every baseline

1. Candidate record with explicit field content, geometry and scope.
2. Action or Hamiltonian, including all terms and provenance labels.
3. Constraints, symmetries and boundary or initial conditions.
4. Quantization status when the target is quantum or a quantum field.
5. Ground state or vacuum statement, including any unresolved choice.
6. Complete parameter inventory: derived, assumed, input and calibrated.
7. At least one executable observable, preferably parameter-free.
8. Independent regression tests and a reproducible pipeline report.
9. A separate target-blind empirical-comparison record, only if explicitly
   authorized later.

## Campaign policy

- The current Mac benchmark is infrastructure evidence, not a physical
  catalog of 64 theories.
- The first expansion batch will contain only genuinely distinct,
  registered baselines, initially 8–16 candidates with four workers.
- Results will be recorded without automatic selection or ranking.
- Empirical data, fitting and calibration remain outside the execution
  campaign.
- Historical phase artifacts remain preserved; they are not promoted to
  executable known-physics candidates without passing this contract.
- Nonperturbative QCD, turbulence and uncontrolled many-body approximations
  require dedicated numerical/error models before inclusion.

## Current frontier

The K1 particle-in-a-box baseline is now implemented and validated on the Mac.
The next controlled step is the three-candidate real campaign combining the
oscillator, free scalar field and particle in a box. Only after that campaign
has been reviewed will the suite advance to K2 targets such as the hydrogen
and spin-1/2 baselines.

Machine-readable inventory:

    schemas/examples/known_physics_suite_manifest.json
