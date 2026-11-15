# Eichhorn--Held target-blind UV-to-IR matching

## Objective

W11 now reproduces the corrected Eichhorn--Held Einstein--Hilbert plus
Standard Model truncation. This campaign closes the next mathematical gate:
evolve the dimensionless UV system toward lower logarithmic scales, explicitly
decouple gravity at a declared transition, and continue the matter flow in the
IR.

This is deliberately target-blind. It does not use the electroweak vacuum
expectation value, measured masses, pole-mass corrections, the fine-structure
constant, or an external dataset.

## Definition of the matching control

For each initialization, the laboratory integrates

1. the full corrected W11 beta system from log-scale offset 0 to a negative
   gravity-transition offset;
2. the same dimensionless matter state with (G_N=\Lambda=0) below that
   transition;
3. the matter-only one-loop flow to a more negative IR endpoint.

The transition and endpoint are logarithmic control parameters, not physical
mass scales. The default grid contains three transition offsets
\((-2,-4,-6)\), three IR endpoints \((-8,-16,-32)\), and all nine valid
combinations.

The UV initialization set contains:

- both the published rounded gravity anchor and the exact root of the
  corrected printed gravitational equations;
- every real matter fixed point found by the deterministic W11 branch
  enumerator for both gravity backgrounds;
- 729 pre-registered perturbations around the source UV reference
  \((g_i,y_t,y_b,\lambda_4)=(0,0.36,0,0.01)\).

No branch is ranked or promoted.

## Archived run

The complete run contains 797 initializations and 7,173 UV-to-IR
trajectories:

| Outcome | Count |
|---|---:|
| `COMPLETE` | 6,901 |
| `BOUND_REACHED` | 204 |
| `THRESHOLD_POLE` | 68 |

The 6,561 source-neighborhood trajectories all complete. The failures are
isolated in the enumerated matter-fixed-point branches and are retained as
negative results. Among complete trajectories, 6,741 have non-negative
quartic coupling at the recorded endpoint and 6,478 develop a nonzero gauge
norm under the perturbation grid. These are internal structural counts, not
phenomenological selections.

Each case records its initial state, transition state when available, final
state, dimensionless ratios, status and error. The report does not store every
Runge--Kutta substep; the integrator itself remains directly reproducible.

## Interpretation and boundary

The campaign demonstrates a reproducible target-blind dimensionless UV-to-IR
flow atlas. It does **not** yet constitute physical Standard Model matching or
a mass prediction. Eichhorn and Held explicitly state that the electroweak
scale is an input in their calculation and that precision requires matching at
the Planck scale to higher-order SM running. Their paper also reports strong
truncation/regulator sensitivity in the gravitational fixed point.

Therefore the next gate is not to compare the generated ratios with measured
masses. It is to specify, independently and explicitly, the missing matching
layer: relevant dimensionful inputs, threshold prescriptions, anomalous
dimensions, loop order and scheme. Until then the results remain correctly
classified as `TARGET_BLIND_FLOW`, with `physical_sm_mass_matching_completed`
set to false.

## Reproduction

```bash
export PYTHONPATH="$PWD/src"
pytest -q tests/test_eichhorn_held_ir_matching.py
python tools/run_eichhorn_held_ir_matching.py
```

Machine-readable summary:
`docs/validation/eichhorn_held_ir_matching_campaign_2026-11-15_summary.json`.

Compressed full case archive:
`docs/validation/eichhorn_held_ir_matching_campaign_2026-11-15.json.gz`.
The uncompressed JSON is regenerated locally by the reproduction command.

## Primary bibliography

- A. Eichhorn and A. Held, *Top mass from asymptotic safety*, Phys. Lett. B
  777, 217--221 (2018), DOI
  [10.1016/j.physletb.2017.12.040](https://doi.org/10.1016/j.physletb.2017.12.040).
- G. Degrassi et al., *Higgs mass and vacuum stability in the Standard Model
  at NNLO*, JHEP 08 (2012) 098, DOI
  [10.1007/JHEP08(2012)098](https://doi.org/10.1007/JHEP08(2012)098).
