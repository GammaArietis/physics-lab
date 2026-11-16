# W11 IR/EFT rescue audit — 2026-11-16

## Result

The declared known-physics IR/EFT mechanisms do not rescue the W11 gauge
sector. The audit is target-blind and retains every W11 source case:

| quantity | result |
|---|---:|
| source configurations | 28,692 |
| complete W11 electroweak states | 27,060 |
| states with no W11 electroweak state | 1,632 |
| all gauge couplings exactly zero | 1,404 |
| partial gauge-zero states | 17,880 |
| nonzero multiplicative-flow states | 7,776 |
| known IR/EFT rescues | 0 |

The machine-readable summary is
`docs/validation/w11_ir_eft_rescue_audit_2026-11-16_summary.json`; the full
per-case audit is compressed in
`docs/validation/w11_ir_eft_rescue_audit_2026-11-16.json.gz`.

## What was tested

### Ordinary SM running

The one-loop control uses the GUT-normalized W11 gauge convention

\[
 \beta_{g_i}=\frac{b_i g_i^3}{16\pi^2},\qquad
 (b_1,b_2,b_3)=\left(\frac{41}{10},-\frac{19}{6},-7\right).
\]

The exact solution has

\[
 \frac{1}{g_i^2(\mu)}=\frac{1}{g_i^2(Q)}-
 \frac{b_i}{8\pi^2}\log\frac{\mu}{Q}.
\]

Therefore an exactly zero gauge coupling is an invariant surface of the
declared perturbative flow. The audit records this as `ZERO_PROTECTED`; it
does not replace zero by a small numerical seed.

### Threshold and low-energy EFT controls

The audit also runs a QED+QCD five-quark/three-lepton control below the
electroweak scale. It tests changes in beta coefficients and decoupling
structure, not an arbitrary IR boundary condition. The largest absolute
low-probe controls in the complete W11 ensemble are:

| control | maximum absolute value at 2 GeV |
|---|---:|
| unbroken-SM g1 (GUT normalized) | 0.65636 |
| unbroken-SM g2 | 0.06990 |
| unbroken-SM g3 | 0.07024 |
| QED e | 0.04256 |
| QCD g3 | 0.07025 |

These are descriptive envelopes, not selected candidates. They remain far
from the SMDR reference gauge sector (`g2≈0.648`, `g3≈1.164`,
`gp≈0.359`) and do not repair the complete SMDR failures.

## Mechanism verdicts

| proposed mechanism | verdict |
|---|---|
| ordinary SM running | cannot seed an exact zero |
| known threshold decoupling | changes coefficients/matching, but supplies no missing non-Abelian seed |
| additional non-Abelian matter | changes beta coefficients; does not seed zero by itself |
| multiple-U(1) kinetic mixing | can affect an Abelian coordinate only; requires a second U(1) and bi-charged matter |
| imposed IR boundary condition | disallowed as a rescue; it is a new physical input or target leakage |
| residual gravity additive term | not derived in the current W11 IR truncation |

The result is not that every conceivable new theory is impossible. It is that
the registered SM/QCD+QED EFT mechanisms do not generate the missing gauge
sector. A rescue requires either a W11 branch that already has nonzero gauge
couplings in the IR window or a derived extension containing new field
content/interactions and a complete action-to-observables pipeline.

## Interpretation of the SMDR failures

The subsequent SMDR replay found 26,964 `SIGABRT` failures from undefined TSIL
arguments and too-small/degenerate inputs, 96 explicit negative-squared-mass
failures, and 1,632 W11 states that were not eligible for replay. The IR/EFT
audit explains why a threshold-only rescue cannot be expected: most complete
states lie on exact or partial gauge-zero surfaces, and the remaining states
stay parametrically small under the declared multiplicative flows.

No coupling was clipped, fitted, selected, or seeded by hand.

## Primary bibliography

- Martin and Robertson, *Standard Model parameters in the tadpole-free pure
  MSbar scheme*, arXiv:1907.02500:
  <https://arxiv.org/abs/1907.02500>
- Martin, *Matching relations for decoupling in the Standard Model at two loops
  and beyond*, arXiv:1812.04100:
  <https://arxiv.org/abs/1812.04100>
- Luo and Xiao, *Two-loop Renormalization Group Equations in the Standard
  Model*, arXiv:hep-ph/0207271:
  <https://arxiv.org/abs/hep-ph/0207271>
- Luo and Xiao, *Renormalization Group Equations in Gauge Theories with
  Multiple U(1) Groups*, arXiv:hep-ph/0212152:
  <https://arxiv.org/abs/hep-ph/0212152>
- Dekens and Stoffer, *Low-energy effective field theory below the electroweak
  scale: matching at one loop*, arXiv:1908.05295:
  <https://arxiv.org/abs/1908.05295>
- Eichhorn and Held, *Top mass from asymptotic safety*,
  <https://doi.org/10.1016/j.physletb.2017.12.040>
