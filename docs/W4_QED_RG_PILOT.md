# W4 — One-loop QED renormalization-group control pilot

This pilot is the first controlled implementation of the dynamic-equilibrium
direction. It starts from known QED and integrates the running fine-structure
coupling as a renormalization-group state variable:

\[
\frac{d\alpha}{d\log\mu} = \frac{2N_f}{3\pi}\alpha^2.
\]

For a finite offset \(t=\log(\mu/\mu_0)\), the one-loop trajectory is

\[
\alpha(t) = \frac{\alpha_0}{1 - \frac{2N_f\alpha_0}{3\pi}t},
\]

and its formal Landau-pole offset is

\[
t_L = \frac{3\pi}{2N_f\alpha_0}.
\]

## What is verified

- the known one-loop QED beta-function coefficient;
- the Gaussian fixed point \(\alpha_*=0\);
- the one-loop IR-attractive / UV-repulsive behavior of that fixed point;
- bounded analytic trajectories for three mathematical initial conditions;
- explicit rejection of trajectories that cross the one-loop Landau pole;
- target-blind execution with no external data, fitting, ranking or selection.

The initial values \(0.01\), \(0.05\) and \(0.10\) are trajectory seeds for a
mathematical control. They are not measurements and are not used to estimate
the physical fine-structure constant.

## What is not claimed

This pilot does not derive \(1/137\), establish an interacting ultraviolet
fixed point, prove asymptotic safety, resolve threshold matching, or perform a
global Standard Model running. The W3A \(F^4\) operators remain inactive and
their unresolved Wilson coefficients are not promoted by this result.

The next gate is a second known-physics control for one-loop threshold
matching before any speculative fixed-point search is considered.
