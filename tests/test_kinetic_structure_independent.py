"""Independent identities for kinetic structure, without the analysis dict."""

from __future__ import annotations

from pathlib import Path

import sympy as sp


def test_independent_p2_parity():
    # m+n even is the joint flip.
    assert (1 + 1) % 2 == 0
    assert (1 + 3) % 2 == 0
    assert (0 + 4) % 2 == 0
    assert (1 + 0) % 2 == 1


def test_independent_xdot4_is_second_order_not_quadratic():
    x, xd, xdd, c2, lam = sp.symbols("x xd xdd c2 lam", real=True)
    V = c2 * x**2
    L = sp.Rational(1, 2) * xd**2 + lam * xd**4 - V
    dL = sp.diff(L, xd)
    el = sp.diff(dL, xd) * xdd + sp.diff(dL, x) * xd - sp.diff(L, x)
    el = sp.simplify(el)
    assert el.has(xdd)
    assert not sp.expand(sp.diff(L, xd, 3)).equals(0)
    hess = sp.diff(L, xd, 2)
    assert not sp.expand(hess - 1).equals(0)


def test_independent_exp_hessian_positive():
    xd = sp.symbols("xd", real=True)
    L = sp.exp(xd**2)
    hess = sp.diff(L, xd, 2)
    assert sp.simplify(hess - 2 * (1 + 2 * xd**2) * sp.exp(xd**2)) == 0
    # At rest the Hessian is 2, not a selection of ẋ^2.
    assert hess.subs(xd, 0) == 2


def test_independent_legendre_l2():
    xd, lam = sp.symbols("xd lam", real=True)
    L = sp.Rational(1, 2) * xd**2 + lam * xd**4
    p = sp.diff(L, xd)
    assert sp.simplify(p - (xd + 4 * lam * xd**3)) == 0
    assert sp.simplify(sp.diff(p, xd) - sp.diff(L, xd, 2)) == 0


def test_independent_linearization_drops_quartic_velocity():
    x, xd, xdd, c2, lam = sp.symbols("x xd xdd c2 lam", real=True)
    V = c2 * x**2
    L = sp.Rational(1, 2) * xd**2 + lam * xd**4 - V
    hess = sp.diff(L, xd, 2)
    Lxx = sp.diff(L, x, 2)
    lin = hess.subs({x: 0, xd: 0}) * xdd - Lxx.subs({x: 0, xd: 0}) * x
    # lam drops out of the rest-point linearization.
    assert sp.simplify(lin - (xdd + 2 * c2 * x)) == 0
    assert lam not in lin.free_symbols


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "kinetic_structure.py",
        root / "models" / "examples" / "kinetic_structure_model.py",
        root / "reporting" / "kinetic_structure_report.py",
        root / "tests" / "kinetic_structure_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
