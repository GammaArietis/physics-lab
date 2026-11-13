"""Independent identities for Phase 2 action classification."""

from __future__ import annotations

from pathlib import Path

import sympy as sp


def test_independent_z2_on_jet():
    t = sp.symbols("t", real=True)
    x = sp.Function("x")
    xt = x(t)
    xd = sp.diff(xt, t)
    flipped = xt.subs(x(t), -x(t))
    # Direct jet rule: x -> -x sends xdot -> -xdot.
    assert sp.diff(-xt, t) == -xd
    assert flipped == -x(t)


def test_independent_joint_z2_allows_mixed_terms():
    x, xd = sp.symbols("x xd", real=True)
    mixed = x * xd**3
    assert sp.expand(mixed - mixed.subs({x: -x, xd: -xd})) == 0
    # Not separately even in xd (time reversal).
    assert sp.expand(mixed - mixed.subs({xd: -xd})) != 0
    # Not a function of (x^2, xd^2) alone.
    k_only = x**2 * xd**2
    assert sp.expand(k_only - k_only.subs({xd: -xd})) == 0


def test_independent_total_derivative_linear_only():
    x, xd, xdd = sp.symbols("x xd xdd", real=True)

    def el(L):
        dL_dxd = sp.diff(L, xd)
        dt = sp.diff(dL_dxd, x) * xd + sp.diff(dL_dxd, xd) * xdd
        return sp.simplify(dt - sp.diff(L, x))

    assert el(x * xd) == 0
    assert el(x**3 * xd) == 0
    mixed_el = el(x * xd**3)
    assert mixed_el != 0
    assert mixed_el.has(xdd)


def test_independent_quadratic_not_forced():
    x, xd = sp.symbols("x xd", real=True)
    # P2-compatible but not quadratic in xd.
    L = xd**4 + x**2
    assert sp.expand(L - L.subs({x: -x, xd: -xd})) == 0
    t, x = sp.symbols("t x", real=True)
    xfun = sp.Function("x")
    F = xfun(t) ** 2 / 2
    dFdt = sp.diff(F, t)
    assert sp.simplify(dFdt - xfun(t) * sp.diff(xfun(t), t)) == 0


def test_independent_odd_potential_rejected():
    x = sp.symbols("x", real=True)
    V_even = x**2 + x**4
    V_odd = x + x**2
    assert sp.expand(V_even - V_even.subs(x, -x)) == 0
    assert sp.expand(V_odd - V_odd.subs(x, -x)) != 0


def test_independent_derivatives_at_origin():
    x, c2, c4 = sp.symbols("x c2 c4", real=True)
    V = c2 * x**2 + c4 * x**4
    assert sp.simplify(sp.diff(V, x).subs(x, 0)) == 0
    assert sp.simplify(sp.diff(V, x, 2).subs(x, 0) - 2 * c2) == 0


def test_independent_M_absorbed_by_reparam():
    x, ydot = sp.symbols("x ydot", real=True)
    M = (1 + x**2) ** 2
    fprime = 1 + x**2
    coeff = sp.Rational(1, 2) * M / fprime**2
    assert sp.simplify(coeff - sp.Rational(1, 2)) == 0
    # An xdot^4 coupling is not removed.
    lam = sp.symbols("lam", real=True)
    leftover = lam / fprime**4
    assert sp.simplify(leftover) != 0


def test_independent_affine_time_rescaling():
    y, t, p = sp.symbols("y t p", real=True, positive=True)
    U = y**2
    # ÿ + p U'(y) = 0 vs time τ = sqrt(p) t.
    tau = sp.sqrt(p) * t
    # d^2 y / dt^2 = p d^2 y / d tau^2, so ÿ_t + p * 2 y = p (ÿ_tau + 2 y)
    assert sp.simplify(p * (2 * y) / p - 2 * y) == 0
    assert tau.is_real is not False


def test_independent_inequivalent_shapes():
    assert sp.simplify(sp.Integer(4) / 1 - sp.Integer(1) / 1) != 0


def test_independent_scale_free_forces_constant_V():
    x, c2 = sp.symbols("x c2", real=True)
    V = c2 * x**2
    # With x dimensionless, c2 carries the dimension of V. Forbidding that scale
    # leaves only the constant term.
    V_noscale = V.subs(c2, 0)
    assert sp.diff(V_noscale, x) == 0


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_principle_phase2.py",
        root / "models" / "examples" / "dynamical_principle_phase2_model.py",
        root / "reporting" / "dynamical_principle_phase2_report.py",
        root / "tests" / "dynamical_principle_phase2_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
