"""Independent derivation of the twisted-circle spectrum."""

from __future__ import annotations

import sympy as sp


def test_independent_multiplier_and_general_solution():
    theta = sp.symbols("theta", real=True)
    nu, phi = sp.symbols("nu phi", real=True)
    chi = sp.exp(sp.I * nu * theta)
    ratio = sp.simplify(chi.subs(theta, theta + 2 * sp.pi) / chi)
    assert sp.simplify(ratio / sp.exp(sp.I * 2 * sp.pi * nu)) == 1
    n = sp.symbols("n", integer=True)
    rho = phi / (2 * sp.pi)
    nu_n = n + rho
    imposed = sp.simplify(sp.exp(sp.I * 2 * sp.pi * nu_n) / sp.exp(sp.I * phi))
    assert imposed == 1


def test_independent_xi_form_k_equals_n_plus_rho_over_R():
    xi = sp.symbols("xi", real=True)
    k, R, phi = sp.symbols("k R phi", real=True, positive=True)
    chi = sp.exp(sp.I * k * xi)
    ratio = sp.simplify(chi.subs(xi, xi + 2 * sp.pi * R) / chi)
    assert sp.simplify(ratio / sp.exp(sp.I * 2 * sp.pi * k * R)) == 1
    n = sp.symbols("n", integer=True)
    rho = phi / (2 * sp.pi)
    k_n = (n + rho) / R
    imposed = sp.simplify(sp.exp(sp.I * 2 * sp.pi * k_n * R) / sp.exp(sp.I * phi))
    assert imposed == 1


def test_independent_t3_is_full_period_hence_periodic():
    theta = sp.symbols("theta", real=True)
    n = sp.symbols("n", integer=True)
    chi = sp.exp(sp.I * n * theta)
    one_step = 2 * sp.pi / 3
    t3 = chi.subs(theta, theta + 3 * one_step)
    full = chi.subs(theta, theta + 2 * sp.pi)
    assert sp.simplify(t3 / full) == 1
    for n_val in range(-4, 5):
        chi_n = sp.exp(sp.I * n_val * theta)
        assert sp.simplify(chi_n.subs(theta, theta + 2 * sp.pi) / chi_n) == 1


def test_independent_character_twist_is_on_the_short_cell():
    """χ(θ+2π/3)=ω^r χ(θ) is not χ(θ+2π)=ω^r χ(θ)."""
    theta = sp.symbols("theta", real=True)
    w = sp.exp(sp.I * 2 * sp.pi / 3)
    for n in range(-6, 7):
        chi = sp.exp(sp.I * n * theta)
        short = sp.simplify(chi.subs(theta, theta + 2 * sp.pi / 3) / chi)
        full = sp.simplify(chi.subs(theta, theta + 2 * sp.pi) / chi)
        assert full == 1
        r = n % 3
        assert sp.simplify(short / (w ** r)) == 1


def test_independent_rescaled_cell_gives_rho_from_chosen_r():
    """α=3θ: ψ(α+2π)=ω^r ψ(α) ⇒ κ = m + r/3.  J_θ = 3 κ remains integer."""
    alpha = sp.symbols("alpha", real=True)
    w = sp.exp(sp.I * 2 * sp.pi / 3)
    for r in (0, 1, 2):
        for m in range(-2, 3):
            kappa = m + sp.Rational(r, 3)
            psi = sp.exp(sp.I * kappa * alpha)
            ratio = sp.simplify(psi.subs(alpha, alpha + 2 * sp.pi) / psi)
            assert sp.simplify(ratio / (w ** r)) == 1
            j_theta = 3 * kappa
            assert sp.simplify(j_theta - (3 * m + r)) == 0
            assert int(j_theta) == 3 * m + r
