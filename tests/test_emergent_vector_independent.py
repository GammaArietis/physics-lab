"""Independent identities: Ψ modes, connection D_μ, and B rescaling."""

from __future__ import annotations

import sympy as sp


def test_independent_mode_expansion_is_scalar():
    x, theta = sp.symbols("x theta", real=True)
    psi = sp.Function("psi")
    n = 2
    chi = sp.exp(sp.I * n * theta)
    Psi = psi(x) * chi
    # A 4D Lorentz vector would be indexed. The internal mode coefficient is not.
    assert isinstance(psi(x), sp.Function)
    assert not isinstance(Psi, sp.Indexed)
    assert x in Psi.free_symbols
    assert theta in Psi.free_symbols


def test_independent_connection_gives_n_B():
    x, theta = sp.symbols("x theta", real=True)
    psi = sp.Function("psi")(x)
    B = sp.Function("B")(x)
    for n in range(-3, 4):
        chi = sp.exp(sp.I * n * theta)
        j_chi = -sp.I * sp.diff(chi, theta)
        DPsi = sp.diff(psi, x) * chi + sp.I * B * j_chi * psi
        expected = sp.diff(psi, x) * chi + sp.I * n * B * psi * chi
        assert sp.simplify(DPsi - expected) == 0


def test_independent_DPsi_squared_has_no_field_strength():
    """|DΨ|² has B and B², not ∂B − ∂B."""
    x, theta = sp.symbols("x theta", real=True)
    n = 1
    psi = sp.Function("psi")(x)
    B = sp.Function("B")(x)
    chi = sp.exp(sp.I * n * theta) / sp.sqrt(2 * sp.pi)
    D = sp.diff(psi, x) + sp.I * n * B * psi
    density = sp.simplify(sp.conjugate(D) * D * chi * sp.conjugate(chi))
    integrated = sp.integrate(density, (theta, 0, 2 * sp.pi))
    text = str(integrated)
    assert "B" in text or integrated.has(B)
    # No derivative of B appears in |DΨ|².
    assert sp.diff(B, x) not in integrated.atoms(sp.Derivative)


def test_independent_B_rescale_invariance():
    G, Z = sp.symbols("G_eff Z_B", positive=True)
    invariant = G ** 2 / Z
    G_phys = G / sp.sqrt(Z)
    for c in (sp.Integer(1), sp.Integer(2), sp.Integer(7), sp.Rational(1, 3)):
        G2 = G / c
        Z2 = Z / c ** 2
        assert sp.simplify(G2 ** 2 / Z2 - invariant) == 0
        assert sp.simplify(G2 / sp.sqrt(Z2) - G_phys) == 0


def test_independent_R_volume_is_not_a_unique_prediction():
    R, z = sp.symbols("R z", positive=True)
    Z_plain = z * 2 * sp.pi
    Z_R = z * 2 * sp.pi * R
    G_plain = 1 / sp.sqrt(Z_plain)
    G_R = 1 / sp.sqrt(Z_R)
    assert R in G_R.free_symbols
    assert z in G_plain.free_symbols
    # Setting z=1 still leaves a coordinate convention 2π, or R if restored.
    G_z1 = sp.simplify(G_plain.subs(z, 1))
    assert G_z1 == 1 / sp.sqrt(2 * sp.pi)
    assert sp.simplify(G_z1 - 1 / sp.sqrt(2 * sp.pi * R)) != 0


def test_independent_c3_phase_does_not_create_a_vector():
    theta = sp.symbols("theta", real=True)
    for n in range(-4, 5):
        chi = sp.exp(sp.I * n * theta)
        phase = sp.exp(sp.I * n * 2 * sp.pi / 3)
        assert sp.simplify(sp.Abs(phase) - 1) == 0
        # T χ = phase χ remains a scalar mode.
        assert sp.simplify(phase * chi - sp.exp(sp.I * n * (theta + 2 * sp.pi / 3))) == 0
