# W18 — BSM self-energy, wave-function and finite two-point backend

## Objective

W18 adds a genuine model-specific BSM two-point calculation to the W17
gauge–Yukawa–scalar extension.  The registered action contains a real
(Z_2)-even singlet (S), vector-like Dirac multiplets (Psi), the portal
(lambda_{HS}S^2H^dagger H), and the Yukawa interaction
(y_SS\bar\Psi\Psi).  The implementation evaluates the finite one-loop
new-sector channels that are present in that action and applies them to every
successful W17 SMDR projection without using measured observables as targets.

The backend is deliberately explicit about its boundary: it is complete for
the registered new-sector two-point channels at one loop, but it is not a
complete two-loop or fully on-shell BSM renormalization program.

## Implemented finite channels

At the declared scale (mu=91.1876) GeV the backend records:

* the finite scalar integrals (A_0), (B_0), and (dB_0/dp^2);
* the singlet contribution to the Higgs two-point function from the portal;
* the finite Higgs wave-function derivative and residue factor;
* transverse vector-like Dirac vacuum polarizations for (W), (Z), photon,
  and (Zgamma) mixing;
* finite vector wave-function derivatives and residue factors;
* the zero-momentum singlet self-energy induced by (y_SarPsiPsi S);
* target-blind finite shifts of the W17 (H,W,Z,alpha^{-1}) projection.

The registered action has no direct Higgs–vector-like-fermion Yukawa.  The BSM
top self-energy is therefore recorded as structurally zero at this order; it
is not silently omitted.

## Renormalization convention

The raw MSbar Higgs insertion contains a momentum-independent
(A_0(m_S^2)) term and the zero-momentum part of (B_0).  Those terms
renormalize the Higgs mass parameter and mix with the tadpole counterterm. A
pole-mass shift cannot be assigned to them without specifying the complete
broken-phase tadpole and counterterm scheme.

W18 therefore stores both quantities:

[
Pi_h^{\rm raw}(p^2)=\frac{1}{16\pi^2}
\left[\lambda_{HS}A_0(m_S^2)+2\lambda_{HS}^2v^2B_0(p^2;m_S,m_S)\right],
]

and the finite decoupling-subtracted insertion used for the reported Higgs
shift,

[
Pi_h^{\rm dec}(p^2)=\Pi_h^{\rm raw}(p^2)-\Pi_h^{\rm raw}(0)
=\frac{2\lambda_{HS}^2v^2}{16\pi^2}
\left[B_0(p^2)-B_0(0)\right].
]

The pole insertion convention is

[
m_{\rm BSM}^2=m_{\rm SMDR}^2+
\frac{\operatorname{Re}\Pi(m_{\rm SMDR}^2)}{1-d\Pi/dp^2}.
]

This subtraction is a decoupling/mass-parameter control, not a claim that the
full on-shell tadpole scheme has been implemented.  The raw term remains in
the JSON report precisely so that a later complete counterterm implementation
can audit the difference.

## Campaign result

The reproducible report is
[`docs/validation/gauge_yukawa_bsm_self_energy_2026-11-16.json`](validation/gauge_yukawa_bsm_self_energy_2026-11-16.json).
It contains all 15 W17 cases in source order:

| Status | Count | Meaning |
|---|---:|---|
| `BSM_ONE_LOOP_COMPLETE` | 12 | all registered two-point channels evaluated |
| `UPSTREAM_FAILURE` | 3 | W17 zero-gauge controls retained without rerunning them |

For the 12 successful cases, the decoupling-subtracted Higgs shifts are finite
and decouple with increasing singlet mass.  At (m_S=10^3) GeV they are about
(1.49\times10^{-9}) GeV; at (10^5) GeV about
(1.49\times10^{-13}) GeV; at (10^8) GeV about
(1.74\times10^{-19}) GeV.  The raw unsubtracted MSbar mass-parameter terms
can instead be very large for the same cases; they are retained as diagnostics
and are not used as physical pole shifts.

The vector-like gauge insertions are also decoupling-suppressed for heavy
multiplets.  No case is ranked, selected, fitted, or compared with experiment.

## What remains outside W18

The following are explicit non-claims:

* complete broken-phase BSM tadpole and counterterm renormalization;
* all one-loop BSM vertices and mixing counterterms;
* full treatment of (Z\gamma) mixing in the shifted pole equations;
* two-loop BSM self-energies and pole matching;
* experimental comparison or parameter inference.

The next scientifically meaningful extension is to close these missing
renormalization conditions consistently, not to interpret the raw (A_0)
term as a new prediction.

## Literature and software anchors

* [Martin, fermion self-energies and pole masses in a general renormalizable theory, hep-ph/0509115](https://arxiv.org/abs/hep-ph/0509115)
* [Martin, two-loop scalar self-energies in a general renormalizable theory, hep-ph/0312092](https://arxiv.org/abs/hep-ph/0312092)
* [Staub, SARAH: automatic calculation of RGEs and self-energies, arXiv:1002.0840](https://arxiv.org/abs/1002.0840)
* [Camargo-Molina et al., one-loop scalar vertices and effective potential, arXiv:1606.07069](https://arxiv.org/abs/1606.07069)
* [Braathen, Goodsell and Slavich, one-loop matching of renormalisable couplings, arXiv:1810.09388](https://arxiv.org/abs/1810.09388)
* [Martin and Robertson, SMDR, arXiv:1907.02500](https://arxiv.org/abs/1907.02500)
* [Official SMDR repository](https://github.com/davidgrobertson/SMDR)

These sources anchor the integral, matching and pole-mass conventions. W18 is
reported as a reproducible laboratory implementation of the declared reduced
model, not as a claim to reproduce every diagram in those general frameworks.
