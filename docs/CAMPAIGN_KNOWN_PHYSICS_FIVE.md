# Bounded five-candidate known-physics campaign

This campaign combines five independently executable baselines:

- quantum harmonic oscillator;
- free real scalar field;
- quantum particle in a one-dimensional box;
- spinless non-relativistic fixed-center hydrogen Coulomb problem;
- spin-only two-level Pauli spin-1/2 system.

The Pauli scope is deliberately limited to
`H = (hbar*omega/2)*sigma_z`, the Pauli matrix algebra, the two spin
projections and the normalized splitting. Orbital motion, spin-orbit coupling,
fine structure, relativistic corrections, external data and empirical
comparison are separate future gates.

This is a bounded reproducibility campaign. It does not activate a search,
select or rank theories, fit parameters, use external data or perform an
empirical comparison.

## Readiness and execution

The campaign is prepared but the activation record remains `NOT_RUN`. After
human review, run from the repository root:

    git pull --ff-only origin optimize/phase14l-14n
    source .venv/bin/activate
    export PYTHONPATH="$PWD/src"

    python tools/run_known_physics_five_campaign.py

Use the checked-in launcher rather than a Python heredoc. macOS uses
multiprocessing spawn, so the parent program must have a real filesystem path.

Expected result:

- `execution_status: COMPLETE`;
- all five candidates `PASS`;
- all records unchanged;
- all campaign controls true;
- `selection.performed: false`;
- `selection.ranking_performed: false`.

Evidence will be written under:

- `docs/validation/campaign_checkpoints/known-physics-five-baselines.json`;
- `docs/validation/campaign_reports/known-physics-five-baselines/`;
- `schemas/examples/campaign_activation_known_physics_five_completed.json`.

Do not edit the original `NOT_RUN` activation record. After inspecting the
report, commit the generated evidence and completed activation record.
