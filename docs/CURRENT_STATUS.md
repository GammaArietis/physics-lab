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
| Campaign pilots | Known-physics single/multi-candidate campaigns `COMPLETE`; K4 11-candidate, K5 14-candidate and final 20-candidate campaigns archived; literature review complete with caveats; safety controls preserved |
| Alpha-geometry stage-0 pilot | `COMPLETE`; 30 finite grammar records generated, 28 canonical records retained, 2 graph-equivalence duplicates removed; no alpha target, fitting, empirical data, selection or ranking used |
| Wyler neighborhood stage-1 pilot | `COMPLETE`; exact historical anchor plus 17 pre-registered normalization stress tests; anchor error approximately 0.608 ppm against CODATA 2022; no physical candidate selected |
| Wyler W2A dimension scan | `COMPLETE`; abstract type-IV dimensions n=3..9 scanned with physical spacetime d=4 fixed; n=5 reproduces the anchor and all dimensions are retained without ranking |
| W3A Maxwell–Dirac F^4 pilot | `COMPLETE` structurally; U(1)- and Lorentz-invariant dimension-eight F^4 basis registered with birefringence and light-by-light observable channels; Wilson coefficients and EFT scale remain `UNDERDETERMINED`; no alpha fitting or empirical comparison |
| W4 one-loop QED RG pilot | `COMPLETE`; known beta function, Gaussian fixed point and bounded analytic trajectories verified; alpha is a dynamical state variable only; no interacting fixed point, alpha fit, F^4 activation or empirical comparison |
| W5 QED threshold RG campaign | `COMPLETE`; 5 normalized threshold schedules, 40 trajectories and 680 points executed with continuous matching; only Gaussian fixed point retained; no physical masses, alpha fit, ranking or F^4 activation |
| W6 coupled gauge–Yukawa/Abelian RG campaign | `COMPLETE`; literature-anchored non-Gaussian gauge–Yukawa fixed points found across 8 epsilon values, while the Abelian coordinate remains Gaussian; 24 trajectories; no alpha prediction, fitting, ranking or F^4 activation |
| W7 scalar-completed gauge–Yukawa/Abelian RG campaign | `COMPLETE`; both scalar quartic branches retained across 8 epsilon values and 48 trajectories; interacting gauge–Yukawa–scalar fixed-point structure survives, while the Abelian coordinate remains Gaussian; no alpha prediction or automatic branch selection |
| W8 Standard Model/gravity/U(1)-mixing RG campaign | `COMPLETE`; reduced one-loop SM, background-gravity Abelian control and 2x2 positive-semidefinite U(1)-mixing control executed in 31 trajectories; only Gaussian UV structure survives the stated controls; no 1/137 fit, ranking or selection |
| W9 gravity-dressed Standard Model fixed-point campaign | `IMPLEMENTED`; all three SM gauge couplings plus parametrized top-Yukawa/Higgs gravity terms scanned across 96 coefficient slices and 384 trajectories; algebraic branches retained without selection; common quantum-gravity derivation and 1/137 prediction remain open |
| W10 correlated gravity–matter single-truncation campaign | `COMPLETE`; \(f_g,f_y,f_\lambda\) derived from one published Einstein–Hilbert matter truncation across 2 gravity settings, 2 regulators and 10 regulator values: 40 slices, 114 branches and 80 trajectories; source explicitly sets Λ=0, so the nonzero-Λ closure gate remains open and no 1/137 prediction is obtained |
| W11 Eichhorn–Held full gravity–matter reproduction | `COMPLETE`; Einstein–Hilbert \(G_N,\Lambda\), all three SM gauge couplings, top/bottom Yukawas and Higgs quartic executed across 45 \((G_N,\Lambda)\) slices, 780 retained matter branches and 3 full trajectories; anchor audit corrected a \(\beta_\Lambda\) transcription error and reproduces the published anchor to displayed precision; no alpha target, ranking or selection |
| W11 target-blind UV–IR matching | `COMPLETE`; 797 UV initializations and 7,173 declared UV→IR trajectories executed: 6,901 `COMPLETE`, 204 `BOUND_REACHED`, 68 `THRESHOLD_POLE`; dimensionless states and ratios only, no masses, vev, alpha target, ranking or selection |
| Speculative-framework catalog | Registered as `CATALOG_ONLY`; string theory, loop quantum gravity, causal dynamical triangulations, asymptotic safety, noncommutative geometry and emergent gravity require explicit actions and observables before execution |
| Known-physics oscillator baseline | `COMPLETE` internally; action, canonical quantization, vacuum, exact spectrum and parameter-free gap ratio verified |
| Oscillator empirical comparison | Not authorized; no external dataset entered |
| Oscillator focused tests | 4/4 passed; campaign regression set 9/9 passed |
| Known-physics free scalar-field baseline | `COMPLETE` internally; Klein–Gordon action, field quantization, Fock vacuum, dispersion and parameter-free squared-frequency ratio verified |
| Mac M4 resource benchmark | 64 controlled variants, 4 workers, 64/64 `PASS`, 8.15 s wall time, approximately 111 MiB peak RSS; infrastructure evidence only |
| Known-physics particle-in-box baseline | `COMPLETE` internally; Dirichlet boundaries, n² spectrum, ground state and parameter-free gap ratio verified; empirical comparison not authorized |
| Known-physics hydrogen Coulomb baseline | `COMPLETE` internally; fixed-center Coulomb action, inverse-n² spectrum, explicit `(n,l,m)` states, n² degeneracy and parameter-free energy ratio verified; spin/fine structure/Lamb shift out of scope |
| Known-physics Pauli spin-half baseline | `COMPLETE` internally; Pauli matrix algebra, exact two-level spectrum, spin projections and parameter-free normalized splitting verified; orbital and relativistic sectors out of scope |
| Known-physics Maxwell vacuum baseline | `COMPLETE` internally; source-free U(1) action, gauge symmetry, field equation, Bianchi identity, two transverse polarizations and parameter-free dispersion verified; quantization out of scope |
| Known-physics Newtonian gravity baseline | `COMPLETE` internally; static field action, Poisson equation, point-source potential, attractive inverse-square acceleration and parameter-free radial ratios verified; relativity and orbital dynamics out of scope |
| Known-physics Einstein-Hilbert vacuum baseline | `COMPLETE` internally; classical Lambda=0 action, vacuum Einstein equation, Bianchi identity, Ricci-flat asymptotically flat Schwarzschild exterior and parameter-free Kretschmann-curvature ratio verified; matter, cosmology and quantum gravity out of scope |
| Known-physics free Dirac baseline | `COMPLETE` internally; free Dirac action, Clifford algebra, fermionic canonical anticommutator, Fock vacuum, particle-antiparticle sector and parameter-free mass-shell ratio verified; interactions out of scope |
| Known-physics free Proca baseline | `COMPLETE` internally; free massive-vector action, Proca equation, Lorenz constraint, three physical polarizations, Fock vacuum and parameter-free mass-shell ratio verified; interactions out of scope |
| Known-physics quantized Maxwell baseline | `COMPLETE` internally; quantized U(1) action, gauge reduction, Coulomb-gauge field quantization, photon Fock vacuum, two transverse polarizations and parameter-free dispersion verified; charges and QED interactions out of scope |
| Known-physics suite expansion | Roadmap registered; 20 executable baselines complete internally; K4, K5 and final 20-candidate campaigns archived; literature review complete with caveats; no empirical gate activated |
| Free scalar-field empirical comparison | Not authorized; no external dataset entered; absolute zero-point energy not assigned a finite value |
| Free scalar-field focused tests | 4/4 passed; pre-hydrogen full suite baseline was 1,536/1,536 |
| Hydrogen Coulomb focused tests | 6/6 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Pauli spin-half focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Maxwell vacuum focused tests | 6/6 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Newtonian gravity focused tests | 6/6 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Einstein-Hilbert vacuum focused tests | 6/6 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Free Dirac focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Free Proca focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Quantized Maxwell focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Controlled scalar phi-four baseline | `COMPLETE` internally; finite periodic classical lattice action, quartic interaction, bounded potential and interaction-strength ratio verified; continuum and renormalization out of scope |
| Controlled scalar phi-four focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Classical Yang-Mills baseline | `COMPLETE` internally; SU(2) non-Abelian field strength, gauge-covariant equation, Bianchi identity and homogeneous ansatz controls verified; quantization and non-perturbative dynamics out of scope |
| Classical Yang-Mills focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| Standard Model structural baseline | `COMPLETE` internally; gauge/matter/Higgs inventory, 12 gauge-boson count and perturbative plus Witten anomaly checks verified; couplings, masses and symmetry breaking out of scope |
| Standard Model structural focused tests | 5/5 passed in the development checkout; full-suite confirmation remains a separate regression gate |
| K6/K7 focused tests | 25/25 passed; final Mac campaign 20/20 `PASS`: finite Ising, harmonic-chain normal modes, finite ideal Bose/Fermi sectors, flat FRW background and linear scalar perturbation |
| K6/K7 scope boundary | Thermodynamic limits, material calibration, cosmological fits, perturbation vacuum selection and power spectra remain explicitly unclaimed; literature review recorded |
| H₂ empirical scope-control dataset | Corrected to allowed Q(1)/Q₂(1), same J=1; immutable and target-blind; comparison complete with `OUTSIDE_UNCERTAINTY`; not promoted to direct oscillator validation |

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

The first speculative search pilot is now complete at stage 0. It explored
only a finite grammar of simple graph geometries and graph actions, producing
structural invariants without pretending that any invariant is the
fine-structure constant. The next gate is to choose one canonical geometry
class and attach an explicit U(1) action before reading or comparing any alpha
target. The protocol and raw report are recorded in
`docs/ALPHA_GEOMETRY_SEARCH_PROTOCOL.md` and
`docs/validation/alpha_geometry_stage0_pilot_2026-11-14.json`.

The Wyler stage-1 pilot now adds a faithful historical anchor and a finite
normalization stress test. The anchor reproduces the published numerical
value, while the surrounding variants are retained as non-admissible
diagnostics unless an independent derivation supplies their factors. The
CODATA comparison is post-generation only; no nearest-value selection is
performed. The protocol and report are recorded in
`docs/WYLER_NEIGHBORHOOD_PROTOCOL.md` and
`docs/validation/wyler_neighborhood_stage1_2026-11-14.json`.

The W2A scan varies the abstract type-IV domain dimension from 3 to 9 while
keeping physical spacetime at four dimensions. It finds the n=5 historical
anchor and records the other dimensions as explicit mathematical
extrapolations. The protocol and report are recorded in
`docs/WYLER_DIMENSION_SCAN_PROTOCOL.md` and
`docs/validation/wyler_dimension_scan_2026-11-14.json`.

The W3A pilot starts from the known Maxwell–Dirac U(1) action and adds the two
parity-even dimension-eight F^4 invariants. It registers vacuum birefringence
and light-by-light scattering as observable channels, but deliberately leaves
the Wilson coefficients and EFT scale unresolved. The pilot is therefore
structurally complete but physically `UNDERDETERMINED`; no value of alpha is
used as an input or fit target. The protocol and report are recorded in
`docs/W3A_MAXWELL_DIRAC_F4_PILOT.md` and
`docs/validation/maxwell_dirac_f4_pilot_2026-11-14.json`.

The W4 pilot then moves from static operator geometry to a controlled dynamic
flow. It reproduces the one-loop QED beta function, records the Gaussian fixed
point and integrates three bounded mathematical trajectories while rejecting
Landau-pole crossings. It does not derive the low-energy value of alpha, claim
an interacting fixed point or activate the unresolved W3A operators. The
protocol and report are recorded in `docs/W4_QED_RG_PILOT.md` and
`docs/validation/qed_rg_pilot_2026-11-15.json`.

The W5 campaign extends W4 to five normalized piecewise-threshold schedules,
eight initial alpha seeds and seventeen scale offsets: 40 trajectories and
680 points in total. It verifies continuous matching and records the changed
slope when the active fermion count increases. Since every regime retains a
positive one-loop QED beta function, no non-zero fixed point appears. The
schedules are mathematical controls, not physical particle-mass inputs. The
protocol and report are recorded in `docs/W5_QED_THRESHOLD_RG_CAMPAIGN.md` and
`docs/validation/qed_threshold_rg_campaign_2026-11-15.json`.

W6 then activates a literature-anchored coupled gauge–Yukawa system from
Litim–Sannino and adds the one-loop Abelian coupling as a decoupled spectator.
Across eight positive epsilon values it finds the expected non-Gaussian
gauge–Yukawa fixed point, but the electromagnetic coordinate remains
alpha_em*=0 because its beta function stays positive and uncoupled at this
order. This is a mechanism demonstration, not a derivation of 1/137. The
protocol, bibliography and report are recorded in
`docs/W6_COUPLED_GAUGE_YUKAWA_EM_RG.md` and
`docs/validation/gauge_yukawa_em_rg_campaign_2026-11-15.json`.

W7 closes the scalar quartic sector at the mixed order used in the original
model analysis. Both scalar branches are retained with their stability
matrices, and the interacting gauge–Yukawa–scalar structure persists across
the scan. The Abelian coordinate remains alpha_em*=0, so scalar completion
still does not derive 1/137. Higher-loop comparison and gravity/matter beta
functions remain separate gates. The protocol and report are recorded in
`docs/W7_COUPLED_GAUGE_YUKAWA_SCALAR_EM_RG.md` and
`docs/validation/gauge_yukawa_scalar_em_rg_campaign_2026-11-15.json`.

W8 now executes one broad campaign over three distinct controls: a reduced
one-loop Standard Model \((g_1,g_2,g_3,y_t,\lambda)\) system, a
literature-shaped background-gravity deformation of the Abelian beta function,
and a charge-agnostic positive-semidefinite two-U(1) mixing control. The
reduced Standard Model has only its Gaussian real perturbative fixed point in
this truncation. The gravity ansatz records a nonzero algebraic root for
positive background coefficient, but that root is UV-repulsive while the
Gaussian point is UV-attractive. The positive mixing controls likewise retain
only the Gaussian point in the nonnegative quadrant. These results are
controls, not a full quantum-gravity or multi-U(1) prediction, and they still
do not derive 1/137. The report, equations, caveats and bibliography are
recorded in `docs/W8_SM_GRAVITY_MIXING_RG.md` and
`docs/validation/sm_gravity_mixing_rg_campaign_2026-11-15.json`.

W9 expands the gravity control to all three Standard Model gauge couplings and
adds independently scanned linear controls for the top Yukawa and Higgs
quartic. The gauge term is literature-shaped, while the matter coefficients
are explicitly marked as minimal closure ansatzes rather than a common
quantum-gravity derivation. The campaign retains every algebraic branch,
records residuals and stability eigenvalues, and executes 96 coefficient
slices with 384 trajectories. It does not derive 1/137. The protocol and
report are recorded in `docs/W9_GRAVITY_DRESSED_SM_FIXED_POINT_RG.md` and
`docs/validation/gravity_sm_fixed_point_rg_campaign_2026-11-15.json`.

W10 removes the independent-coefficient gap in W9 for the published
Einstein–Hilbert matter truncation of de Brito and Eichhorn. The three
coefficients \(f_g,f_y,f_\lambda\) are evaluated from the same threshold
integrals and the same Newton fixed point, with standard and unimodular
gravity plus Litim and exponential regulator controls. The run contains 40
correlated slices, 114 retained branches and 80 target-blind trajectories.
The source truncation explicitly omits the cosmological constant, so W10
records the requested nonzero-Λ extension as an open closure gate rather than
adding an arbitrary term. It does not derive 1/137. The protocol and report
are recorded in `docs/W10_GRAVITY_MATTER_SINGLE_TRUNCATION_RG.md` and
`docs/validation/gravity_matter_single_truncation_rg_campaign_2026-11-15.json`.

W11 reproduces the explicit Eichhorn–Held Einstein–Hilbert plus Standard Model
truncation with nonzero \(\Lambda\), \(g_1,g_2,g_3\), \(y_t,y_b\) and
\(\lambda_4\). The broad target-blind run contains 45 gravity slices, 780
retained matter fixed-point branches and 3 complete eight-dimensional
trajectories. The anchor audit found and corrected a laboratory transcription
error in the \(\beta_\Lambda\) bracket: the exact root
\((3.2945094357,-4.5139868308)\) rounds to the paper's \((3.29,-4.51)\).
No field count or coefficient was adjusted. The source mass claims are not
used as targets and no value of 1/137 is derived. The equations, correction
and report are recorded in
`docs/EICHHORN_HELD_ASYMPTOTIC_SAFETY.md` and
`docs/validation/eichhorn_held_asymptotic_safety_campaign_2026-11-15.json`.
The complete version/count audit is in
`docs/EICHHORN_HELD_ANCHOR_AUDIT.md` and
`docs/validation/eichhorn_held_anchor_audit_2026-11-15.json`.

The target-blind UV-to-IR flow atlas is recorded in
`docs/EICHHORN_HELD_IR_MATCHING.md` and
`docs/validation/eichhorn_held_ir_matching_campaign_2026-11-15_summary.json`,
with the compressed full case archive in
`docs/validation/eichhorn_held_ir_matching_campaign_2026-11-15.json.gz`. It
connects the corrected UV truncation to a declared matter-only IR window, but
does not claim physical Standard Model mass matching: the electroweak vev,
dimensionful inputs, pole-mass conversion and higher-loop threshold matching
remain outside scope.

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
corrected frozen target-blind H₂ scope-control dataset using the allowed
same-J=1 Q(1)/Q₂(1) pair. Its outside-uncertainty result is not a direct claim
against the ideal oscillator because molecular anharmonicity is outside that
baseline. The Mac M4 resource benchmark, the first real two-candidate campaign,
the particle-in-a-box baseline, the internal hydrogen Coulomb runner, the
internal Pauli spin-half runner, the internal Maxwell vacuum runner and the
internal Newtonian gravity runner are now complete. The Einstein-Hilbert
vacuum runner now closes K3 with the classical Lambda=0 Ricci-flat
Schwarzschild exterior and a normalized Kretschmann-curvature observable. The
free Dirac, free Proca and quantized Maxwell runners now close K4 with their
respective free-field quantization controls. K5 now adds three deliberately
bounded baselines: a finite classical scalar phi-four lattice, classical
SU(2) Yang-Mills, and a structural Standard Model/anomaly record. These are
not claims of quantum phi-four renormalization, quantum Yang-Mills existence,
confinement, fitted Standard Model parameters or precision agreement. The
K4's eleven-candidate campaign and K5's fourteen-candidate campaign are now
complete and archived with their checkpoints and per-candidate reports. K6
and K7 now add six finite, explicitly bounded baselines with 25 focused tests
passing in the development checkout. The final twenty-candidate campaign,
containing the 14 archived K1-K5 records and the 6 K6-K7 records, is now
complete on the Mac with 20/20 `PASS` and is archived with checkpoint and
per-candidate reports. A literature-backed review is recorded in
`docs/validation/HUMAN_REVIEW_FINAL_TWENTY_2026-11-14.md` and accepts all
baselines within their declared scopes, with explicit caveats for finite
lattice reductions and cosmological truncations. Empirical comparison,
fitting, selection and ranking remain separate closed gates.
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


## W12 dimensionful physical matching — 2026-11-15

The corrected v2 physical-matching campaign is recorded as
`CONTROLLED_MATCHING_COMPLETE`: 797 UV initializations, 3 gravity transitions,
3 loop controls and 4 threshold schedules produced 28,692 configurations,
27,060 complete, 1,452 bound-reached and 180 numerical-failure cases. The
lambda convention map `lambda_SM = 2 lambda_4` is explicit, the two-loop
top-dominance control and four-loop pure-QCD top pole control are implemented,
and no comparison was used for fitting, ranking or selection. Full SM NNLO
threshold/Higgs-pole matching remains an explicit external SMDR backend gate;
no phenomenological claim is made before that gate is connected. The v2
closeout is in `docs/PHYSICAL_MATCHING_CLOSEOUT_2026-11-15.md` and the
machine-readable summary is in
`docs/validation/eichhorn_held_physical_matching_campaign_2026-11-15_v2_summary.json`.
