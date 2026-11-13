"""Kinetic-structure test: does any declared principle force ẋ²?

Starts from the general P2 class, then P2+P9.  Does not take a quadratic
kinetic term as the starting point.  λ is an INPUT probe, not chosen for
stability.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active


def euler_lagrange(L: Any, x: Any, xdot: Any, xddot: Any) -> Any:
    dL_dxdot = sp.diff(L, xdot)
    dt = sp.diff(dL_dxdot, x) * xdot + sp.diff(dL_dxdot, xdot) * xddot
    return sp.simplify(sp.expand(dt - sp.diff(L, x)))


def kinetic_hessian(L: Any, xdot: Any) -> Any:
    return sp.simplify(sp.diff(L, xdot, 2))


def canonical_momentum(L: Any, xdot: Any) -> Any:
    return sp.simplify(sp.diff(L, xdot))


def eom_order(el: Any, xddot: Any, xdddot: Any | None = None) -> int:
    if xdddot is not None and el.has(xdddot):
        return 3
    if el.has(xddot):
        return 2
    return 1


def is_first_order_total_derivative(L: Any, x: Any, xdot: Any) -> bool:
    xddot = sp.symbols("xddot_probe")
    return sp.simplify(euler_lagrange(L, x, xdot, xddot)) == 0


def classify_monomial(m: int, n: int) -> dict[str, Any]:
    """Classify a_mn x^m xdot^n under P2 and under P2+P9."""
    p2_ok = ((m + n) % 2) == 0
    p9_ok = (n % 2) == 0
    even_x = (m % 2) == 0
    p2p9_ok = p2_ok and p9_ok and even_x
    td = n == 1

    def status(*, allowed: bool, td_flag: bool) -> str:
        if not allowed:
            return "forbidden"
        if td_flag:
            return "total derivative"
        return "allowed"

    return {
        "m": m,
        "n": n,
        "term": f"x^{m} xdot^{n}" if m or n else "const",
        "P2": status(allowed=p2_ok, td_flag=p2_ok and td),
        "P2_P9": status(allowed=p2p9_ok, td_flag=False if not p2p9_ok else td),
        "total_derivative": "YES" if td and p2_ok else ("NO" if not td else "YES but forbidden by P2"),
    }


def monomial_table(max_power: int = 4) -> list[dict[str, Any]]:
    rows = []
    for m in range(max_power + 1):
        for n in range(max_power + 1):
            rows.append(classify_monomial(m, n))
    return rows


def example_lagrangians(*, c2: Any, lam: Any) -> dict[str, Any]:
    x, xdot = sp.symbols("x xdot", real=True)
    V = c2 * x**2
    L1 = sp.Rational(1, 2) * xdot**2 - V
    L2 = sp.Rational(1, 2) * xdot**2 + lam * xdot**4 - V
    L3 = sp.exp(xdot**2) - V
    return {"x": x, "xdot": xdot, "V": V, "L1": L1, "L2": L2, "L3": L3}


def analyze_example(name: str, L: Any, x: Any, xdot: Any, *, lam: Any | None = None) -> dict[str, Any]:
    xddot = sp.symbols("xddot", real=True)
    el = euler_lagrange(L, x, xdot, xddot)
    hess = kinetic_hessian(L, xdot)
    p = canonical_momentum(L, xdot)
    dp = sp.simplify(sp.diff(p, xdot))
    order = eom_order(el, xddot)
    tr = sp.simplify(sp.expand(L - L.subs(xdot, -xdot))) == 0
    joint = sp.simplify(sp.expand(L - L.subs({x: -x, xdot: -xdot}))) == 0
    hess0 = sp.simplify(hess.subs({x: 0, xdot: 0}))
    Lxx0 = sp.simplify(sp.diff(L, x, 2).subs({x: 0, xdot: 0}))
    # Linearized EL at (0,0): hess(0,0) xddot - L_xx(0,0) x = 0
    lin = sp.simplify(hess0 * xddot - Lxx0 * x)
    H = sp.simplify(p * xdot - L)
    cubic = sp.simplify(sp.diff(L, xdot, 3))
    is_quad = bool(sp.expand(cubic).equals(0))
    nondeg_identically = not bool(sp.expand(hess).equals(0))
    hess0_nonzero = not bool(sp.expand(hess0).equals(0))
    return {
        "name": name,
        "L": str(L),
        "time_reversal": "YES" if tr else "NO",
        "joint_P2": "YES" if joint else "NO",
        "eom_order": order,
        "EL": str(el),
        "hessian": str(hess),
        "hessian_at_rest": str(hess0),
        "momentum": str(p),
        "dp_dxdot": str(dp),
        "legendre_nondeg_identical": nondeg_identically,
        "legendre_nondeg_at_rest": hess0_nonzero,
        "quadratic_in_xdot": is_quad,
        "linearized_EL": str(lin),
        "static_curvature_Lxx0": str(Lxx0),
        "hamiltonian": str(H),
        "lam_probe": str(lam) if lam is not None else None,
    }


def coordinate_canonicalization() -> dict[str, str]:
    return {
        "applies_to": "only L=(1/2) M(x) xdot^2 - V(x) with M(x)>0",
        "local": "M>0 on a neighborhood; y=Integral sqrt(M) dx is a local chart change",
        "global_on_R": "M(x)>0 for all real x and the integral a diffeomorphism of R. Not automatic.",
        "coordinate": "M(x) is then chart redundancy",
        "dynamical": "V becomes U(y); higher xdot powers are NOT removed by y=f(x)",
        "L2_L3": "xdot^4 and exp(xdot^2) survive any y=f(x). Not coordinate-equivalent to L1.",
    }


def analyze_kinetic_structure() -> dict[str, Any]:
    c2, lam = sp.symbols("c2 lam", real=True)
    ex = example_lagrangians(c2=c2, lam=lam)
    x, xdot = ex["x"], ex["xdot"]
    a1 = analyze_example("L1", ex["L1"], x, xdot)
    a2 = analyze_example("L2", ex["L2"], x, xdot, lam=lam)
    a3 = analyze_example("L3", ex["L3"], x, xdot)
    # Explicit counterexample: second-order EOM but not quadratic.
    implication_false = (a2["eom_order"] == 2) and (not a2["quadratic_in_xdot"])
    hess_pos_not_quad = (not a3["quadratic_in_xdot"]) and a3["legendre_nondeg_identical"]
    table = monomial_table(4)
    p2_allowed = [r for r in table if r["P2"] != "forbidden"]
    p2p9_allowed = [r for r in table if r["P2_P9"] != "forbidden"]
    conclusion = (
        "P2 allows all monomials with m+n even, including mixed odd-odd terms. "
        "P2+P9 keeps even-even monomials only: K(x^2, xdot^2). Neither time reversal, "
        "second-order EOM, Legendre non-degeneracy, nor a positive kinetic Hessian "
        "forces a purely quadratic kinetic term. L2 and L3 are counterexamples. "
        "quadratic kinetic term = ADDITIONAL ASSUMPTION / NOT SELECTED. "
        "Linearized rest-point dynamics still uses Hessian(0,0) and L_xx(0,0); "
        "higher xdot couplings drop from the linearization but remain genuine nonlinearly."
    )
    return {
        "general_p2_class": "L(x,xdot)=L(-x,-xdot)=K(x^2,xdot^2)+x xdot W(x^2,xdot^2)",
        "p2_time_reversal": "L(x,xdot)=K(x^2,xdot^2)  [P9 additional]",
        "second_order_eom": (
            "For any L(x,xdot) with Hessian != 0, EL is second order. "
            "Second-order EOM does not imply a quadratic kinetic term. "
            f"Counterexample L2: order={a2['eom_order']}, quadratic={a2['quadratic_in_xdot']}."
        ),
        "nondegenerate_legendre": (
            "det(dp/dxdot)=d^2 L/dxdot^2. Non-vanishing selects invertibility of (x,xdot)->(x,p), "
            "not quadraticity. L3 has Hessian=2(1+2 xdot^2)exp(xdot^2)>0 and is not quadratic."
        ),
        "positive_kinetic_hessian": (
            "Hessian>0 is kinetic stability / no ghost, and does not force ẋ^2. "
            "L2 with lam>0 and L3 satisfy it without being quadratic."
        ),
        "quadratic_kinetic_term": "NOT SELECTED",
        "quadratic_status": "ADDITIONAL ASSUMPTION",
        "coordinate_canonicalization": coordinate_canonicalization(),
        "static_stability_criterion": (
            "For L=T(xdot)-V(x) with V even: V'(0)=0, static test is sign of V''(0)=2 c2. "
            "c2 remains INPUT."
        ),
        "full_dynamical_stability": (
            "Linearized at rest: L_xdotxdot(0,0) xddot - L_xx(0,0) x = 0. "
            "Higher xdot couplings drop. Nonlinearly they remain: if lam<0, L2 Hessian can vanish "
            "at finite speed, so full dynamical solvability is not the same as V''(0)>0."
        ),
        "remaining_functional_freedom": (
            "After P2+P9: free K(x^2,xdot^2). After Hessian>0: still an infinite class "
            "(L1, L2 with lam>0, L3, ...). Quadratic form is a slice of that class."
        ),
        "unique_dynamics": "NO",
        "implication_second_order_to_quadratic": "FALSE" if implication_false else "TRUE",
        "hessian_positive_selects_quadratic": "NO" if hess_pos_not_quad else "UNCHECKED",
        "time_reversal_selects_quadratic": "NO",
        "legendre_selects_quadratic": "NO",
        "minimal_combination_for_quadratic": "NONE among the declared principles",
        "how_much_is_assumed": (
            "The entire restriction from K(x^2,xdot^2) with Hessian>0 down to "
            "(1/2) M(x) xdot^2 - V(x) is an ADDITIONAL ASSUMPTION."
        ),
        "stability_modified_for_general_class": (
            "Linear rest-point criterion is unchanged in form (Hessian(0,0) and L_xx(0,0)). "
            "It is incomplete for the general class: nonlinear kinetic terms can destroy "
            "global invertibility or boundedness without changing V''(0)."
        ),
        "monomials": table,
        "p2_allowed_count": len(p2_allowed),
        "p2p9_allowed_count": len(p2p9_allowed),
        "examples": {"L1": a1, "L2": a2, "L3": a3},
        "probes": {
            "c2": "INPUT / free sign",
            "lam": "INPUT, not chosen for stability",
        },
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Kinetic-structure analysis must run inside DerivationContext.")
