# W13 — Maxwell E/B geometry audit

## What is physically different between E and B?

The visual intuition is useful, but the correct separation is topological and
source-based rather than “continuous versus discrete”. In ordinary Maxwell
theory:

* `div B = 0` in the absence of magnetic monopoles, so magnetic field lines
  have no endpoints and close or escape through the boundary;
* `div E = rho/epsilon_0`, so electric field lines can begin/end on electric
  charge or continue to infinity;
* both `E` and `B` are components of the same antisymmetric tensor `F` and
  both are continuous classical fields in the continuum theory;
* for a plane wave, `E`, `B` and the propagation direction are mutually
  orthogonal, with `|E|=c|B|` and `E/H=Z_0`.

The “ombrello” or closed-steck geometry can therefore be a good visualisation
of a dipole or solenoid, but field lines are not quantised tubes. Quantised
flux appears in specific quantum systems; it is not a generic discretisation
of the Maxwell magnetic field.

## What can be tested without cheating?

The campaign computes the Lorentz scalars

\[
 I_1 = F_{\mu\nu}F^{\mu\nu} \propto B^2-E^2/c^2,
 \qquad
 I_2 = F_{\mu\nu}\widetilde F^{\mu\nu} \propto \mathbf E\cdot\mathbf B/c,
\]

and the Poynting direction `E x H`. It also records electric/magnetic energy
fractions and support-area scalings. A raw area or volume ratio is not Lorentz
invariant, depends on the chosen support and dimensions, and cannot by itself
be identified with `alpha`.

For a null plane wave, the energy ratio is exactly one. More generally, if the
magnetic amplitude is changed by a continuous factor `r`, the electric-to-
magnetic energy ratio changes as `1/r^2`. Thus `1/137` can be manufactured by
choosing `r=sqrt(137)`, but that is a parameterisation, not a prediction.

The only promising geometric route is to construct a gauge- and Lorentz-
invariant action/topological quantity that fixes a dimensionless coefficient
without inserting `alpha` as a target, and then test it against independent
observables. The present audit records that requirement explicitly.

