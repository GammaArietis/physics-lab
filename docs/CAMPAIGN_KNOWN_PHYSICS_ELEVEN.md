# Bounded eleven-candidate known-physics campaign

This campaign combines the eight previously validated baselines with three
free relativistic quantum-field baselines:

- free Dirac field;
- free Proca field;
- quantized free Maxwell U(1) field.

The Dirac scope is the free fermionic Fock field and its mass-shell relation.
The Proca scope is the free massive constrained vector field and its three
physical polarizations. The quantized Maxwell scope is the free Coulomb-gauge
photon field with two transverse polarizations. Interactions, charged matter,
external data and empirical comparison remain separate gates.

This is a bounded reproducibility campaign. It does not activate a search,
select or rank theories, fit parameters, use external data or perform an
empirical comparison.

## Readiness and execution

The activation record remains `NOT_RUN`. From the repository root:

    git pull --ff-only origin optimize/phase14l-14n
    source .venv/bin/activate
    export PYTHONPATH="$PWD/src"

    python tools/run_known_physics_eleven_campaign.py

Use the checked-in launcher rather than a Python heredoc. macOS uses
multiprocessing spawn, so the parent program must have a real filesystem path.

Expected result:

- `execution_status: COMPLETE`;
- all eleven candidates `PASS`;
- all records unchanged;
- all campaign controls true;
- `selection.performed: false`;
- `selection.ranking_performed: false`.

Evidence will be written under:

- `docs/validation/campaign_checkpoints/known-physics-eleven-baselines.json`;
- `docs/validation/campaign_reports/known-physics-eleven-baselines/`;
- `schemas/examples/campaign_activation_known_physics_eleven_completed.json`.

Do not edit the original `NOT_RUN` activation record. After inspecting the
report, commit the generated evidence and completed activation record.
