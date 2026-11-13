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
| Phase 14L–14N reproducibility | Phase 14L full replay retained; 14M–14N stored-artifact verification added; 1,486-test isolated suite green |

## Still required before a theory avalanche

| Area | Required completion |
| --- | --- |
| Historical integrity | Issue a new validation record for the v22/v23 hash findings |
| Portability | Replace machine-specific paths in new artifacts |
| Candidate registry | Define a schema for fields, geometry, action, constraints, parameters and provenance |
| Candidate runner | Execute one candidate through derivation, consistency and observable generation |
| Parameter closure | Separate free, assumed, calibrated and experimentally compared quantities |
| Vacuum sector | Define the selection policy or explicitly keep it open |
| Quantum sector | Mark classical-only results and implement quantization tests where authorized |
| Observable layer | Produce dimensionful/dimensionless predictions with uncertainty and dependency traces |
| Empirical comparison | Add a final, isolated data-comparison gate that cannot feed values back into derivation |

## Controlled order of work

1. Reconcile historical validation and portability without rewriting history.
2. Define and validate the candidate-theory schema.
3. Implement one complete end-to-end candidate as a reference pipeline.
4. Add batch execution only after the single-candidate pipeline is auditable.
5. Expand to many candidates and compare only derived observables with external data.

The current project is therefore still far from claiming a theory of all
known physics, but it is close enough to begin building the machinery that
can test such claims honestly.
