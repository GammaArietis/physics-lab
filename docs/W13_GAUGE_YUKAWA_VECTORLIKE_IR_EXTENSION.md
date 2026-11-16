# W13 — Gauge–Yukawa vector-like IR/EFT extension

## Result

The laboratory now contains one explicit extension of the Standard Model:

\[
  \mathcal L = \mathcal L_{SM} + \frac12(\partial S)^2
  -\frac{m_S^2}{2}S^2 -\frac{\lambda_S}{4}S^4
  +i\bar\Psi\!\not\!D\Psi -M_\Psi\bar\Psi\Psi
  -y_S S\bar\Psi\Psi -\lambda_{HS}S^2H^\dagger H .
\]

`Q`, `U`, `D`, `L` and `E` are registered as vector-like Dirac pairs. Their
one-loop gauge contributions are derived from the representation indices, not
entered as unexplained coefficients. The real singlet is Z2-even in this
control, so the cubic singlet operator is absent.

The pipeline is:

`activation → explicit action → representation-derived b_i → reduced one-loop running → IR observables`.

The observables include `g1`, `g2`, `g3`, the electromagnetic coupling
`e`, `alpha_em`, `alpha_s`, the new Yukawa and the scalar/portal quartics.

## What this does and does not establish

This is a real, reproducible EFT branch, but it is not yet a precision SM
matching calculation. The gauge coefficients are one-loop controlled; the
Yukawa and scalar block is explicitly labelled a reduced control. It does not
claim a two-loop/NNLO result, an interacting fixed point, a fit to the measured
fine-structure constant, or a rescue of W11 states with exactly zero gauge
couplings.

The last point is structural: with perturbative beta functions of the form
`beta_g = g^3 f(g,...)`, an exactly zero gauge coupling remains zero. Adding
vector-like matter changes `f`, but does not create an additive seed. This
campaign therefore tests which non-degenerate branches are physically viable;
it does not silently repair the negative W11 replay.

## Literature anchor

Vector-like fermions in gauge–Yukawa theories and interacting UV fixed points
are established research directions, including the large-flavour analysis of
Litim–Sannino and vector-like extensions of the Standard Model. The present
module is a controlled laboratory implementation inspired by that literature,
not a claim to reproduce its full multi-loop truncations. See:

* D. F. Litim and F. Sannino, *Asymptotic safety guaranteed*,
  [arXiv:1406.2337](https://arxiv.org/abs/1406.2337).
* R. Mann et al., *Asymptotically Safe Standard Model via Vector-Like
  Fermions*, [arXiv:1707.02942](https://arxiv.org/abs/1707.02942).
* E. Eichhorn and A. Held, *Top mass from asymptotic safety*,
  [Phys. Lett. B 777 (2018)](https://doi.org/10.1016/j.physletb.2017.12.040).

