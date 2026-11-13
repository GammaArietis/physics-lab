"""Independent identities for D_μ = ∂_μ + i g A_μ J."""

from __future__ import annotations

import sympy as sp


def test_independent_j_eigenvalue():
    theta = sp.symbols("theta", real=True)
    for n in range(-4, 5):
        chi = sp.exp(sp.I * n * theta)
        j_chi = -sp.I * sp.diff(chi, theta)
        assert sp.simplify(j_chi - n * chi) == 0


def test_independent_dmu_produces_g_n():
    x, theta = sp.symbols("x theta", real=True)
    g = sp.symbols("g", real=True)
    psi = sp.Function("psi")(x)
    A = sp.Function("A")(x)
    for n in range(-3, 4):
        chi = sp.exp(sp.I * n * theta)
        dpsi = sp.diff(psi, x) * chi
        couple = sp.I * g * A * (-sp.I * sp.diff(chi, theta)) * psi
        total = sp.simplify(dpsi + couple)
        expected = sp.diff(psi, x) * chi + sp.I * (g * n) * A * psi * chi
        assert sp.simplify(total - expected) == 0


def test_independent_gauge_covariance():
    x, theta = sp.symbols("x theta", real=True)
    g = sp.symbols("g", real=True)
    n = 2
    psi = sp.Function("psi")(x)
    A = sp.Function("A")(x)
    Lam = sp.Function("Lam")(x)
    chi = sp.exp(sp.I * n * theta)

    def D(psi_f, A_f):
        return sp.diff(psi_f, x) * chi + sp.I * g * n * A_f * psi_f * chi

    Dpsi = D(psi, A)
    psi_p = sp.exp(-sp.I * g * n * Lam) * psi
    A_p = A + sp.diff(Lam, x)
    left = sp.simplify(sp.expand(D(psi_p, A_p)))
    right = sp.simplify(sp.expand(sp.exp(-sp.I * g * n * Lam) * Dpsi))
    assert sp.simplify(left - right) == 0


def test_independent_coupling_not_r_over_three():
    """n=1 and n=4 share a C3 character class but not the same g n."""
    w = sp.exp(sp.I * 2 * sp.pi / 3)
    g = sp.symbols("g", real=True)
    for n, r in ((1, 1), (4, 1), (2, 2), (5, 2)):
        phase = sp.simplify(sp.exp(sp.I * n * 2 * sp.pi / 3) / (w ** r))
        assert phase == 1
    assert sp.simplify(g * 1 - g * 4) != 0
    assert sp.simplify(g * 1 - g * sp.Rational(1, 3)) != 0
