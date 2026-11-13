# Integrity audit of the reorganized tree

Audit performed during the repository cleanup on 13 November 2026. The
original ZIP was not modified. Historical source files were copied byte for
byte unless a code path had to be updated because `diario/` was renamed to
`docs/history/`.

## Report v23

| Record | SHA-256 observed | SHA-256 recorded | Result |
| --- | --- | --- | --- |
| v23 DOCX | `cd587b4fd90259f264392ccfb1bcdbb013a4c38076bf401f646a07e8b92cc5b0` | same | Verified |
| v23 PDF | `638993a1e6e8e217a35ac9a074d491b585a5a6a85c31c10982aeca8c38ab2b84` | `94da0bff455883ff1f5b520547bf931dc39809c79e0b8c9d3bda88b702656ba6` | Mismatch |
| v23 validation JSON | identical to supplied file | n/a | Preserved |

The mismatch is present in the supplied project and is not caused by the
reorganization. It means the v23 PDF cannot currently be treated as sealed by
the hash in `REPORT_V23_VALIDATION.json`. The historical files remain
unchanged so that the discrepancy can be investigated and resolved without
destroying provenance.

## Repository cleanup

- macOS metadata, virtual environments, bytecode and test caches were removed
  from the Git candidate tree.
- Phase artifacts were retained in their original package locations because
  the phase code addresses them by relative path and verifies their hashes.
- Historical reports were moved from `diario/` to `docs/history/`; the small
  number of executable references and tests were updated accordingly.
- The focused Phase 18A-18E test set passes after the move.

## Publication gate

Before the first public release, decide whether to:

1. preserve the mismatch as a historical integrity finding; or
2. produce a new, explicitly versioned validation record after confirming
   which PDF is authoritative.

The second option must not overwrite the v23 record.

## Point 2 resolution

The publication gate is resolved by the versioned record
`docs/validation/HISTORICAL_INTEGRITY_PORTABILITY_2026-11-13.json`.
It preserves the v22/v23 files, scopes the PDF authority to the repository
copy present in this snapshot, records the corrected v22 digest, and declares
the 24 legacy JSON files with absolute paths as immutable historical
exceptions. New checkpoint references are generated as repository-relative
POSIX paths by `src/physics_lab/physics/portability.py`.
