# Phase 7 pilot: execution and analysis

The explicitly authorized pilot ran one candidate:
`circle-reference-internal-spectrum`.

## Evidence

- Activation record:
  [`schemas/examples/campaign_activation_pilot_completed.json`](../schemas/examples/campaign_activation_pilot_completed.json)
- Campaign report:
  [`docs/validation/campaign_reports/circle-reference-pilot/campaign_report.json`](validation/campaign_reports/circle-reference-pilot/campaign_report.json)
- Checkpoint:
  [`docs/validation/campaign_checkpoints/circle-reference-pilot.json`](validation/campaign_checkpoints/circle-reference-pilot.json)
- Analysis:
  [`docs/validation/CAMPAIGN_PILOT_ANALYSIS_2026-11-13.json`](validation/CAMPAIGN_PILOT_ANALYSIS_2026-11-13.json)

The pilot passed the infrastructure contract: the action-to-observables
pipeline completed, the candidate record remained unchanged, and all isolation
controls passed. No theory was selected or ranked, and no search, finite bound,
external datum, fitting or calibration was activated.

The result is therefore `PILOT_PASS_INFRASTRUCTURE_ONLY`, not a physical
confirmation. The campaign is held before scaling because one candidate does
not exercise multi-candidate deduplication, failure isolation under load, or
the memory profile of the target machine.
