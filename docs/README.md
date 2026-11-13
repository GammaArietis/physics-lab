# Project documentation

This directory contains the human-readable record of the laboratory. The
executable source remains under `src/`, while immutable phase artifacts remain
inside `src/physics_lab/physics/` because the phase modules address them by
relative path.

## Start here

- [`CURRENT_STATUS.md`](CURRENT_STATUS.md): verified project state and the
  current frontier.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): package boundaries and data flow.
- [`INTEGRITY_AUDIT.md`](INTEGRITY_AUDIT.md): cleanup checks and the unresolved
  v23 PDF hash discrepancy.
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
