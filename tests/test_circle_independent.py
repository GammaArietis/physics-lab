"""Independent circle-model checks that do not reuse the production verifier.

These tests write the expected formulae from the mathematics, not by calling
`verify_circle_momentum_eigenfunction` or copying results out of the solver.
"""

from __future__ import annotations

import math

import pytest
import sympy as sp

from physics_lab.core.provenance import Provenance
from physics_lab.models.examples.circle_model import build_circle_model


def _chi(n, xi, R):
    return sp.exp(sp.I * n * xi / R)


def test_independent_momentum_identity_n_values():
    """p_xi chi_n = n hbar / R chi_n for n = 0, 1, -1, 2, derived with SymPy."""
    xi = sp.symbols("xi", real=True)
    R, hbar = sp.symbols("R hbar", positive=True)

    def p_op(f):
        return -sp.I * hbar * sp.diff(f, xi)

    for n in (0, 1, -1, 2):
        chi = _chi(n, xi, R)
        residual = sp.simplify(p_op(chi) - (n * hbar / R) * chi)
        assert residual == 0


def test_independent_periodicity_requires_integer_n():
    """chi(xi + 2 pi R) = chi(xi) holds for integer n, not for n = 1/2."""
    xi = sp.symbols("xi", real=True)
    R = sp.symbols("R", positive=True)
    for n in (0, 1, -1, 2):
        chi = _chi(n, xi, R)
        shifted = _chi(n, xi + 2 * sp.pi * R, R)
        assert sp.simplify(shifted / chi) == 1
    n_half = sp.Rational(1, 2)
    chi = _chi(n_half, xi, R)
    shifted = _chi(n_half, xi + 2 * sp.pi * R, R)
    assert sp.simplify(shifted / chi) != 1


def test_independent_spectrum_mass_charge_for_selected_n():
    """Numeric values for non-default R, hbar, kappa, C, computed by hand."""
    R_val, hbar_val, kappa_val, C_val = 2.0, 3.0, 0.5, 4.0
    model = build_circle_model(
        radius=R_val,
        hbar=hbar_val,
        kappa=kappa_val,
        mass_constant=C_val,
        n_max=2,
    )
    result = model.solve()
    by_n = {int(s.quantum_numbers["n"]): s for s in result.spectrum.states}

    for n in (0, 1, -1, 2):
        state = by_n[n]
        p_expected = n * hbar_val / R_val
        lam_expected = p_expected ** 2
        m_expected = math.sqrt(C_val * lam_expected)
        q_expected = kappa_val * n * hbar_val / R_val

        assert state.eigenvalue.numeric() == pytest.approx(lam_expected)
        assert state.observables["momentum"].numeric() == pytest.approx(p_expected)
        assert state.observables["mass"].numeric() == pytest.approx(m_expected)
        assert state.observables["charge"].numeric() == pytest.approx(q_expected)

        assert state.observables["mass"].provenance is Provenance.ASSUMED
        assert "ASSUMED" in (state.observables["mass"].assumption or "")
        assert state.observables["charge"].provenance is Provenance.DERIVED
        assert state.observables["charge"].is_prediction() is False
        assert "kappa" in state.observables["charge"].free_dependencies
        assert "R" in state.observables["charge"].free_dependencies

    assert by_n[0].eigenvalue.numeric() == pytest.approx(0.0)
    assert by_n[0].observables["mass"].numeric() == pytest.approx(0.0)
    for n in (1, -1, 2):
        assert by_n[n].eigenvalue.numeric() > 0
        assert by_n[n].observables["mass"].numeric() > 0
