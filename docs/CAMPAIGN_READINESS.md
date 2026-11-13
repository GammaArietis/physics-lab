# Phase 7A: campaign readiness and pilot manifest

Phase 7A prepares the laboratory for campaigns without executing a theory
batch. The manifest is a bounded execution contract; it does not select,
rank, fit, calibrate or compare candidates.

## Canonical files

- [`schemas/campaign_manifest.schema.json`](../schemas/campaign_manifest.schema.json): versioned manifest contract.
- [`schemas/examples/campaign_manifest_pilot.json`](../schemas/examples/campaign_manifest_pilot.json): one-candidate pilot plan.
- [`src/physics_lab/registry/campaign.py`](../src/physics_lab/registry/campaign.py): manifest validator and readiness audit.
- [`docs/validation/CAMPAIGN_READINESS_AUDIT_2026-11-13.json`](validation/CAMPAIGN_READINESS_AUDIT_2026-11-13.json): deterministic readiness evidence.

The pilot manifest currently contains only
`circle-reference-internal-spectrum`. Its execution status is `NOT_RUN`.
Readiness requires:

- portable candidate paths and valid candidate records;
- `search_status: NOT_ACTIVATED`, no finite bounds and no empirical comparison;
- no automatic selection or ranking, with human review required;
- bounded parallelism and per-candidate timeout;
- checkpointing with resume support;
- canonical deduplication and isolated failure handling.

The audit intentionally stops before execution. A later activation must be an
explicit human decision and must create execution reports without changing
the candidate records or historical artifacts.
