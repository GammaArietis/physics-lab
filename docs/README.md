# Project documentation

This directory contains the human-readable record of the laboratory. The
executable source remains under `src/`, while immutable phase artifacts remain
inside `src/physics_lab/physics/` because the phase modules address them by
relative path.

## Start here

- [`CURRENT_STATUS.md`](CURRENT_STATUS.md): verified project state and the
  current frontier.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): package boundaries and data flow.
- [`THEORY_CANDIDATE_SCHEMA.md`](THEORY_CANDIDATE_SCHEMA.md): versioned
  candidate record, provenance gates and validation contract.
- [`INTEGRITY_AUDIT.md`](INTEGRITY_AUDIT.md): baseline cleanup checks and the
  preserved historical findings.
- [`validation/HISTORICAL_INTEGRITY_PORTABILITY_2026-11-13.json`](validation/HISTORICAL_INTEGRITY_PORTABILITY_2026-11-13.json):
  versioned resolution of hashes and portability policy.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md): rules for changing code and
  scientific records.
- [`history/`](history/): chronological reports and sealed historical
  documents.
- [`decisions/`](decisions/): open-decision documents preserved from the
  original project.

## Source of truth

The latest cumulative report is the authoritative human-readable summary of
the scientific state. Historical reports are not overwritten. Code-level
status is determined by the stored phase artifacts and their hashes, not by a
directory name or by an uncommitted note.
