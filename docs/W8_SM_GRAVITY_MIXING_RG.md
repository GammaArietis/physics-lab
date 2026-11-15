# W8 — Reduced Standard Model, gravity and U(1)-mixing RG campaign

W8 executes three related controls in one reproducible report. They are kept
separate because they answer different questions and have different physical
status.

## Subcampaigns

### Reduced Standard Model control

The first subcampaign uses the one-loop equations for the GUT-normalized

\[
 (g_1,g_2,g_3,y_t,\lambda)
\]

sector. It is a reduced control: it does not claim the full precision Standard
Model, threshold matching, neutrino sector, or higher-loop running. In this
polynomial one-loop truncation the real perturbative fixed point is Gaussian.
The positive one-loop Abelian coefficient remains visible, while the
non-Abelian gauge factors are asymptotically free.

### Background-gravity Abelian control

The second subcampaign evaluates the literature-shaped ansatz

\[
 \beta_{g_1}=-A g_1+\frac{41/10}{16\pi^2}g_1^3.
\]

For \(A>0\) it records both \(g_1=0\) and the positive nonzero root. The
Gaussian root is UV-attractive in this convention; the nonzero root is
UV-repulsive. Thus this ansatz can represent gravity driving the Abelian
coupling toward a free UV fixed point or imposing an upper-bound structure,
but it does not produce a nonzero UV-attractive value of the coupling and does
not derive \(1/137\).

This is a background-gravity control, not a calculation of a coupled quantum
gravity–matter fixed point. Scheme, gauge and truncation dependence must be
resolved before treating any coefficient \(A\) as physical.

### Two-U(1) mixing control

The third subcampaign uses the charge-agnostic normalized control

\[
 \beta_i=\frac{g_i}{16\pi^2}\sum_j B_{ij}g_j^2,
\]

with positive-semidefinite symmetric matrices \(B\). This deliberately checks
whether positive cross-couplings alone generate a nonzero fixed point in the
nonnegative quadrant. They do not: the Gaussian point is retained and all
trajectories are recorded. No physical charge assignment, matter spectrum or
full kinetic-mixing convention is silently invented.

## Broad run and controls

- 4 reduced-Standard-Model initial states;
- 6 background-gravity coefficients and 3 Abelian seeds: 18 trajectories;
- 3 positive-semidefinite two-U(1) matrices and 3 initial states: 9
  trajectories;
- five logarithmic scale offsets per trajectory;
- no experimental data, fitting, ranking, automatic selection or use of alpha
  as a target;
- W3A \(F^4\) operators remain inactive.

The generated JSON report preserves the equations, fixed-point residuals,
trajectories, controls and bibliography:

`docs/validation/sm_gravity_mixing_rg_campaign_2026-11-15.json`

## Conclusion

The combined run does not find a mechanism that forces a nonzero Abelian
coupling. The reduced Standard Model control is Gaussian in the stated
truncation. The simple gravity deformation supplies a nonzero algebraic root
but not a UV-attractive one. Positive mixing controls remain Gaussian. The
decisive missing input is therefore a specific, independently derived
gravity–matter or multi-U(1) beta system, including its charge content,
matching prescription and scheme/truncation audit.

## References

1. M. E. Machacek and M. T. Vaughn, *Two-loop renormalization group
   equations in a general quantum field theory*, Nucl. Phys. B 222, 83
   (1983), DOI [10.1016/0550-3213(83)90610-7](https://doi.org/10.1016/0550-3213(83)90610-7).
2. M.-x. Luo and Y. Xiao, *Two-loop renormalization group equations in the
   Standard Model*, Phys. Rev. Lett. 90, 011601 (2003), DOI
   [10.1103/PhysRevLett.90.011601](https://doi.org/10.1103/PhysRevLett.90.011601).
3. M.-x. Luo and Y. Xiao, *Renormalization group equations in gauge theories
   with multiple U(1) groups*, Phys. Lett. B 555, 279 (2003), DOI
   [10.1016/S0370-2693(03)00076-5](https://doi.org/10.1016/S0370-2693(03)00076-5).
4. A. Eichhorn and F. Versteegen, *Upper bound on the Abelian gauge coupling
   from asymptotic safety*, JHEP 01 (2018) 030, DOI
   [10.1007/JHEP01(2018)030](https://doi.org/10.1007/JHEP01(2018)030).
5. A. Riabokon, M. Schiffer and F. Wagner, *Regulator and gauge dependence of
   the Abelian coupling in asymptotically safe gravity*, Phys. Rev. D 112
   (2025), DOI [10.1103/gxm2-trn6](https://doi.org/10.1103/gxm2-trn6).

This is a bounded literature-anchored control campaign, not a derivation of
the observed fine-structure constant.
