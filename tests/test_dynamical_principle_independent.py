"""Independent identities for even modulus dynamics, without the analysis dict."""

from __future__ import annotations

from pathlib import Path

import sympy as sp


def test_independent_log_flips_under_inversion():
    a = sp.symbols("a", positive=True)
    x = sp.log(a)
    assert sp.simplify(sp.log(1 / a) + x) == 0


def test_independent_odd_terms_drop():
    x, c0, c2, c4 = sp.symbols("x c0 c2 c4", real=True)
    V = c0 + c2 * x**2 + c4 * x**4
    assert sp.expand(V - V.subs(x, -x)) == 0
    c1 = sp.symbols("c1", real=True)
    W = V + c1 * x
    assert sp.expand(W - W.subs(x, -x)) != 0


def test_independent_derivatives_at_origin():
    x, c2, c4 = sp.symbols("x c2 c4", real=True)
    V = c2 * x**2 + c4 * x**4
    Vp = sp.diff(V, x)
    Vpp = sp.diff(Vp, x)
    assert sp.simplify(Vp - (2 * c2 * x + 4 * c4 * x**3)) == 0
    assert sp.simplify(Vp.subs(x, 0)) == 0
    assert sp.simplify(Vpp.subs(x, 0) - 2 * c2) == 0
    assert sp.simplify(sp.diff(Vpp, x).subs(x, 0)) == 0


def test_independent_min_max_from_c2():
    x = sp.symbols("x", real=True)
    Vmin = 1 * x**2
    Vmax = -1 * x**2
    assert sp.diff(Vmin, x, 2).subs(x, 0) > 0
    assert sp.diff(Vmax, x, 2).subs(x, 0) < 0


def test_independent_bounded_quartic_does_not_fix_c2_sign():
    x = sp.symbols("x", real=True)
    # Bounded below when the quartic coefficient is positive, including a local max at 0.
    V = -1 * x**2 + 1 * x**4
    assert sp.diff(V, x, 2).subs(x, 0) < 0
    assert sp.limit(V, x, sp.oo) == sp.oo


def test_independent_affine_leaves_ratio():
    c2, c4, p, q = sp.symbols("c2 c4 p q", real=True)
    x = sp.symbols("x", real=True)
    V = c2 * x**2 + c4 * x**4
    W = p * V + q
    w2 = sp.expand(W).coeff(x, 2)
    w4 = sp.expand(W).coeff(x, 4)
    assert sp.simplify(w4 / w2 - c4 / c2) == 0


def test_independent_inequivalent_ratios():
    assert sp.simplify(sp.Integer(1) / 1 - sp.Integer(4) / 1) != 0


def test_independent_x_rescaling_changes_c4_over_c2():
    c2, c4, s, x = sp.symbols("c2 c4 s x", real=True, positive=True)
    V = c2 * x**2 + c4 * x**4
    y = sp.symbols("y", real=True, positive=True)
    W = sp.Poly(sp.expand(V.subs(x, y / s)), y)
    w2 = W.coeff_monomial(y**2)
    w4 = W.coeff_monomial(y**4)
    assert sp.simplify(w4 / w2 - c4 / c2) != 0
    assert sp.simplify(w4 / w2**2 - c4 / c2**2) == 0


def test_independent_omega_depends_on_coefficients_and_time_unit():
    c2, M, d = sp.symbols("c2 M d", positive=True)
    omega2 = 2 * c2 / M
    assert sp.simplify(omega2.subs(M, 2) - omega2.subs(M, 1)) != 0
    assert sp.simplify(omega2.subs(c2, 2) - omega2.subs(c2, 1)) != 0
    omega = sp.sqrt(omega2)
    assert sp.simplify(omega / d - omega) != 0


def test_independent_no_hardcoded_targets_or_experimental():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_principle.py",
        root / "models" / "examples" / "dynamical_principle_model.py",
        root / "reporting" / "dynamical_principle_report.py",
        root / "tests" / "dynamical_principle_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
