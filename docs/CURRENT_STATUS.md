# Current laboratory status

Status baseline: report v23, dated 26 October 2026, plus the post-v23 Phase
18E audit recorded in `docs/AUDIT_BASELINE_2026-11-13.md`.

## Executive state

| Item | Verified value |
| --- | --- |
| Latest executed search | Phase 17 TIER 1 |
| Search active | No |
| Theory selected | No |
| Dynamical action selected | No |
| Vacuum selected | No |
| Structural PFR | None verified |
| Dynamical PFR | Not tested |
| Structural parameter closure | Open |
| Dynamical parameter closure | Not tested |
| All possible physics exhausted | No |
| Current frontier | Phase 18E formalization closure audit |
| Phase 18E audit | Complete; no search or authorization activated |
| Phase 14L–14N reproducibility | Complete under the stored-artifact policy; 1,520-test isolated suite green |
| Historical integrity and portability | Closed by a versioned resolution record; 24 legacy path exceptions remain documented and immutable |
| Theory-candidate registry | Schema v1 and validator complete; neutral template registered but unselected; search not activated |
| Reference candidate pipeline | Complete internally from `H = p_xi^2` to spectrum and observables; semantic closure audit complete; 0 legacy-validator failures |
| Experimental comparison gate | Implemented downstream and target-blind; current circle comparison blocked because no parameter-free derived observable is available |
| Campaign readiness | Phase 7A complete; one-candidate pilot is `READY_FOR_PILOT` and `NOT_RUN` |

## What has been done

- Phase 16 registered 69 points across the declared tiers.
- Phase 17 TIER 1 processed 27 authorized structural grammars.
- Phase 18A catalogued 47 dynamical formulation specifications for those
  structures.
- Phase 18B produced the dynamical batch proposal.
- Phase 18C separated mathematical definition, finite search authorization,
  physical interpretation and vacuum selection.
- Phase 18D classified the missing formalization requirements by class.
- Phase 18E completed the closure audit without selecting a theory, action,
  vacuum, parameter, or numerical bound.

## What has not been established

- No complete physical theory has been selected.
- No dynamical action has been derived or authorized for search.
- No vacuum-selection principle has been found or activated.
- No numerical bounds have been introduced by the current frontier.
- The project has not demonstrated impossibility; it has exhausted only the
  registered search windows.

## Synchronization note

The v23 report is preserved as a historical snapshot and says Phase 18E was
not started. A later stored Phase 18E artifact records that the formalization
closure audit completed, while keeping all physical-selection gates closed.
The two states must not be conflated; the next report version must integrate
the later audit explicitly.

## Machine-readable snapshot

The synchronized state is also recorded in
`docs/status/STATUS_SNAPSHOT_2026-11-13_PHASE18E.json`. It is a new status
record and does not rewrite the historical v23 files.

The remaining implementation gates are tracked in
`docs/COMPLETION_ROADMAP.md`; the 14L–14N runtime diagnosis is in
`docs/PERFORMANCE_PHASE14.md`.

The 14L–14N execution gate is now closed with an explicit distinction: 14L
retains the full symbolic replay, while 14M and 14N validate committed parent
artifacts without claiming an independent replay. The result is recorded by
the `STORED_ARTIFACT` and `NOT_PERFORMED` fields in the phase outputs.

Historical hash discrepancies and machine-specific paths are resolved by
`docs/validation/HISTORICAL_INTEGRITY_PORTABILITY_2026-11-13.json`. That
record scopes the repository copy of the v23 PDF as authoritative for this
checkout, corrects the v22 cross-check without rewriting v22/v23 files, and
requires all newly generated checkpoint references to be repository-relative.

## Next controlled step

The candidate-theory schema and one complete internal reference pipeline are
now defined and validated. The benchmark's parameter, vacuum, quantum and
observable semantics are closed internally without relabelling assumptions as
derivations: its four parameters remain free inputs, its vacuum is outside
scope, and its discrete spectrum is kept distinct from field quantization.
The experimental comparison gate is also implemented, but it does not turn
the current benchmark into an empirical prediction: no parameter-free derived
observable is currently eligible for comparison, and no fitting or calibration
has been performed.
The phase-7A campaign manifest is ready for a controlled pilot, but no batch
execution or theory selection has been activated.
Before a finite dynamical search can be authorized, the three
formulations that still require an explicit theory-level choice are:

- `g17b1.riemann_cartan__constrained_action__1`;
- `g17b1.characteristic_class__local_action_functional__0`;
- `g17b1.finite_algebra__not_yet_specifiable__0`.

For any selected formulation, each missing requirement must be classified as
one of:

1. derived from the registered structure;
2. explicitly assumed;
3. a neutral mathematical definition;
4. a new physical input; or
5. undecided.

Until this schema and closure step is complete, a new batch would mix
formalization with physical selection and would not be a comparable
continuation of the record.
