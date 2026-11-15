# Eichhorn--Held dimensionful physical matching

Version `eichhorn-held-physical-matching-v2`.

## What this campaign does

This campaign is the first consolidated bridge from the corrected W11
dimensionless flow to declared physical scales. Every declared combination of

1. reduced Planck scale, electroweak matching scale and a low-scale probe;
2. gravity-decoupling offset;
3. one-loop SM matter flow, a two-loop gauge control, or a two-loop
   top-dominance SM control;
4. pre-registered threshold schedule;
5. top pole and Higgs mass conversion control;

is retained. No case is ranked or promoted.

The dimensionful inputs are calibration conventions, not fitted parameters. The
threshold schedules are fractions of the electroweak scale and are deliberately
not taken from measured masses. This prevents the late comparison from leaking
into the generated trajectories.

## Precision boundary

The `two-loop-gauge-control` mode adds the known two-loop Standard Model gauge
terms in the GUT-normalized `g1` convention. The
`two-loop-sm-top-dominance` mode additionally implements the published
two-loop top-Yukawa and Higgs-quartic polynomials, with the convention map
`lambda_SM = 2 lambda_4` made explicit in code. Bottom, tau and lighter-family
two-loop terms are not silently invented.

The top conversion now transports the running mass with the QCD control and
applies the four-loop pure-QCD pole relation. The Higgs conversion remains at
tree level; a complete two-loop pole evaluation requires a self-energy and
tadpole backend such as SMDR. Below the electroweak threshold the state is
frozen rather than replaced by a full QED+QCD effective theory; those points
are diagnostic only.

Therefore the report explicitly records:

- `full_sm_two_loop = NOT_IMPLEMENTED` (top-dominance control implemented);
- `full_sm_nnlo = NOT_IMPLEMENTED`;
- `nnlo_pole_conversion_not_claimed = true`;
- `regulator_shape_uncertainty_not_claimed = true`.

This is a reproducible precision-control result, not yet a publication-grade
phenomenological prediction. The authoritative external reference for closing
the remaining Higgs pole and QED+QCD EFT gates is SMDR, whose published scope
includes two-loop heavy-particle matching and multi-loop pole masses.

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

The v1 summary remains historical. The corrected v2 summary is written to
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2_summary.json`.
The complete case archive is gzip-compressed at
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz`.

## Primary references

- A. Eichhorn and A. Held, *Top mass from asymptotic safety*, Phys. Lett. B
  777 (2018) 217--221, DOI 10.1016/j.physletb.2017.12.040.
- M. Luo and Y. Xiao, *Two-loop Renormalization Group Equations in the
  Standard Model*, Phys. Rev. Lett. 90 (2003) 011601, arXiv:hep-ph/0207271.
- D. Buttazzo et al., *Investigating the near-criticality of the Higgs boson*,
  JHEP 12 (2013) 089, DOI 10.1007/JHEP12(2013)089.
- G. Degrassi et al., *Higgs mass and vacuum stability in the Standard Model
  at NNLO*, JHEP 08 (2012) 098, DOI 10.1007/JHEP08(2012)098.
- S. P. Martin and D. G. Robertson, *Standard Model parameters in the
  tadpole-free pure MSbar scheme*, Phys. Rev. D 100 (2019) 073004,
  arXiv:1907.02500; accompanying SMDR reference implementation.
- Particle Data Group, *Review of Particle Physics 2025*, Top Quark review and
  Higgs listing. The PDG values are used only in the late comparison block.
