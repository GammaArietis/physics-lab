# Eichhorn--Held dimensionful physical matching

## What this campaign does

This campaign is the first consolidated bridge from the corrected W11
dimensionless flow to declared physical scales. Every declared combination of

1. reduced Planck scale, electroweak matching scale and a low-scale probe;
2. gravity-decoupling offset;
3. one-loop SM matter flow or a known two-loop gauge control;
4. pre-registered threshold schedule;
5. top pole and Higgs mass conversion control;

is retained. No case is ranked or promoted.

The dimensionful inputs are calibration conventions, not fitted parameters. The
threshold schedules are fractions of the electroweak scale and are deliberately
not taken from measured masses. This prevents the late comparison from leaking
into the generated trajectories.

## Precision boundary

The `two-loop-gauge-control` mode adds the known two-loop Standard Model gauge
terms in the GUT-normalized `g1` convention. The Yukawa and Higgs beta
functions remain at the W11 one-loop level. The pole conversion is one-loop
QCD for the top and tree-level for the Higgs. Below the electroweak threshold
the state is frozen rather than replaced by a full QED+QCD effective theory;
those points are diagnostic only.

Therefore the report explicitly records:

- `full_sm_two_loop = NOT_IMPLEMENTED`;
- `full_sm_nnlo = NOT_IMPLEMENTED`;
- `nnlo_pole_conversion_not_claimed = true`;
- `regulator_shape_uncertainty_not_claimed = true`.

This is a reproducible partial matching result, not yet a publication-grade
phenomenological prediction.

## Late experimental comparison

The comparison block is generated only after all cases have been integrated. It
uses PDG 2025 top and Higgs references descriptively and cannot fit, rank or
select a trajectory. Since the implemented mass relations are not NNLO, pulls
are diagnostic and must not be interpreted as a precision test.

## Reproduction

```bash
export PYTHONPATH="$PWD/src"
pytest -q tests/test_eichhorn_held_physical_matching.py
python tools/run_eichhorn_held_physical_matching.py
```

To include the full 729-point source neighborhood from the earlier target-blind
campaign:

```bash
python tools/run_eichhorn_held_physical_matching.py --include-neighborhood
```

The summary is written to
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_summary.json`.
The complete case archive is gzip-compressed at
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15.json.gz`.

## Primary references

- A. Eichhorn and A. Held, *Top mass from asymptotic safety*, Phys. Lett. B
  777 (2018) 217--221, DOI 10.1016/j.physletb.2017.12.040.
- G. Degrassi et al., *Higgs mass and vacuum stability in the Standard Model
  at NNLO*, JHEP 08 (2012) 098, DOI 10.1007/JHEP08(2012)098.
- Particle Data Group, *Review of Particle Physics 2025*, Top Quark review and
  Higgs listing. The PDG values are used only in the late comparison block.
