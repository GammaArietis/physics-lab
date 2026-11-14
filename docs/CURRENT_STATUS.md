# Current laboratory status

Status baseline: report v23, dated 26 October 2026, plus the post-v23 Phase
18E audit and the known-physics baselines recorded on 13–14 November 2026.

## Executive state

| Item | Verified value |
| --- | --- |
| Latest executed search | Phase 17 TIER 1; no new search activated |
| Search active | No |
| Theory selected | No |
| Dynamical action selected | No |
| Vacuum selected | No |
| Structural PFR | None verified |
| Dynamical PFR | Not tested |
| Structural parameter closure | Open |
| Dynamical parameter closure | Not tested |
| All possible physics exhausted | No |
| Current frontier | Review of known-physics baselines and separate empirical gate |
| Phase 18E audit | Complete; no search or authorization activated |
| Phase 14L–14N reproducibility | Historical stored-artifact policy preserved; current checkout passes 1,536/1,536 tests with per-test artifact isolation |
| Historical integrity and portability | Closed by a versioned resolution record; 24 legacy path exceptions remain documented and immutable |
| Theory-candidate registry | Schema v1 and validator complete; neutral template registered but unselected; search not activated |
| Reference candidate pipeline | Complete internally from `H = p_xi^2` to spectrum and observables; semantic closure audit complete; 0 legacy-validator failures |
| Experimental comparison gate | Implemented downstream and target-blind; first frozen H₂ scope-control comparison complete, direct scope-matched validation remains open |
| Campaign readiness | Phase 7A complete; original one-candidate readiness manifest preserved |
| Campaign pilot | Single and multi-candidate pilots `COMPLETE`; infrastructure pass only; wide campaign held pending physical/empirical and Mac resource gates |
| Known-physics oscillator baseline | `COMPLETE` internally; action, canonical quantization, vacuum, exact spectrum and parameter-free gap ratio verified |
| Oscillator empirical comparison | Not authorized; no external dataset entered |
| Oscillator focused tests | 4/4 passed; campaign regression set 9/9 passed |
| Known-physics free scalar-field baseline | `COMPLETE` internally; Klein–Gordon action, field quantization, Fock vacuum, dispersion and parameter-free squared-frequency ratio verified |
| Free scalar-field empirical comparison | Not authorized; no external dataset entered; absolute zero-point energy not assigned a finite value |
| Free scalar-field focused tests | 4/4 passed; current full suite passes 1,536/1,536 |
| H₂ empirical scope-control dataset | Registered immutable and target-blind; comparison complete with `OUTSIDE_UNCERTAINTY`; not promoted to direct oscillator validation |

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

The candidate-theory schema and complete internal reference pipelines are now
defined and validated. The circle benchmark remains an internal structural
reference. The quantum harmonic oscillator is the first concrete known-physics
candidate whose action, canonical quantization, vacuum, exact spectrum and
parameter-free gap-ratio observable close in one executable chain. Its mass,
frequency and `hbar` inputs remain explicit; no empirical value has entered the
model, and no fitting or calibration has been performed.

The oscillator and free-scalar campaigns were each explicitly activated for
one candidate and completed with unchanged records. No theory selection or
ranking occurred. The free-scalar field quantization, Fock vacuum, periodic
mode spectrum and parameter-free ratio are verified only within the declared
1+1-dimensional baseline; the absolute zero-point sum is deliberately not
assigned a finite value. The empirical gate has now been exercised with a
frozen target-blind H₂ scope-control dataset. Its outside-uncertainty result
is not a direct claim against the ideal oscillator because molecular
anharmonicity is outside that baseline. The next controlled step is the Mac
resource benchmark; a scope-matched direct validation dataset remains open.
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
