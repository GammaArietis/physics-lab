# Laboratory completion roadmap

The laboratory is not one unfinished calculation. It is a stack of gates,
and the gates must close in order before a large theory campaign is useful.

## Already present

| Area | State |
| --- | --- |
| Core models, provenance, reports and CLI | Implemented and smoke-tested |
| Circle and C3 examples | Implemented; intentionally incomplete as physical theories |
| Structural phase history through Phase 17 TIER 1 | Preserved and internally sealed where checked |
| Dynamical catalogues 18A–18D | Implemented and audited |
| Phase 18E closure audit | Complete as an audit; no theory selected |
| Phase 14L–14N reproducibility | Phase 14L full replay retained; 14M–14N stored-artifact verification added; current checkout passes 1,536/1,536 tests with per-test artifact isolation |
| Historical integrity and portability | Versioned hash resolution created; legacy files preserved; new checkpoint paths are repository-relative |
| Theory candidate registry | Schema v1, standard-library validator and neutral unselected template; no search activated |
| Reference candidate pipeline | Circle benchmark runs from `H = p_xi^2` through spectrum and observables; parameter/vacuum/quantization/observable closure audited; 0 legacy-validator failures |
| Experimental comparison gate | Isolated dataset validator and downstream comparator implemented; current circle comparison remains blocked without parameter-free derived observables |
| Campaign readiness | Phase 7A manifest and readiness audit complete; explicit activation records preserved |
| Campaign pilot | Single- and multi-candidate infrastructure pilots complete; wide scaling held pending physical candidate, empirical gate and Mac resource measurements |
| Known-physics harmonic oscillator | Complete internal action-to-observable baseline; no empirical comparison authorized |
| Known-physics free scalar field | Complete internal action-to-Fock-observable baseline; no empirical comparison authorized |

## Still required before a theory avalanche

| Area | Required completion |
| --- | --- |
| Parameter closure | Separate free, assumed, calibrated and experimentally compared quantities |
| Vacuum sector | Define the selection policy or explicitly keep it open |
| Quantum sector | Mark classical-only results and implement quantization tests where authorized |
| Observable layer | Produce dimensionful/dimensionless predictions with uncertainty and dependency traces |
| Empirical comparison | Activate only an explicitly authorized dataset against parameter-free derived observables; fitting and calibration remain forbidden |
| Campaign execution | Multi-candidate checkpoint, deduplication and failure-isolation evidence complete; Mac benchmark and physical-candidate gate remain |
| Separate empirical gate | First immutable target-blind H₂ scope-control dataset registered and compared; scope-matched direct validation remains open; fitting and calibration remain forbidden |

## Controlled order of work

1. Review the completed oscillator and free-scalar baselines without conflating their quantum-mechanical and field-theoretic scopes.
2. Register a parameter-free derived observable and an immutable, traceable comparison dataset for a separate target-blind comparison gate; the first H₂ scope-control record is complete, while direct scope-matched validation remains open.
3. Measure the multi-candidate runner on the target Mac before authorizing larger batches.
4. Decide whether one registered Phase 18E formulation can be formalized without mixing assumptions and derivations.
5. Expand to many candidates only after the physical/empirical gate and resource audit pass.

The current project is therefore still far from claiming a theory of all
known physics. It now has two complete internal known-physics baselines, but
neither has been compared with external data. Speculative theories remain
deferred until the separate empirical gate and the Mac resource audit are
closed.
