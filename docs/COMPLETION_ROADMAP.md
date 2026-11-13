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
| Phase 14L–14N reproducibility | Phase 14L full replay retained; 14M–14N stored-artifact verification added; 1,526-test isolated suite green |
| Historical integrity and portability | Versioned hash resolution created; legacy files preserved; new checkpoint paths are repository-relative |
| Theory candidate registry | Schema v1, standard-library validator and neutral unselected template; no search activated |
| Reference candidate pipeline | Circle benchmark runs from `H = p_xi^2` through spectrum and observables; parameter/vacuum/quantization/observable closure audited; 0 legacy-validator failures |
| Experimental comparison gate | Isolated dataset validator and downstream comparator implemented; current circle comparison remains blocked without parameter-free derived observables |
| Campaign readiness | Phase 7A manifest and readiness audit complete; explicit activation records preserved |
| Campaign pilot | Single- and multi-candidate infrastructure pilots complete; wide scaling held pending physical candidate, empirical gate and Mac resource measurements |

## Still required before a theory avalanche

| Area | Required completion |
| --- | --- |
| Parameter closure | Separate free, assumed, calibrated and experimentally compared quantities |
| Vacuum sector | Define the selection policy or explicitly keep it open |
| Quantum sector | Mark classical-only results and implement quantization tests where authorized |
| Observable layer | Produce dimensionful/dimensionless predictions with uncertainty and dependency traces |
| Empirical comparison | Activate only an explicitly authorized dataset against parameter-free derived observables; fitting and calibration remain forbidden |
| Campaign execution | Multi-candidate checkpoint, deduplication and failure-isolation evidence complete; Mac benchmark and physical-candidate gate remain |

## Controlled order of work

1. Decide whether one registered Phase 18E formulation can be formalized without mixing assumptions and derivations.
2. Register at least one concrete physical candidate with a closed action and explicit parameter map.
3. Produce a parameter-free derived observable and register an immutable, traceable comparison dataset.
4. Measure the multi-candidate runner on the target Mac before authorizing larger batches.
5. Expand to many candidates only after the physical/empirical gate and resource audit pass.

The current project is therefore still far from claiming a theory of all
known physics, but it is close enough to begin building the machinery that
can test such claims honestly.
