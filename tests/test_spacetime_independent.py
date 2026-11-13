"""Independent identities for Phase 3 spacetime structure."""

from __future__ import annotations

from pathlib import Path

import sympy as sp


def test_independent_X_both_signatures():
    phidot, g2 = sp.symbols("phidot g2", real=True)
    x_plus = -phidot**2 + g2
    x_minus = phidot**2 - g2
    assert sp.simplify(x_plus + x_minus) == 0


def test_independent_boost_leaves_X():
    pt, px, v = sp.symbols("pt px v", real=True)
    gamma = 1 / sp.sqrt(1 - v**2)
    ptp = gamma * (pt + v * px)
    pxp = gamma * (px + v * pt)
    X = -pt**2 + px**2
    Xp = -ptp**2 + pxp**2
    assert sp.simplify(Xp - X) == 0


def test_independent_nonlinear_F_still_second_order():
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")(t)
    phid = sp.diff(phi, t)
    # mostly_plus homogeneous: X = -phidot^2, F = -X/2 + lam X^2
    lam = sp.symbols("lam", real=True)
    X = -(phid**2)
    L = -X / 2 + lam * X**2
    dL = sp.diff(L, phid)
    el = sp.diff(phi, t) * 0 + sp.diff(dL, t)  # kinetic EL piece
    assert el.has(sp.diff(phi, t, 2))
    assert not el.has(sp.diff(phi, t, 4))


def test_independent_box_squared_is_fourth_order():
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")(t)
    phidd = sp.diff(phi, t, 2)
    L = phidd**2
    dL = sp.diff(L, phidd)
    el = sp.diff(dL, t, 2)
    assert el.has(sp.diff(phi, t, 4))


def test_independent_X_box_linear_in_phidd():
    t = sp.symbols("t", real=True)
    phi = sp.Function("phi")(t)
    phid = sp.diff(phi, t)
    phidd = sp.diff(phi, t, 2)
    L = (-(phid**2)) * (-phidd)
    assert sp.diff(L, phidd, 2) == 0


def test_independent_canonical_H_positive_both():
    phidot = sp.symbols("phidot", real=True)
    # mostly_plus canonical: L = 1/2 phidot^2  => H = 1/2 phidot^2
    Lp = phidot**2 / 2
    Hp = phidot * sp.diff(Lp, phidot) - Lp
    assert sp.simplify(Hp - phidot**2 / 2) == 0
    # mostly_minus adapted canonical is the same L in 1+0 split
    Lm = phidot**2 / 2
    Hm = phidot * sp.diff(Lm, phidot) - Lm
    assert sp.simplify(Hp - Hm) == 0


def test_independent_m2_classes():
    def cls(m2: float) -> str:
        if m2 > 0:
            return "ordinary_m2"
        if m2 < 0:
            return "tachyonic_m2"
        return "vanishing_m2"

    assert cls(1) == "ordinary_m2"
    assert cls(0) == "vanishing_m2"
    assert cls(-1) == "tachyonic_m2"


def test_independent_euclidean_not_lorentzian():
    eucl = (1, 1, 1, 1)
    plus = (-1, 1, 1, 1)
    minus = (1, -1, -1, -1)
    assert eucl != plus
    assert eucl != minus


def test_independent_adapted_canonical_is_hyperbolic_both():
    phidot, g2 = sp.symbols("phidot g2", real=True)
    # mostly_plus: X = -phidot^2 + g2, L = -X/2 = phidot^2/2 - g2/2
    Lplus = -(-phidot**2 + g2) / 2
    # mostly_minus: X = phidot^2 - g2, L = +X/2 = phidot^2/2 - g2/2
    Lminus = (phidot**2 - g2) / 2
    target = phidot**2 / 2 - g2 / 2
    assert sp.simplify(Lplus - target) == 0
    assert sp.simplify(Lminus - target) == 0


def test_independent_unadapted_minus_flips_H():
    phidot = sp.symbols("phidot", real=True)
    # mixed: F = -X/2 with mostly_minus X = +phidot^2
    L = -phidot**2 / 2
    H = phidot * sp.diff(L, phidot) - L
    assert sp.simplify(H + phidot**2 / 2) == 0


def test_independent_nonlinear_X_survives_redefinition():
    t, a = sp.symbols("t a", real=True)
    psi = sp.Function("psi")(t)
    phi = a * psi  # local linear chart, a>0 constant
    Xpsi = sp.diff(psi, t) ** 2
    Xphi = sp.diff(phi, t) ** 2
    assert sp.simplify(Xphi - a**2 * Xpsi) == 0
    assert sp.simplify(Xphi**2 - a**4 * Xpsi**2) == 0


def test_independent_L5_hessian_eom_ibp_both_signatures():
    from sympy.calculus.euler import euler_equations

    t, x = sp.symbols("t x", real=True)
    phi = sp.Function("phi")(t, x)
    pt = sp.diff(phi, t)
    px = sp.diff(phi, x)
    ptt = sp.diff(phi, t, 2)
    ptx = sp.diff(phi, t, x)
    pxx = sp.diff(phi, x, 2)
    cases = (
        (-1, 1),
        (1, -1),
    )
    els = []
    for e0, e1 in cases:
        X = e0 * pt**2 + e1 * px**2
        box = e0 * ptt + e1 * pxx
        L = X * box
        ptt_s, ptx_s, pxx_s, pt_s, px_s = sp.symbols("ptt ptx pxx pt px", real=True)
        Ljet = L.subs({ptt: ptt_s, ptx: ptx_s, pxx: pxx_s, pt: pt_s, px: px_s})
        H = sp.hessian(Ljet, [ptt_s, ptx_s, pxx_s])
        assert H == sp.zeros(3)
        el = sp.expand(euler_equations(L, phi, [t, x])[0].lhs)
        max_order = max(len(d.variables) for d in el.atoms(sp.Derivative))
        assert max_order == 2
        dt_up = e0 * pt
        dx_up = e1 * px
        div = sp.diff(X * dt_up, t) + sp.diff(X * dx_up, x)
        contract = dt_up**2 * ptt + 2 * dt_up * dx_up * ptx + dx_up**2 * pxx
        assert sp.simplify(L - div + 2 * contract) == 0
        els.append(sp.simplify(el))
    assert sp.simplify(els[0] - els[1]) == 0


def test_independent_epsilon_four_copies_vanishes():
    v = sp.symbols("v0 v1 v2 v3", real=True)
    s = 0
    for a in range(4):
        for b in range(4):
            for c in range(4):
                for d in range(4):
                    s += int(sp.LeviCivita(a, b, c, d)) * v[a] * v[b] * v[c] * v[d]
    assert sp.simplify(s) == 0


def test_independent_no_hardcoded_targets():
    root = Path(__file__).resolve().parents[1] / "src" / "physics_lab"
    files = [
        root / "physics" / "spacetime.py",
        root / "geometry" / "minkowski.py",
        root / "models" / "examples" / "spacetime_model.py",
        root / "reporting" / "spacetime_report.py",
        root / "tests" / "spacetime_test.py",
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "1/" + "3" not in text
        assert "137" not in text
        assert "from physics_lab.physics.constants" not in text
        assert "ALPHA" not in text
