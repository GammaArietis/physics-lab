# Known-physics particle in a one-dimensional box

This is the next executable known-physics baseline after the harmonic
oscillator and the free scalar field.

Scope:

- non-relativistic quantum mechanics;
- one spatial coordinate on the open interval 0 < x < L;
- infinite-wall Dirichlet boundary conditions psi(0) = psi(L) = 0;
- positive input parameters m, L and hbar;
- no external data, fitting or empirical comparison.

The action is the free-particle action inside the interval. Canonical
quantization on the Dirichlet domain gives

    H = p^2/(2*m) = -hbar^2/(2*m) d^2/dx^2
    E_n = pi^2*hbar^2*n^2/(2*m*L^2),  n = 1, 2, ...

The ground state is n = 1. The parameter-free observable is

    (E_n - E_1)/(E_2 - E_1) = (n^2 - 1)/3

The displayed n range is a report window, not a search bound. The candidate is
registered but not selected, and its empirical-comparison gate remains closed.
