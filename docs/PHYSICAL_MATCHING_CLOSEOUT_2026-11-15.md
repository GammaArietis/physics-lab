# Physical matching closeout — 2026-11-15

## Executive result

The corrected v2 campaign closes the laboratory's reproducible dimensionful
matching control. It does not claim a complete NNLO phenomenological
prediction, because the final electroweak/Higgs pole and low-energy EFT layer
requires the full self-energy, tadpole and decoupling backend described by
Martin and Robertson's SMDR implementation.

The complete v2 grid contains:

- 797 UV initializations from the previously archived target-blind atlas;
- 3 gravity-decoupling offsets;
- 3 loop controls;
- 4 pre-registered threshold schedules;
- 28,692 total configurations;
- 27,060 `COMPLETE` cases;
- 1,452 `BOUND_REACHED` cases;
- 180 `NUMERICAL_FAILURE` cases, all retained.

No trajectory was fitted, ranked or selected.

## What is now implemented

1. Dimensionful scales: reduced Planck scale, electroweak matching scale and
   low-energy probe scale are explicit.
2. Gravity decoupling: all three declared logarithmic transition offsets are
   executed.
3. SM running: one-loop W11 matter, two-loop gauge, and two-loop
   top-dominance controls are executed. The latter includes the published
   top-Yukawa and Higgs-quartic polynomials and maps the published convention
   with `lambda_SM = 2 lambda_4`.
4. Running-to-pole: the top uses a four-loop pure-QCD conversion control and
   transport to the running top scale. The Higgs tree-level relation is now
   normalized consistently with `lambda_4`.
5. Uncertainty propagation: loop, threshold and gravity-transition variants
   are retained case by case; no envelope is used to select a preferred case.
6. Late comparison: PDG top/Higgs values enter only after trajectory
   generation and are descriptive only.

## Physical reading of the run

The maximum top-pole control output is about 101.5 GeV, while the Higgs
tree-level control spans values up to about 175.0 GeV. Some Higgs cases pass
through the observed region, but this is not evidence for a prediction because
the Higgs pole correction is not implemented and no case was selected.

The maximum generated electromagnetic coupling at the electroweak evaluation
scale is about `1.44e-4`, so this truncation and initialization ensemble does
not derive the electromagnetic coupling near `1/137`.

## Remaining authoritative gate

The only remaining precision gate is not another arbitrary coefficient scan:

```text
SMDR_REQUIRED_FOR_FULL_EFT_AND_HIGGS_POLE_MATCHING
```

SMDR is the primary reference implementation for two-loop heavy-particle
decoupling, the Higgs pole mass, the top pole mass with electroweak effects,
and the low-energy QCD+QED effective theory. Until that backend is compiled
and its interface is connected to the target-blind UV output, the honest status
is `CONTROLLED_MATCHING_COMPLETE`, not `FULL_NNLO_PHENOMENOLOGY_COMPLETE`.

## Reproduction

```bash
export PYTHONPATH="$PWD/src"
pytest -q tests/test_eichhorn_held_physical_matching.py
python tools/run_eichhorn_held_physical_matching.py \
  --include-neighborhood \
  --steps-per-unit 4
```

The v2 summary is
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2_summary.json`.
The full case archive is regenerated locally as
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2.json.gz`.

## Primary references

- Eichhorn and Held, *Top mass from asymptotic safety*, Phys. Lett. B 777
  (2018), DOI [10.1016/j.physletb.2017.12.040](https://doi.org/10.1016/j.physletb.2017.12.040).
- Luo and Xiao, *Two-loop Renormalization Group Equations in the Standard
  Model*, Phys. Rev. Lett. 90 (2003) 011601,
  DOI [10.1103/PhysRevLett.90.011601](https://doi.org/10.1103/PhysRevLett.90.011601).
- Buttazzo et al., *Investigating the near-criticality of the Higgs boson*,
  JHEP 12 (2013) 089,
  DOI [10.1007/JHEP12(2013)089](https://doi.org/10.1007/JHEP12(2013)089).
- Martin and Robertson, *Standard Model parameters in the tadpole-free pure
  MSbar scheme*, Phys. Rev. D 100 (2019) 073004,
  [arXiv:1907.02500](https://arxiv.org/abs/1907.02500), and the official
  [SMDR implementation](https://github.com/davidgrobertson/SMDR).
- Particle Data Group, [2025 Top Quark review](https://pdg.lbl.gov/2025/reviews/rpp2025-rev-top-quark.pdf)
  and [Higgs listing](https://pdg.lbl.gov/2025/web/viewer.html?file=..%2Flistings%2Frpp2025-list-higgs-boson.pdf).
