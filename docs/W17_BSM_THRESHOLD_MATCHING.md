# W17 — BSM threshold matching control

## Objective

W17 extends the W16 projection by applying an explicit one-loop
\(\overline{\mathrm{MS}}\) threshold control before invoking the official SMDR
executable. The input remains the W15 target-blind IR state; no measured mass
or coupling is used as a target.

The registered W15 action is

\[
V \supset \lambda_h (H^\dagger H)^2 + \lambda_{hs}S^2H^\dagger H,
\qquad
M_\Psi\bar\Psi\Psi+y_SS\bar\Psi\Psi,
\]

with a real \(Z_2\)-even singlet and anomaly-free vector-like Dirac
multiplets. W15 already contains the piecewise running across the vector-like
thresholds. W17 adds the corresponding one-loop logarithmic matching control
and scans a declared singlet-mass grid.

## Matching equations

For each vector-like threshold, the heavy-field contribution \(\Delta b_i\)
is derived from the registered representation. At the declared matching scale
\(\mu\), the gauge projection uses

\[
\frac{1}{g_i^2}\longrightarrow
\frac{1}{g_i^2}+\frac{\Delta b_i}{16\pi^2}
\log\frac{\mu^2}{M_\Psi^2}.
\]

For the unbroken \(Z_2\) singlet and the W15 portal convention, the
one-loop effective-potential threshold control is

\[
\lambda_h\longrightarrow \lambda_h+
\frac{\lambda_{hs}^2}{16\pi^2}
\log\frac{m_S^2}{\mu^2}.
\]

At this order the registered vector-like Yukawa \(y_S\) has no direct Higgs
or top-Yukawa matching term, because it couples the singlet to \(\Psi\), not
the Higgs doublet to the SM top sector. That zero is recorded as a structural
control, not inserted to improve agreement.

## Reproduced campaign

The archived report is
[`docs/validation/gauge_yukawa_bsm_threshold_matching_2026-11-16.json`](validation/gauge_yukawa_bsm_threshold_matching_2026-11-16.json).
It evaluates all five W15 candidates at the pre-registered singlet masses

\[
 m_S\in\{10^3,10^5,10^8\}\ \mathrm{GeV},
\]

for 15 cases in source order:

* 12 cases return `SMDR_COMPLETE`;
* the three `ZERO_PROTECTED` gauge-control cases remain `BACKEND_FAILURE`
  because SMDR does not complete on exactly vanishing gauge inputs within the
  declared 10-second per-case timeout.

The corrected projections remain far from the Standard Model regime. The
successful cases give approximately \(M_W=2.463\) GeV, \(M_Z=2.641\) GeV,
\(M_t=8.701\) GeV and \(1/\alpha\simeq 240,969\text{--}240,973\). The portal
shift is only \(2.9\times10^{-8}\) to \(1.7\times10^{-7}\) over the declared
mass grid. This is a useful negative result: the one-loop threshold layer does
not rescue the weak-coupling W15 IR trajectories.

## Boundary of the claim

W17 is a reproducible one-loop threshold control, not a complete BSM pole
calculation. In particular, it does not include the full new-sector
wave-function, vertex and self-energy corrections needed to turn the pure-SM
SMDR projection into a precision prediction of the extended model. It also
does not fit the singlet mass grid, rank cases, select a candidate or compare
the generated poles with experiment.

The next possible extension is therefore not another arbitrary mass scan. It
is a model-complete BSM self-energy/matching backend, or a published backend
whose complete conventions and diagrams can be reproduced independently.

## Literature and software anchors

* [Official SMDR repository](https://github.com/davidgrobertson/SMDR)
* [Official SMDR documentation](https://davidgrobertson.github.io/SMDR/)
* [Martin and Robertson, SMDR, arXiv:1907.02500](https://arxiv.org/abs/1907.02500)
* [Martin, SM decoupling relations at two loops, arXiv:1812.04100](https://arxiv.org/abs/1812.04100)
* [Braathen, Goodsell and Slavich, one-loop matching of renormalisable couplings, arXiv:1810.09388](https://arxiv.org/abs/1810.09388)
* [Elias-Miró et al., scalar threshold effect, arXiv:1203.0237](https://arxiv.org/abs/1203.0237)
* [Luo and Xiao, two-loop Standard Model RGEs, arXiv:hep-ph/0207271](https://arxiv.org/abs/hep-ph/0207271)

The implementation uses these sources as convention and method anchors. The
archived report explicitly separates the published ingredients from the
laboratory's reduced BSM control and does not present the run as a literature
reproduction beyond that declared scope.
