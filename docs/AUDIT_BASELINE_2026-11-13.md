# Baseline audit — 13 November 2026

## Verdict

The repository is a coherent research framework, not yet a test of a
completed physical theory. The current record stops before the selection of a
dynamical law, a theory, a vacuum, or numerical parameters. No empirical
claim should be promoted from the current state.

The main issues found in this audit concern state synchronization,
historical hashes, and portability. They are repairable, but they must be
resolved before treating the public repository as a reproducible scientific
record.

## Verified controls

- All 743 JSON files in the repository parse successfully.
- The Phase 18E internal partition is consistent: 47 formulations in total,
  0 complete, 34 partial, 9 unresolved, and 4 not yet specifiable.
- No formulation is marked ready for finite bounding.
- Phase 17A–17E and Phase 18A–18D sealed inputs are reported as verified by
  the Phase 18E integrity check.
- Phase 18E keeps the search, theory selection, action selection, vacuum
  selection, and numerical-bound gates closed.
- Python bytecode compilation succeeds for `src/` and `tests/`.
- The circle example passes the CLI `validate` and `audit` smoke checks.
- The focused Phase 18A–18E test set passed in the disposable dependency
  environment used during the audit. The current audit shell does not have
  `pytest` installed, so a complete local suite certification is still open.

## Findings

### A1 — Phase 18E state is not integrated into the v23 snapshot

The v23 validation record and `docs/CURRENT_STATUS.md` say:

```text
PHASE18E_STATUS = NOT_STARTED
PHASE18E_AUTHORIZATION = NOT_AUTHORIZED
```

The stored Phase 18E artifact says instead:

```text
PHASE18E_STATUS = COMPLETE
validation_status = INTERNAL_CHECKS_PASSED
search_status = NOT_STARTED
```

The timestamps place the Phase 18E artifact after the v23 report files. The
most likely explanation is that the audit was executed after v23 was written
and its result was not integrated into a new report. This is a provenance
problem, not evidence that a physical theory was completed: the same artifact
still records no selected theory, action, vacuum, parameter closure, or
dynamical PFR.

**Required action:** publish a new explicitly versioned status snapshot, or
state clearly that v23 is historical and Phase 18E is a post-v23 audit.

### A2 — v23 PDF digest is not sealed by the recorded digest

The PDF present in the repository hashes to:

```text
638993a1e6e8e217a35ac9a074d491b585a5a6a85c31c10982aeca8c38ab2b84
```

The v23 validation record and changelog record:

```text
94da0bff455883ff1f5b520547bf931dc39809c79e0b8c9d3bda88b702656ba6
```

The mismatch was already present in the supplied project. The historical PDF
has not been replaced or rewritten.

**Required action:** identify which PDF is authoritative and create a new
validation record. Do not overwrite the historical v23 validation file.

### A3 — v23 copy of the v22 digest contains a transcription error

The v22 DOCX and its own validation file agree on:

```text
7f9441709705c336d369f9944837c445e790696295df82c0be1cd70033275c1b
```

The `REPORT_V22_SHA256` value copied into the v23 validation file differs in
one character. This explains the `UNVERIFIED` v22 cross-check in the Phase 18E
artifact.

**Required action:** preserve the old record and add a corrected cross-check
in the next versioned validation record.

### A4 — Historical artifacts contain machine-specific absolute paths

Twenty-four JSON files contain paths such as `/Users/giovanni/...` or
`/tmp/...`. They do not change the mathematics, but they make the repository
non-portable and can make a future audit depend on files outside the clone.

**Required action:** replace operational paths with repository-relative paths
in new artifacts. Keep old historical files immutable and annotate their
portability limitation.

### A5 — Full-suite certification is still open because of symbolic runtime

The CI workflow installs the declared development dependencies and runs the
full pytest suite on Python 3.11 and 3.12. In this audit environment pytest is
available in an isolated environment and collects 1,483 tests. A baseline run
with the original verification logic reached the symbolic Phase 14L–14N
region without reporting a failure, but exceeded a controlled 900-second
timeout before producing a final summary. The focused Phase 18A–18E tests
passed; the historical symbolic replay remains uncertified for runtime.

An experimental cache made the suite finish, but it was rejected and removed:
it would have reused the complete audit result and weakened the independent
repeatability check. No scientific shortcut was kept in the repository.

**Required action:** let CI complete on the pushed repository, then record the
commit and CI run that produced the result. Profile Phase 14L–14N and reduce
their symbolic cost while preserving independent repeated evaluation. Tests
that materialize phase artifacts should run in a disposable checkout or be
made explicitly non-mutating.

## Scientific distance to a testable theory

The present frontier is a formalization gate, not an empirical test. The next
scientifically meaningful milestones are:

1. reconcile the post-v23 state and historical integrity records;
2. choose one registered formulation, or prove that the choice is forced;
3. define or derive one complete dynamical law with fields, domain, action or
   equivalent generator, constraints, boundary/initial data, and symmetries;
4. close the parameter and vacuum policy without importing experimental
   values into the derivation;
5. derive observables and identify at least one quantitative, falsifiable
   prediction;
6. only then compare that prediction with independent data.

The project is therefore still far from testing a theory in the strict
scientific sense. That is not a failure of the laboratory: its current
architecture is doing the valuable job of preventing an under-specified
mathematical framework from being mistaken for a physical theory.

## Audit branch policy

This report belongs to `audit/baseline-2026-11-13`. Historical v22/v23
documents and phase artifacts are not rewritten by this audit.
