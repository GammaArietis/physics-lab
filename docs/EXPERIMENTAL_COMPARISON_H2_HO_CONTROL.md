# H₂ empirical scope-control comparison

This record is the first frozen, comparison-only empirical dataset registered
after the known-physics baselines. It is deliberately not presented as a
direct validation of the ideal quantum harmonic oscillator: molecular H₂ has an
anharmonic vibrational potential, so the record tests whether the laboratory
preserves the scope boundary when real data are introduced.

## Frozen record

- Dataset: [`experimental_dataset_h2_harmonic_oscillator_control.json`](../schemas/examples/experimental_dataset_h2_harmonic_oscillator_control.json)
- Authorization: [`experimental_comparison_authorization_h2_ho_control.json`](../schemas/examples/experimental_comparison_authorization_h2_ho_control.json)
- Comparison report: [`EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json`](validation/EXPERIMENTAL_COMPARISON_H2_HO_CONTROL_2026-11-14.json)
- Dataset ID: `h2-vibrational-gap-ratio-control`
- Source extraction digest: `af7eae2fc5e1af2c4bf6e6970fc9af3bbdeb044d2db2df55762dedfd04dfaa03`

The frozen observations are the H₂ rotationless fundamental Q(0) line,
the first-overtone Q₂(0) line, and their comparison-only ratio. The ratio is
computed from the two frozen line positions before entering the comparator; no
model parameter is used.

## Result

The harmonic-oscillator prediction is `gap_ratio[2] = 2`. The frozen H₂
measurement gives `1.9434462307192757`, with the comparison engine returning
`OUTSIDE_UNCERTAINTY`. All comparison controls remain true: target-blind,
immutable, no fitting, no calibration, no parameter update and unchanged model
report.

This result is not a direct failure of the ideal oscillator baseline. It is a
scope-control outcome showing that the laboratory does not silently treat a
real anharmonic molecule as an exact harmonic oscillator. A scope-matched
ideal-oscillator dataset remains a separate scientific question.
