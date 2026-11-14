# Bounded three-candidate known-physics campaign

This campaign combines the three validated executable baselines:

- quantum harmonic oscillator;
- free real scalar field;
- quantum particle in a one-dimensional box.

It is a bounded reproducibility campaign. It does not activate a search,
select or rank theories, fit parameters, use external data or perform an
empirical comparison.

## Run on the Mac

From the repository root:

    git pull --ff-only origin optimize/phase14l-14n
    source .venv/bin/activate
    export PYTHONPATH="$PWD/src"

    python tools/run_known_physics_three_campaign.py

Use the checked-in launcher rather than a Python heredoc. macOS uses
multiprocessing spawn, so the parent program must have a real filesystem path.

Expected result:

- execution_status: COMPLETE;
- all three candidates PASS;
- all records unchanged;
- all campaign controls true;
- selection.performed: false;
- selection.ranking_performed: false.

Evidence is written under:

- docs/validation/campaign_checkpoints/known-physics-three-baselines.json;
- docs/validation/campaign_reports/known-physics-three-baselines/;
- schemas/examples/campaign_activation_known_physics_three_completed.json.

Do not edit the original NOT_RUN activation record. After inspecting the
report, commit the generated evidence and completed activation record.
