# H₂ empirical scope-control comparison

This record is the corrected first frozen, comparison-only empirical dataset
registered after the known-physics baselines. It is deliberately not presented
as a direct validation of the ideal quantum harmonic oscillator: molecular H₂
has an anharmonic vibrational potential, so the record tests whether the
laboratory preserves the scope boundary when real data are introduced.

## Frozen record

- Dataset: [`experimental_dataset_h2_harmonic_oscillator_control.json`](../schemas/examples/experimental_dataset_h2_harmonic_oscillator_control.json)
- Authorization: [`experimental_comparison_authorization_h2_ho_control.json`](../schemas/examples/experimental_comparison_authorization_h2_ho_control.json)
- Comparison report: [`EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json`](validation/EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json)
- Dataset ID: `h2-vibrational-gap-ratio-control`
- Dataset version: `corrected-allowed-j1-2026-11-14`
- Source extraction digest: `4f43423eba9d2b0d3a70e7a833a66494ff051ca86ff90b7447e1b7e638854693`

The corrected frozen observations are the allowed H₂ fundamental Q(1) line,
the allowed first-overtone Q₂(1) line, and their comparison-only ratio. Both
lines use the same ground-state rotational quantum number J=1. The previous
Q₂(0) entry was withdrawn because the relevant symmetry selection rule makes
that transition forbidden; the cited source gives only a reference position,
not a clean direct measurement. The ratio is computed from the two frozen line
positions before entering the comparator; no model parameter is used.

## Result

The harmonic-oscillator prediction is `gap_ratio[2] = 2`. The corrected frozen
H₂ measurement gives `1.943396817619332`, with the comparison engine returning
`OUTSIDE_UNCERTAINTY`. All comparison controls remain true: target-blind,
immutable, no fitting, no calibration, no parameter update and unchanged model
report.

This result is not a direct failure of the ideal oscillator baseline. It is a
scope-control outcome showing that the laboratory does not silently treat a
real anharmonic molecule as an exact harmonic oscillator. A scope-matched
ideal-oscillator dataset remains a separate scientific question.
