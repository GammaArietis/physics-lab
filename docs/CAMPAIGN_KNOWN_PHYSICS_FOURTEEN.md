# Fourteen-candidate known-physics campaign

Status: executed and archived, 14 November 2026.

## Purpose

This is the next bounded execution campaign after the internal K5 checks. It
combines the eleven previously registered K1--K4 baselines with three K5
baselines:

- a finite periodic classical scalar phi-four lattice;
- classical SU(2) Yang-Mills with an explicit homogeneous ansatz;
- the structural Standard Model gauge, matter, Higgs and anomaly record.

The three K5 entries are deliberately narrower than the names might suggest.
They do not claim quantum phi-four renormalization, a quantum Yang-Mills
existence result, confinement, fitted Standard Model couplings or masses,
symmetry-breaking dynamics, precision agreement or empirical validation.

## Controls

- 14 registered candidate records;
- 8 isolated workers, suitable for the MacBook Air M4 benchmark envelope;
- 120 seconds per candidate;
- deterministic seed `0`;
- canonical-record deduplication;
- failure isolation and checkpoint/report writing;
- no automatic selection or ranking;
- no search, finite bounds, external data, fitting or empirical comparison.

The machine-readable manifest is
`schemas/examples/campaign_manifest_known_physics_fourteen.json` and the
explicit activation record is
`schemas/examples/campaign_activation_known_physics_fourteen.json`.

## Reproducible command

From the repository root:

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD/src"
python tools/run_known_physics_fourteen_campaign.py
```

The command writes a completed activation, a checkpoint and one report per
candidate under `docs/validation/`. Results must be reviewed before any larger
campaign is authorized. The campaign is an execution/validation record, not a
physics ranking.

## Archived result

The recorded run completed with 14/14 candidates in `PASS` and
`execution_status: COMPLETE`. Candidate records were unchanged; deduplication,
worker isolation, failure isolation and checkpoint writing were active. Search,
finite bounds, external data, empirical comparison, fitting, selection and
ranking remained closed. Human review is still required before defining or
activating K6.
