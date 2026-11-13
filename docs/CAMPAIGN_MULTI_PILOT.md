# Multi-candidate pilot

The multi-candidate pilot is the second execution gate after the single-
candidate reference pilot. It runs two explicit parameterized variants of the
internal circle benchmark:

- `circle-reference-internal-spectrum`
- `circle-reference-internal-spectrum-r2`

The variants are infrastructure controls, not two independent physical
theories. They exercise the same versioned runner while changing only the
explicit radius input.

The activation is recorded in
[`schemas/examples/campaign_activation_multi_candidate.json`](../schemas/examples/campaign_activation_multi_candidate.json).
The completed record is preserved separately in
[`schemas/examples/campaign_activation_multi_candidate_completed.json`](../schemas/examples/campaign_activation_multi_candidate_completed.json).

The execution completed with both candidates passing. Their records were
unchanged, checkpointing and per-candidate reports were written, and no
selection, ranking, search, finite-bound activation, external data, fitting,
or empirical comparison occurred.

This closes the multi-candidate infrastructure gate only. It does not validate
a physical theory. Both variants still have four free input parameters and no
parameter-free derived observable, so the isolated empirical gate remains
blocked until a concrete physical candidate and an immutable comparison
dataset are registered separately.

Evidence:

- [execution report](validation/campaign_reports/circle-reference-multi-pilot/campaign_report.json)
- [checkpoint](validation/campaign_checkpoints/circle-reference-multi-pilot.json)
- [pilot analysis](validation/CAMPAIGN_MULTI_PILOT_ANALYSIS_2026-11-13.json)
