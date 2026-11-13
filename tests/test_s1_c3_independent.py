"""Independent S¹+C3 checks written from the equations, not from sector lists."""

from __future__ import annotations

import sympy as sp

from physics_lab.models.examples.s1_c3_model import build_s1_c3_model


def _chi(n, theta):
    return sp.exp(sp.I * n * theta)


def test_independent_s1_periodicity_integer_n():
    theta = sp.symbols("theta", real=True)
    for n in range(-6, 7):
        chi = _chi(n, theta)
        assert sp.simplify(_chi(n, theta + 2 * sp.pi) / chi) == 1
    chi_half = _chi(sp.Rational(1, 2), theta)
    assert sp.simplify(_chi(sp.Rational(1, 2), theta + 2 * sp.pi) / chi_half) != 1


def test_independent_c3_multiplier_from_shift():
    """χ_n(θ + 2π/3) / χ_n(θ) = exp(i n 2π / 3), derived by substitution."""
    theta = sp.symbols("theta", real=True)
    for n in range(-6, 7):
        chi = _chi(n, theta)
        shifted = chi.subs(theta, theta + 2 * sp.pi / 3)
        phase = sp.simplify(sp.together(shifted / chi))
        expected = sp.simplify(sp.exp(sp.I * n * 2 * sp.pi / 3))
        assert sp.simplify(phase - expected) == 0


def test_independent_three_applications_are_s1_periodicity():
    """T³ is the S¹ identification, hence identity on integer-n waves."""
    theta = sp.symbols("theta", real=True)
    shift = 2 * sp.pi / 3
    for n in range(-6, 7):
        chi = _chi(n, theta)
        cubed = chi.subs(theta, theta + 3 * shift)
        assert sp.simplify(sp.together(cubed / chi)) == 1
        assert sp.simplify(3 * shift - 2 * sp.pi) == 0


def test_independent_phase_matching_implies_residue_classes():
    """Classify by which cube root the phase is; then n ≡ r (mod 3) follows."""
    omega = sp.exp(sp.I * 2 * sp.pi / 3)
    roots = (sp.Integer(1), sp.simplify(omega), sp.simplify(omega ** 2))
    seen = set()
    for n in range(-6, 7):
        phase = sp.simplify(sp.exp(sp.I * n * 2 * sp.pi / 3))
        matched = [r for r, root in enumerate(roots) if sp.simplify(phase - root) == 0]
        assert len(matched) == 1
        r = matched[0]
        seen.add(r)
        assert (n - r) % 3 == 0
    assert seen == {0, 1, 2}


def test_independent_lambda_degeneracy_pm_n():
    result = build_s1_c3_model(radius=2.0, hbar=3.0, n_max=4).solve()
    by_n = {int(s.quantum_numbers["n"]): s for s in result.spectrum.states}
    for n in range(-4, 5):
        expected = (n * 3.0 / 2.0) ** 2
        assert abs(by_n[n].eigenvalue.numeric() - expected) < 1e-12
        if n != 0:
            assert abs(by_n[n].eigenvalue.numeric() - by_n[-n].eigenvalue.numeric()) < 1e-12
            assert by_n[n].quantum_numbers["c3_sector"] != by_n[-n].quantum_numbers["c3_sector"] or n % 3 == 0
