"""Phase 2: admissible first-order actions for the modulus, without choosing V.

Classifies Lagrangians compatible with declared principles, removes coordinate
and affine redundancies, and counts leftover freedoms.  Does not select a law.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active


def principles() -> list[dict[str, str]]:
    return [
        {
            "name": "P1 temporal locality",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Action depends on x(t) and finitely many time derivatives.",
        },
        {
            "name": "P2 symmetry x -> -x",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Inherited from a -> 1/a. Not re-derived here.",
        },
        {
            "name": "P3 reality",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Lagrangian is a real function.",
        },
        {
            "name": "P4 first-order time derivatives in L",
            "status": "PRINCIPLE / ASSUMED",
            "note": "L = L(x, xdot). Higher jets are a larger class, not forced.",
        },
        {
            "name": "P5 kinetic stability (no ghost)",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Quadratic kinetic coefficient M(x) > 0. Not implied by x -> -x.",
        },
        {
            "name": "P6 no artificial-coordinate dependence",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Invertible y=f(x) is a chart change on the modulus, not new physics.",
        },
        {
            "name": "P7 no term inserted only to create a minimum",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Methodological stop: do not enlarge L to force U''(0)>0.",
        },
        {
            "name": "P8 no external dimensionful scale",
            "status": "ASSUMED OPTION",
            "note": "Separate branch. Not assumed to be required.",
        },
        {
            "name": "P9 time-reversal t -> -t, x(t) -> x(-t)",
            "status": "ADDITIONAL PRINCIPLE / ASSUMED",
            "note": "Implies xdot -> -xdot at fixed x. Not imposed by P1-P4. Needed for L=K(x^2, xdot^2).",
        },
    ]


def z2_flips_velocity(x: Any, xdot: Any) -> bool:
    """x(t) -> -x(t) sends (x, xdot) -> (-x, -xdot)."""
    return True


def lagrangian_even_under_z2(expr: Any, x: Any, xdot: Any) -> bool:
    """P2 on the first-order jet: L(x, xdot) = L(-x, -xdot)."""
    flipped = expr.subs({x: -x, xdot: -xdot})
    return sp.simplify(sp.expand(expr - flipped)) == 0


def even_under_time_reversal(expr: Any, x: Any, xdot: Any) -> bool:
    """P9: L(x, xdot) = L(x, -xdot). Not implied by P2."""
    flipped = expr.subs({xdot: -xdot})
    return sp.simplify(sp.expand(expr - flipped)) == 0


def euler_lagrange(L: Any, x: Any, xdot: Any, xddot: Any) -> Any:
    """EL operator d/dt(∂L/∂xdot) - ∂L/∂x, staying inside first-order L."""
    dL_dxdot = sp.diff(L, xdot)
    dt = sp.diff(dL_dxdot, x) * xdot + sp.diff(dL_dxdot, xdot) * xddot
    return sp.simplify(sp.expand(dt - sp.diff(L, x)))


def is_first_order_total_derivative(L: Any, x: Any, xdot: Any) -> bool:
    """True iff L differs from a function of x by g(x) xdot = dF(x)/dt.

    Higher odd powers of xdot are not dF(x)/dt.  They would require F(x, xdot)
    and would introduce xddot, leaving P4.
    """
    xddot = sp.symbols("xddot_probe")
    el = euler_lagrange(L, x, xdot, xddot)
    return sp.simplify(el) == 0


def monomial_catalog() -> list[dict[str, Any]]:
    """Explicit probes of joint Z2 vs total-derivative status."""
    x, xdot = sp.symbols("x xdot", real=True)
    specs = [
        ("x xdot", x * xdot),
        ("x^3 xdot", x**3 * xdot),
        ("x xdot^3", x * xdot**3),
        ("x^2 xdot^2", x**2 * xdot**2),
    ]
    rows = []
    for name, term in specs:
        rows.append(
            {
                "term": name,
                "symmetry_compatible": "YES" if lagrangian_even_under_z2(term, x, xdot) else "NO",
                "time_reversal": "YES" if even_under_time_reversal(term, x, xdot) else "NO",
                "in_K_x2_xdot2": "YES" if even_under_time_reversal(term, x, xdot) and lagrangian_even_under_z2(term, x, xdot) else "NO",
                "total_derivative": "YES" if is_first_order_total_derivative(term, x, xdot) else "NO",
            }
        )
    return rows


def linear_velocity_is_total_derivative(g: Any, x: Any, xdot: Any) -> bool:
    """g(x) xdot = dF/dt for F' = g.  It does not affect the EOM."""
    F = sp.integrate(g, x)
    dFdt = sp.diff(F, x) * xdot
    return sp.simplify(sp.expand(g * xdot - dFdt)) == 0


def even_potential_class(x: Any) -> str:
    """Global class DERIVED from P2: V(x)=F(x^2). Taylor is the local form."""
    return "V(x)=F(x^2)  (global);  V=c0+c2 x^2+c4 x^4+...  (local Taylor)"


def quadratic_lagrangian(M: Any, V: Any, xdot: Any) -> Any:
    return (sp.Rational(1, 2) * M * xdot**2) - V


def transformed_kinetic_coefficient(M: Any, fprime: Any) -> Any:
    """y=f(x) sends (1/2) M xdot^2 to (1/2) (M/f'^2) ydot^2."""
    return sp.simplify(M / fprime**2)


def kinetic_can_be_canonicalized(M: Any, fprime: Any) -> bool:
    return sp.simplify(transformed_kinetic_coefficient(M, fprime) - 1) == 0


def quartic_velocity_after_reparam(lam: Any, fprime: Any) -> Any:
    """lambda(x) xdot^4 becomes lambda/f'^4 ydot^4.  Not removed by y=f(x)."""
    return sp.simplify(lam / fprime**4)


def curvature_even_potential(V: Any, x: Any) -> tuple[Any, Any]:
    Vp = sp.diff(V, x)
    Vpp = sp.diff(Vp, x)
    return sp.simplify(Vp.subs(x, 0)), sp.simplify(Vpp.subs(x, 0))


def classify_stability_curvature(vpp0: Any) -> str:
    val = sp.sympify(vpp0)
    if val.is_number:
        num = float(val)
        if num > 0:
            return "stable minimum"
        if num < 0:
            return "unstable"
        return "flat direction / marginal"
    return "parameter-dependent"


def affine_same_eom(p: Any) -> str:
    """U -> p U + q. Offset q always drops. p>0 is a time-unit rescaling."""
    p = sp.sympify(p)
    if p.is_number:
        num = float(p)
        if num > 0:
            return "equivalent_by_energy_scale_and_offset"
        if num < 0:
            return "inequivalent_stability_flip"
        return "degenerate"
    return "parameter-dependent"


def polynomial_shape_ratios(coeffs: dict[int, Any]) -> dict[str, Any]:
    """Dimensionless ratios c_{2k}/c2 at fixed x=log a. Empty if c2=0."""
    c2 = sp.sympify(coeffs.get(2, 0))
    if c2 == 0:
        return {}
    out: dict[str, Any] = {}
    for k, ck in coeffs.items():
        if k <= 2:
            continue
        out[f"c{k}/c2"] = sp.simplify(sp.sympify(ck) / c2)
    return out


def same_shape_quartic(c2_a: Any, c4_a: Any, c2_b: Any, c4_b: Any) -> bool:
    a2, a4, b2, b4 = (sp.sympify(v) for v in (c2_a, c4_a, c2_b, c4_b))
    if a2 == 0 or b2 == 0:
        return sp.simplify(a2 - b2) == 0 and sp.simplify(a4 - b4) == 0
    return sp.simplify(a4 / a2 - b4 / b2) == 0


def equivalence_kind(*, same_canonical_U: bool, affine: str) -> str:
    if same_canonical_U:
        return "equivalent_by_coordinate_transformation"
    if affine == "equivalent_by_energy_scale_and_offset":
        return "equivalent_by_energy_scale_and_offset"
    return "genuinely_inequivalent_dynamics"


def scale_free_branch() -> dict[str, str]:
    """P8 as a separate option. x is dimensionless (log a)."""
    return {
        "status": "ASSUMED OPTION",
        "V": "must be constant: every c_{2k}, k>=1, is dimensionful",
        "M": "M has dimension energy*time^2; forbidding scales removes it or treats it as a time-unit CONVENTION",
        "stable_isolated_vacuum": "NO",
        "characteristic_scale": "NO",
        "flat_modulus": "YES",
        "dimensionless_ratio": "NONE (no couplings left to ratio)",
        "nontrivial_dynamics": "NO",
        "unique_dynamics": "NO",
        "predictivity": (
            "More constrained (trivial/flat) but it does not select a unique "
            "non-trivial law. Dynamical content decreases. Unique prediction still NO."
        ),
    }


def minimality_criteria() -> list[dict[str, str]]:
    return [
        {
            "name": "minimum derivative order",
            "status": "ASSUMED (P4)",
            "unique_dynamics": "NO",
            "note": "First-order L is a restriction of class A, not a derivation.",
        },
        {
            "name": "minimum number of free functions",
            "status": "ASSUMED (P9, then drop xdot^{2k} for k>1, then P6)",
            "unique_dynamics": "NO",
            "note": "P9 reduces to K(x^2,xdot^2). Quadratic velocity is a further ASSUMPTION. U remains free.",
        },
        {
            "name": "minimum number of free parameters",
            "status": "MINIMALITY ASSUMPTION",
            "unique_dynamics": "NO",
            "note": "Taylor truncation is not DERIVED. Finite polynomials still have free ratios.",
        },
    ]


def class_census() -> dict[str, dict[str, str]]:
    return {
        "A": {
            "description": "P1-P4 only",
            "most_general_L": "L(x,xdot)=L(-x,-xdot) = K(x^2,xdot^2) + x xdot W(x^2,xdot^2)",
            "free_functions": "K and W, or one F(x^2, xdot^2, x xdot)",
            "free_coefficients": "all compatible Taylor coefficients of K and W",
            "symmetry_assumptions": "P2 joint flip (x,xdot)->(-x,-xdot). Not L(x,xdot)=L(x,-xdot).",
            "additional_assumptions": "none beyond P1-P4",
            "coordinate_redundancies": "A(x) xdot with A odd is dF/dt and drops from the EOM (boundary aside)",
            "stability_freedom": "PARAMETER-DEPENDENT",
            "uniqueness": "NO",
        },
        "B": {
            "description": "P1-P4 + P9 time reversal",
            "most_general_L": "L(x,xdot)=K(x^2, xdot^2)",
            "free_functions": "one function K of two even arguments",
            "free_coefficients": "Taylor coefficients of K",
            "symmetry_assumptions": "P2 and P9 (xdot -> -xdot at fixed x)",
            "additional_assumptions": "P9 ADDITIONAL PRINCIPLE / ASSUMED",
            "coordinate_redundancies": "linear-in-xdot terms already absent by P9 (or are total derivatives)",
            "stability_freedom": "PARAMETER-DEPENDENT",
            "uniqueness": "NO",
        },
        "C": {
            "description": "Class B + quadratic kinetic term",
            "most_general_L": "L=(1/2) M(x) xdot^2 - V(x) with M even, V even",
            "free_functions": "two even functions M, V; after P5+P6 locally one even U",
            "free_coefficients": "even Taylor coefficients of M and V; shape of U after gauge",
            "symmetry_assumptions": "P2 and P9",
            "additional_assumptions": "quadratic in xdot is ADDITIONAL ASSUMPTION; P5 M>0",
            "coordinate_redundancies": (
                "If M>0 locally, y=Integral sqrt(M) dx canonicalizes the kinetic term. "
                "Global on x in R only if M(x)>0 for all real x and the integral is a diffeomorphism of R."
            ),
            "stability_freedom": "sign of V''(0) is free",
            "uniqueness": "NO",
        },
    }


def canonicalization_domain() -> dict[str, str]:
    return {
        "local": "Requires M(x)>0 on a neighborhood, so f'=sqrt(M) is real and nonzero.",
        "global_on_R": (
            "Requires M(x)>0 for every real x and Integral_0^x sqrt(M) a C1 diffeomorphism "
            "R->R (f' never zero, |f|->infinity as |x|->infinity). Not automatic from evenness of M."
        ),
        "status": "coordinate redundancy of class C, after the quadratic ASSUMPTION and P5",
    }


def dimensional_table() -> list[list[str]]:
    return [
        ["x = log a", "dimensionless", "chart CONVENTION"],
        ["t", "time", "external unit CONVENTION"],
        ["xdot", "1/time", "derived"],
        ["M(x)", "energy * time^2", "dimensionful; redundant by P6 if M>0"],
        ["V(x) or U(y)", "energy", "dimensionful function; genuine after P6"],
        ["c0", "energy", "offset CONVENTION"],
        ["c2, c4, ...", "energy", "dimensionful coefficients (x dimensionless)"],
        ["c4/c2", "dimensionless", "PARAMETER / shape; not fixed"],
        ["c4/c2^2", "1/energy", "not a pure number at dimensionless x"],
    ]


def numerical_family_examples() -> list[dict[str, Any]]:
    """INPUT probes. Coefficients are not chosen to manufacture a minimum."""
    x = sp.symbols("x", real=True)
    probes = [
        {"c2": 1, "c4": 1, "c6": 0},
        {"c2": 1, "c4": 4, "c6": 0},
        {"c2": -2, "c4": 1, "c6": 0},
        {"c2": 2, "c4": 3, "c6": 5},
        {"c2": -1, "c4": -1, "c6": 0},
    ]
    rows = []
    for p in probes:
        V = p["c2"] * x**2 + p["c4"] * x**4 + p["c6"] * x**6
        vp0, vpp0 = curvature_even_potential(V, x)
        rows.append(
            {
                "c2": p["c2"],
                "c4": p["c4"],
                "c6": p["c6"],
                "Vprime0": str(vp0),
                "Vsecond0": str(vpp0),
                "stability": classify_stability_curvature(vpp0),
                "ratios": {k: str(v) for k, v in polynomial_shape_ratios({2: p["c2"], 4: p["c4"], 6: p["c6"]}).items()},
                "provenance": "INPUT probe, not a selected law",
            }
        )
    return rows


def leftover_after_redundancy() -> dict[str, str]:
    return {
        "coordinate_redundancy": (
            "After the quadratic ASSUMPTION and P5, M(x)>0 even can be set to 1 locally "
            "by y=Integral sqrt(M) dx, odd when M is even. Global on R is extra."
        ),
        "affine_redundancy": "U -> p U + q with p>0 is time-unit + offset. q never enters the EOM.",
        "genuine_dynamical_freedom": (
            "Class A: K and W. Class B: K. Class C: even U (and sign of U''(0)). "
            "Linear A(x) xdot with A odd is not genuine: it is dF/dt."
        ),
        "convention": "c0; overall positive scale of U once the time unit is free; chart y vs x",
        "not_convention": "sign(U''(0)); inequivalent shapes of U; W in class A; higher even velocities in class B",
    }


def analyze_phase2() -> dict[str, Any]:
    x, xdot = sp.symbols("x xdot", real=True)
    c0, c2, c4 = sp.symbols("c0 c2 c4", real=True)
    V = c0 + c2 * x**2 + c4 * x**4
    vp0, vpp0 = curvature_even_potential(V, x)
    M0 = sp.symbols("M0", positive=True)
    M_even = (1 + x**2) ** 2
    fprime_const = sp.sqrt(M0)
    fprime_even = 1 + x**2
    kin_ok_const = kinetic_can_be_canonicalized(M0, fprime_const)
    kin_ok_even = kinetic_can_be_canonicalized(M_even, fprime_even)
    lam = sp.symbols("lam", real=True)
    leftover_quartic_vel = quartic_velocity_after_reparam(lam, fprime_even)
    g_odd = x
    total_der = linear_velocity_is_total_derivative(g_odd, x, xdot)
    L_quad = quadratic_lagrangian(M0, V, xdot)
    even_L = lagrangian_even_under_z2(L_quad, x, xdot)
    catalog = monomial_catalog()
    mixed = next(row for row in catalog if row["term"] == "x xdot^3")
    xxdot = next(row for row in catalog if row["term"] == "x xdot")
    examples = numerical_family_examples()
    inequivalent = not same_shape_quartic(1, 1, 1, 4)
    census = class_census()
    conclusion = (
        "P1-P4 imply L(x,xdot)=L(-x,-xdot), i.e. L=K(x^2,xdot^2)+x xdot W(x^2,xdot^2), "
        "not L=K(x^2,xdot^2). The latter needs P9 time-reversal, an ADDITIONAL PRINCIPLE. "
        "L=(1/2) M(x) xdot^2 - V(x) is an ADDITIONAL ASSUMPTION. Only linear A(x) xdot "
        "is a first-order total derivative. Mixed terms such as x xdot^3 are P2-compatible "
        "and dynamically relevant. Linear stability of x=0 is still PARAMETER-DEPENDENT: "
        "the sign of V''(0) is not selected. Unique dynamics: NO."
    )
    return {
        "degrees_of_freedom": "one modulus coordinate x(t)=log a(t) in R",
        "declared_principles": principles(),
        "general_allowed_lagrangian": (
            "Class A (P1-P4): L=K(x^2,xdot^2)+x xdot W(x^2,xdot^2). "
            "Class B (plus P9): L=K(x^2,xdot^2). "
            "Class C (plus quadratic ASSUMPTION): L=(1/2) M(x) xdot^2 - V(x), M,V even."
        ),
        "k_derived_from_p1p4": "NO",
        "principle_for_K": "P9 time-reversal, ADDITIONAL PRINCIPLE / ASSUMED",
        "quadratic_status": "ADDITIONAL ASSUMPTION",
        "previous_eliminations": (
            "Only terms A(x) xdot = dF(x)/dt, including x xdot and x^3 xdot. "
            "Not every term odd in xdot is a total derivative: x xdot^3 is not."
        ),
        "stability_changed": "NO",
        "coordinate_redundancies": leftover_after_redundancy()["coordinate_redundancy"],
        "equivalent_actions": (
            "y=f(x) invertible after the quadratic ASSUMPTION and M>0 locally; "
            "U -> p U + q with p>0; linear-in-xdot total derivatives."
        ),
        "genuine_dynamical_freedoms": leftover_after_redundancy()["genuine_dynamical_freedom"],
        "free_functions": "Class A: K and W. Class B: K. Class C: even U after local kinetic gauge.",
        "free_dimensionless_parameters": "shape of U (c4/c2, c6/c2, ...); none of them fixed",
        "free_dimensionful_parameters": "scale of U if time is held fixed; M(x) is chart-redundant when M>0 locally",
        "stability_of_x0": (
            "PARAMETER-DEPENDENT. Unchanged: V'(0)=0 by evenness of V; sign of V''(0) free. "
            "P2-compatible mixed terms such as x xdot^3 do not fix that sign."
        ),
        "scale_free_branch": scale_free_branch(),
        "unique_dynamics": "NO",
        "unique_stable": "NO",
        "unique_dimensionless": "NO",
        "classes": census,
        "monomials": catalog,
        "canonicalization": canonicalization_domain(),
        "minimality": minimality_criteria(),
        "dimensional_table": dimensional_table(),
        "numerical_examples": examples,
        "leftover": leftover_after_redundancy(),
        "checks": {
            "z2_even_quadratic_L": even_L,
            "linear_xdot_total_derivative": total_der,
            "Vprime0": str(vp0),
            "Vsecond0": str(vpp0),
            "canonical_M_const": kin_ok_const,
            "canonical_M_even": kin_ok_even,
            "quartic_velocity_survives": sp.simplify(leftover_quartic_vel) != 0,
            "distinct_quartics_inequivalent": inequivalent,
            "principles_select_Vsecond_sign": False,
            "k_from_p1p4": False,
            "x_xdot_total_derivative": xxdot["total_derivative"] == "YES",
            "x_xdot3_symmetry": mixed["symmetry_compatible"] == "YES",
            "x_xdot3_total_derivative": mixed["total_derivative"] == "NO",
            "x_xdot3_time_reversal": mixed["time_reversal"] == "NO",
        },
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
        "additional_principle_not_adopted": (
            "A rule that fixes the leftover free functions (K, W, or U), not a term "
            "added to force a minimum. P9 is classified but not used to select a law. "
            "Not adopted as a solution."
        ),
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Phase 2 dynamical-principle analysis must run inside DerivationContext.")
