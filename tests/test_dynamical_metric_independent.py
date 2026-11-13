"""Independent identities for Phase 4A dynamical metric."""

from __future__ import annotations

from pathlib import Path

import sympy as sp

from physics_lab.physics.dynamical_metric import (
    MOSTLY_MINUS,
    MOSTLY_PLUS,
    bianchi_diag,
    curvature_diagonal,
    einstein_divergence,
    eta_diag,
    flrw_diag,
)


def test_independent_minkowski_flat_both_signatures():
    t, x, y, z = sp.symbols("t x y z", real=True)
    for sig in (MOSTLY_PLUS, MOSTLY_MINUS):
        cur = curvature_diagonal(list(eta_diag(sig)), [t, x, y, z])
        assert cur["R"] == 0
        assert cur["K"] == 0
        assert cur["gauss_bonnet"] == 0
        assert cur["nondegenerate"] is True


def test_independent_flrw_R_and_G00():
    t, x, y, z = sp.symbols("t x y z", real=True)
    a = sp.Function("a")(t)
    coords = [t, x, y, z]
    plus = curvature_diagonal(flrw_diag(MOSTLY_PLUS, a), coords)
    minus = curvature_diagonal(flrw_diag(MOSTLY_MINUS, a), coords)
    ad = sp.diff(a, t)
    add = sp.diff(a, t, 2)
    assert sp.simplify(plus["R"] - 6 * (add / a + ad**2 / a**2)) == 0
    assert sp.simplify(minus["R"] + 6 * (add / a + ad**2 / a**2)) == 0
    assert sp.simplify(plus["einstein"][0][0] - 3 * ad**2 / a**2) == 0
    assert sp.simplify(minus["einstein"][0][0] - 3 * ad**2 / a**2) == 0


def test_independent_gb_total_derivative_flrw():
    t, x, y, z = sp.symbols("t x y z", real=True)
    a = sp.Function("a")(t)
    cur = curvature_diagonal(flrw_diag(MOSTLY_PLUS, a), [t, x, y, z])
    vol = a**3
    dens = sp.simplify(vol * cur["gauss_bonnet"])
    assert sp.simplify(dens - sp.diff(8 * sp.diff(a, t) ** 3, t)) == 0


def test_independent_gb_kernel_anisotropic():
    t, x, y, z = sp.symbols("t x y z", real=True)
    a = sp.Function("a")(t)
    b = sp.Function("b")(t)
    cur = curvature_diagonal(bianchi_diag(MOSTLY_PLUS, a, b), [t, x, y, z])
    vol = a * b**2
    c2, c3, c4 = sp.symbols("c2 c3 c4", real=True)
    dens = vol * (c2 * cur["R"] ** 2 + c3 * cur["Ric2"] + c4 * cur["K"])
    H = sp.simplify(sp.hessian(dens, [sp.diff(a, t, 2), sp.diff(b, t, 2)]))
    eqs = [H[0, 0], H[0, 1], H[1, 1]]
    matrix, _ = sp.linear_eq_to_matrix(eqs, [c2, c3, c4])
    nulls = matrix.nullspace()
    assert len(nulls) == 1
    vec = sp.Matrix(nulls[0])
    assert sp.simplify(vec[0] / vec[2] - 1) == 0
    assert sp.simplify(vec[1] / vec[2] + 4) == 0
    dens_gb = sp.simplify(vol * cur["gauss_bonnet"])
    assert (
        sp.simplify(dens_gb - sp.diff(8 * sp.diff(a, t) * sp.diff(b, t) ** 2, t)) == 0
    )


def test_independent_bianchi_identity():
    t, x, y, z = sp.symbols("t x y z", real=True)
    a = sp.Function("a")(t)
    coords = [t, x, y, z]
    cur = curvature_diagonal(flrw_diag(MOSTLY_PLUS, a), coords)
    assert einstein_divergence(cur, coords) == 0


def test_independent_variation_volume_and_linear_eom_order():
    from sympy.calculus.euler import euler_equations

    t = sp.symbols("t", real=True)
    a = sp.Function("a")(t)
    c0, c1 = sp.symbols("c0 c1", real=True)
    ad = sp.diff(a, t)
    add = sp.diff(a, t, 2)
    vol = a**3
    R = 6 * (add / a + ad**2 / a**2)
    el0 = euler_equations(vol * c0, a, t)[0].lhs
    assert not el0.has(sp.diff(a, t, 2))
    el1 = sp.expand(euler_equations(vol * (c0 + c1 * R), a, t)[0].lhs)
    assert el1.has(sp.diff(a, t, 2))
    assert not el1.has(sp.diff(a, t, 4))
    el2 = sp.expand(euler_equations(vol * (R**2), a, t)[0].lhs)
    assert el2.has(sp.diff(a, t, 4))


def test_independent_lovelock_slots_by_dimension():
    from physics_lab.physics.lovelock import lovelock_slot

    assert lovelock_slot(1, 2) == "topological Euler density"
    assert lovelock_slot(2, 3) == "identically zero"
    assert lovelock_slot(2, 4) == "topological Euler density"
    assert lovelock_slot(2, 5) == "local dynamical"
    assert lovelock_slot(3, 4) == "identically zero"
    assert lovelock_slot(3, 6) == "topological Euler density"


def test_independent_kronecker_vanishes_beyond_D():
    from physics_lab.physics.lovelock import antisymmetric_index_count_vanishes

    assert antisymmetric_index_count_vanishes(n_antisym=6, dimension=4) is True
    assert antisymmetric_index_count_vanishes(n_antisym=4, dimension=4) is False
    assert antisymmetric_index_count_vanishes(n_antisym=4, dimension=3) is True


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "dynamical_metric.py",
        root / "physics" / "lovelock.py",
        root / "geometry" / "lorentzian_manifold.py",
        root / "models" / "examples" / "dynamical_metric_model.py",
        root / "reporting" / "dynamical_metric_report.py",
        root / "tests" / "dynamical_metric_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
        assert "6." + "674" not in text
