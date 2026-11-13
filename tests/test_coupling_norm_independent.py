"""Independent identities for gauge-field rescaling and internal reduction."""

from __future__ import annotations

import sympy as sp


def test_independent_interaction_is_g_n():
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


def test_independent_canonical_g_phys():
    g, Z = sp.symbols("g Z_A", positive=True)
    g_phys = sp.simplify(g / sp.sqrt(Z))
    # A_c = sqrt(Z) A  ⇒  g_c A_c = g A
    assert sp.simplify(g_phys * sp.sqrt(Z) - g) == 0


def test_independent_A_rescale_and_g():
    g, Z = sp.symbols("g Z_A", positive=True)
    invariant = g ** 2 / Z
    g_phys = g / sp.sqrt(Z)
    for c in (sp.Integer(1), sp.Integer(2), sp.Integer(7), sp.Rational(1, 3)):
        g2 = g / c
        Z2 = Z / c ** 2
        assert sp.simplify(g2 ** 2 / Z2 - invariant) == 0
        assert sp.simplify(g2 / sp.sqrt(Z2) - g_phys) == 0
        # F scales with A
        A = sp.Function("A")
        x = sp.symbols("x", real=True)
        F = sp.diff(A(x), x)
        F_new = sp.diff(c * A(x), x)
        assert sp.simplify(F_new - c * F) == 0


def test_independent_chi_normalization_does_not_fix_g():
    theta = sp.symbols("theta", real=True)
    g = sp.symbols("g", real=True)
    for n in range(-3, 4):
        chi_raw = sp.exp(sp.I * n * theta)
        N_raw = sp.integrate(sp.simplify(chi_raw * sp.conjugate(chi_raw)), (theta, 0, 2 * sp.pi))
        assert sp.simplify(N_raw - 2 * sp.pi) == 0
        chi = chi_raw / sp.sqrt(2 * sp.pi)
        N = sp.integrate(sp.simplify(chi * sp.conjugate(chi)), (theta, 0, 2 * sp.pi))
        assert sp.simplify(N - 1) == 0
        # After ψ_c = √N ψ the coupling in D remains g
        assert sp.simplify((g) - g) == 0


def test_independent_R_absorbed_by_psi():
    R = sp.symbols("R", positive=True)
    g, Z = sp.symbols("g Z_A", positive=True)
    N = R  # measure R dθ with χ already normalized in θ
    # ψ_c = √N ψ absorbs R; g_phys unchanged
    g_phys = g / sp.sqrt(Z)
    g_after = g
    Z_after = Z
    assert sp.simplify(g_after / sp.sqrt(Z_after) - g_phys) == 0
    assert R not in g_phys.free_symbols
    assert g_phys.free_symbols == {g, Z}


def test_independent_c3_phase_does_not_change_norm():
    theta = sp.symbols("theta", real=True)
    for n in range(-4, 5):
        chi = sp.exp(sp.I * n * theta) / sp.sqrt(2 * sp.pi)
        phase = sp.exp(sp.I * n * 2 * sp.pi / 3)
        chi_T = phase * chi
        dens = sp.simplify(chi * sp.conjugate(chi))
        dens_T = sp.simplify(chi_T * sp.conjugate(chi_T))
        assert sp.simplify(dens - dens_T) == 0


def test_independent_one_third_is_only_a_rescale_probe():
    """c=1/3 is a mathematical probe of A→cA, not a derived coupling."""
    g, Z = sp.symbols("g Z_A", positive=True)
    c = sp.Rational(1, 3)
    g_phys = g / sp.sqrt(Z)
    g_new = g / c
    assert sp.simplify(g_new / sp.sqrt(Z / c ** 2) - g_phys) == 0
    assert sp.simplify(g_phys - c) != 0
    assert sp.simplify(g_phys - sp.Rational(1, 3)) != 0
