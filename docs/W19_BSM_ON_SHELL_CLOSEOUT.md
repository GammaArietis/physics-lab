# W19 — one-loop BSM on-shell pole-sector closure

## Result

W19 closes the one-loop on-shell renormalization conditions for every
successful W17 projection of the registered model

\[
SU(3)_c\times SU(2)_L\times U(1)_Y + S + \Psi_{VL},
\qquad
V\supset \lambda_{HS}S^2H^\dagger H,
\qquad
\mathcal L_Y\supset-y_S S\bar\Psi\Psi.
\]

The implementation is a mixed OS/\(\overline{MS}\) scheme, which is the
minimal closed scheme for pole observables:

| Sector | Renormalization condition |
|---|---|
| Higgs tadpole | renormalized tadpole set to zero |
| Higgs mass and residue | on-shell pole and unit residue |
| W and Z | on-shell masses and residues |
| Photon | Thomson-limit charge and residue |
| Z–photon | both off-diagonal on-shell mixing conditions |
| Singlet S | on-shell mass and residue |
| Vector-like Dirac fermions | on-shell mass and residue |
| Gauge, Yukawa and scalar couplings | \(\overline{MS}\) at \(\mu=91.1876\) GeV |

Keeping the couplings in \(\overline{MS}\) is explicit, not an omission: a
pure on-shell definition of every coupling would require a complete set of
one-loop three-point amplitudes and corresponding finite vertex conditions.
W19 closes the pole sector used by the laboratory without silently claiming
that larger amplitude basis.

## Counterterms implemented

For each successful case the report contains finite one-loop counterterms for:

* the singlet-portal Higgs tadpole, mass and field;
* W/Z masses and field residues;
* photon field and Z–photon off-diagonal fields;
* the Thomson electric charge;
* the weak mixing angle and derived \(g_2,g_Y\) OS shifts;
* the singlet scalar mass and field;
* every registered vector-like fermion mass and field.

The gauge-boson sector uses the full finite MSbar logarithm, rather than the
zero-momentum-subtracted diagnostic from W18. The photon and Z–photon
functions retain the required Ward-identity controls

\[
\Pi_{AA}(0)=0,\qquad \Pi_{ZA}(0)=0,
\]

and the Thomson charge counterterm is formed from the photon residue and
Z–photon mixing counterterm. Fermion self-energies are decomposed into vector
and scalar parts, including their momentum derivatives for the residue.

The real-pole control excludes absorptive parts above two-particle thresholds;
each case records whether the declared kinematics remain below threshold.

## Campaign result

The machine-readable report is
[`docs/validation/gauge_yukawa_bsm_on_shell_2026-11-23.json`](validation/gauge_yukawa_bsm_on_shell_2026-11-23.json).

| Status | Count |
|---|---:|
| `BSM_ONE_LOOP_ON_SHELL_COMPLETE` | 12 |
| `UPSTREAM_FAILURE` | 3 |

The three upstream zero-gauge controls are retained unchanged from W17; they
are not rerun or silently promoted. For each of the 12 successful cases the
report contains zero renormalized residuals for all declared OS conditions by
construction, together with the unrenormalized two-point functions and the
counterterms that cancel them.

No experimental datum, fit, ranking or automatic selection is used. The
on-shell pole observables are therefore the W17 baseline values interpreted in
the declared OS scheme, not a fitted reconstruction of measured masses.

## Scope boundary

This closes the complete one-loop OS pole sector, not every possible BSM
amplitude. The following remain explicitly outside the claim:

* pure-OS finite renormalization of gauge, Yukawa and scalar couplings;
* the complete one-loop three-point vertex basis;
* two-loop BSM counterterms and pole masses;
* absorptive parts and complex-pole treatment above thresholds;
* experimental comparison.

This boundary follows the standard on-shell organization of electroweak
renormalization and the general self-energy/pole-mass treatments in the
literature. Vector-like models require the same explicit mass, field and
mixing conditions; they cannot be closed by a mass shift alone.

## Literature and software anchors

* [Denner, one-loop electroweak renormalization and radiative corrections, arXiv:0709.1075](https://arxiv.org/abs/0709.1075)
* [Möhling, Stöckinger and Stöckinger-Kim, on-shell renormalization with vector-like leptons, arXiv:2407.09421](https://arxiv.org/abs/2407.09421)
* [Martin, fermion self-energies and pole masses in a general renormalizable theory, hep-ph/0509115](https://arxiv.org/abs/hep-ph/0509115)
* [Martin, two-loop scalar self-energies in a general renormalizable theory, hep-ph/0312092](https://arxiv.org/abs/hep-ph/0312092)
* [Braathen, Goodsell and Slavich, one-loop matching of renormalisable couplings, arXiv:1810.09388](https://arxiv.org/abs/1810.09388)
* [Martin and Robertson, SMDR, arXiv:1907.02500](https://arxiv.org/abs/1907.02500)

W19 is a reproducible implementation of the declared reduced model and
scheme; it is not presented as a replacement for a general-purpose symbolic
package such as SARAH or a full two-loop precision code.
