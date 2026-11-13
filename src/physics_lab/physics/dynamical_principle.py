"""Phase 1 dynamical principles for the torus modulus a ~ 1/a.

Does not choose a single potential.  Catalogues even V(x), x = log a,
and records which facts follow from symmetry versus free coefficients.
"""

from __future__ import annotations

from typing import Any

import sympy as sp

from physics_lab.core.provenance import derivation_is_active


def log_coordinate(a: Any) -> Any:
    """x = log a.  DERIVED change of coordinate."""
    return sp.log(a)


def inversion_to_sign_flip(a: Any) -> bool:
    """a → 1/a is x → −x."""
    x = log_coordinate(a)
    x_inv = log_coordinate(1 / a)
    return sp.simplify(x_inv + x) == 0


def even_potential(x: Any, c0: Any, c2: Any, c4: Any) -> Any:
    """Truncation of the even Taylor series.  Odd powers are absent by symmetry."""
    return c0 + c2 * x**2 + c4 * x**4


def odd_part(expr: Any, x: Any) -> Any:
    return sp.simplify(sp.expand((expr - expr.subs(x, -x)) / 2))


def even_part(expr: Any, x: Any) -> Any:
    return sp.simplify(sp.expand((expr + expr.subs(x, -x)) / 2))


def first_derivative(c2: Any, c4: Any, x: Any) -> Any:
    return sp.diff(even_potential(x, 0, c2, c4), x)


def second_derivative(c2: Any, c4: Any, x: Any) -> Any:
    return sp.diff(first_derivative(c2, c4, x), x)


def curvature_at_origin(c2: Any) -> Any:
    """V''(0) = 2 c2."""
    return 2 * sp.sympify(c2)


def classify_stability_c2(c2: Any) -> str:
    val = sp.sympify(c2)
    if val.is_number:
        num = float(val)
        if num > 0:
            return "stable minimum"
        if num < 0:
            return "unstable"
        return "flat direction / marginal"
    return "parameter-dependent"


def stability_condition() -> str:
    return "c2 > 0"


def affine_equivalent_quartic(c2_a: Any, c4_a: Any, c2_b: Any, c4_b: Any) -> bool:
    """True iff V_b = p V_a + q for some p ≠ 0, with x held fixed.

    Distinct c4/c2 (x = log a held fixed) are not equivalent.
    """
    a2, a4, b2, b4 = (sp.simplify(v) for v in (c2_a, c4_a, c2_b, c4_b))
    if a2 == 0 and b2 == 0:
        if a4 == 0 and b4 == 0:
            return True
        if a4 == 0 or b4 == 0:
            return False
        return True
    if a2 == 0 or b2 == 0:
        return False
    return sp.simplify(a4 / a2 - b4 / b2) == 0


def shape_ratio(c2: Any, c4: Any) -> Any:
    """ρ = c4/c2. Dimensionless because x = log a is dimensionless.

    Invariant under V → p V + q with x held fixed. Not invariant under x → s x.
    """
    if sp.simplify(c2) == 0:
        return sp.nan
    return sp.simplify(c4 / c2)


def x_rescale_combination(c2: Any, c4: Any) -> Any:
    """c4/c2². Invariant under x → s x, but not a pure number: it carries 1/[V]."""
    if sp.simplify(c2) == 0:
        return sp.nan
    return sp.simplify(c4 / c2**2)


def frequency_squared(c2: Any, M: Any) -> Any:
    """ω² = V''(0)/M = 2 c2 / M. Small-oscillation frequency only."""
    return sp.simplify(2 * c2 / M)


def rescaled_coefficients(*, c2: Any, c4: Any, s: Any) -> tuple[Any, Any]:
    """x → s x.  V = c2 x² + c4 x⁴ = (c2/s²) y² + (c4/s⁴) y⁴."""
    return sp.simplify(c2 / s**2), sp.simplify(c4 / s**4)


def time_rescaled_omega(omega: Any, d: Any) -> Any:
    """t → d t sends frequencies to ω/d."""
    return sp.simplify(omega / d)


def principles() -> list[dict[str, str]]:
    return [
        {
            "name": "symmetry a -> 1/a",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Inherited from the rectangular-torus toy. Not re-derived here.",
        },
        {
            "name": "real action",
            "status": "PRINCIPLE / ASSUMED",
            "note": "V is a real function of a > 0.",
        },
        {
            "name": "regularity for a > 0",
            "status": "PRINCIPLE / ASSUMED",
            "note": "V is smooth in x = log a on the real line.",
        },
        {
            "name": "no arbitrary coordinate dependence",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Physical statements refer to the geometry, not to a preferred chart.",
        },
        {
            "name": "no term added only to create a minimum",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Stop criterion: do not enlarge V to force c2 > 0.",
        },
        {
            "name": "boundedness from below",
            "status": "PRINCIPLE / ASSUMED (optional, not imposed)",
            "note": "If imposed on a quartic, c4 ≥ 0. That still does not fix sign(c2).",
        },
        {
            "name": "minimal free parameters",
            "status": "PRINCIPLE / ASSUMED",
            "note": "Truncate the even series; do not add extra fields or moduli.",
        },
    ]


def catalog_simple_even_potentials() -> list[str]:
    """Simplest representatives of V(x)=V(-x). None is selected."""
    return [
        "V = c0  (constant; no dynamics)",
        "V = c0 + c2 x^2  (even quadratic)",
        "V = c0 + c2 x^2 + c4 x^4  (even quartic truncation)",
        "V = F(x^2) for smooth F",
        "V(a) = G(a + 1/a) for smooth G  (equivalent: a+1/a = 2 cosh x)",
    ]


def compare_to_eta_model() -> dict[str, str]:
    return {
        "from_symmetry_alone": (
            "x=0 is always stationary, V even, odd Taylor terms absent"
        ),
        "specific_to_eta": (
            "the particular function 4 log|η(i a)| + log(a) fixes all c_{2k}, "
            "and gives V''(0)<0 (unstable)"
        ),
        "requires_dynamical_choice": (
            "the sign of c2, the value of c4/c2, and any higher even couplings"
        ),
        "old_model_modified": "NO",
    }


def analyze_dynamical_principle() -> dict[str, Any]:
    x, c0, c2, c4, M, s, d, p, q = sp.symbols("x c0 c2 c4 M s d p q", real=True)
    V = even_potential(x, c0, c2, c4)
    Vp = sp.diff(V, x)
    Vpp = sp.diff(Vp, x)
    rho = shape_ratio(c2, c4)
    w2 = frequency_squared(c2, M)
    conclusion = (
        "Symmetry a→1/a makes V even in x=log a, so x=0 is always stationary "
        "and odd powers drop out. That is geometry-selected, not stability-selected. "
        "The curvature V''(0)=2 c2 is INPUT. The listed principles do not fix "
        "sign(c2) or c4/c2. Unique dynamical law: NO. Unique stable configuration: NO. "
        "No extra term is added to force a minimum."
    )
    return {
        "modulus": "a",
        "symmetry": "a -> 1/a",
        "log_coordinate": "x = log a",
        "equivalent_symmetry": "x -> -x",
        "allowed": (
            "V(x)=V(-x): c0 + c2 x^2 + c4 x^4 + higher even powers. "
            "Simplest truncations: constant; quadratic even; quartic even."
        ),
        "independent_coefficients": "c2, c4, ... even; c0 is an offset CONVENTION",
        "stationary": "x = 0  (V'(0)=0 for every even V)",
        "stability": "parameter-dependent: sign(c2) is not fixed",
        "stability_conditions": "stable minimum iff c2 > 0; unstable iff c2 < 0; marginal iff c2 = 0",
        "kinetic": "L = (M/2) (dx/dt)^2 - V(x),  M>0 INPUT",
        "frequency": "omega^2 = V''(0)/M = 2 c2 / M   (PARAMETER-DEPENDENT; small oscillation only)",
        "normalization": (
            "c0 is an offset CONVENTION. V -> p V rescales energy. t -> d t rescales omega. "
            "x = log a is the working CONVENTION (e-foldings). x -> s x (change of log base) "
            "mixes c2 and c4: rho=c4/c2 is NOT invariant, while c4/c2^2 is invariant but not dimensionless."
        ),
        "dimensionless": (
            "With x=log a held fixed: rho = c4/c2 is dimensionless and affine-invariant. INPUT. "
            "c4/c2^2 is the x-rescaling combination but has dimension 1/[V], so it is not a pure number. "
            "Neither combination is fixed by the principles."
        ),
        "unique_dynamics": "NO",
        "unique_stable": "NO",
        "free_parameters": (
            "even function space (infinite). Quartic truncation after offset and units: "
            "sign(c2) and rho=c4/c2. M is entangled with the time unit."
        ),
        "catalog": catalog_simple_even_potentials(),
        "geometry_selected": "x=0 as stationary candidate",
        "stability_selected": "NO",
        "scale_selected": "NO",
        "principles": principles(),
        "classification": {
            "symmetry a -> 1/a": "ASSUMED / inherited from toy geometry",
            "x = log a": "DERIVED transformation",
            "V(x)=V(-x)": "DERIVED given symmetry",
            "absence of odd terms": "DERIVED",
            "coefficient c2": "INPUT / FREE",
            "coefficient c4": "INPUT / FREE",
            "stability c2 > 0": "DERIVED CONDITION (not a derived sign)",
            "M": "INPUT",
            "omega^2 = V''/M": "DERIVED GIVEN MODEL",
            "rho = c4/c2": "PARAMETER-DEPENDENT",
            "c4/c2^2": "CONVENTION mix under x-rescaling; not dimensionless",
            "unique dynamics": "NO",
            "x = log a held fixed": "CONVENTION",
        },
        "comparison_eta": compare_to_eta_model(),
        "symbolic": {
            "V": str(V),
            "Vprime": str(sp.expand(Vp)),
            "Vsecond": str(sp.expand(Vpp)),
            "Vprime_at_0": str(sp.simplify(Vp.subs(x, 0))),
            "Vsecond_at_0": str(sp.simplify(Vpp.subs(x, 0))),
            "rho": str(rho),
            "omega2": str(w2),
            "odd_part": str(odd_part(V, x)),
        },
        "interpretation": "UNTESTED",
        "conclusion": conclusion,
    }


def assert_solve_context() -> None:
    if not derivation_is_active():
        raise RuntimeError("Dynamical-principle analysis must run inside DerivationContext.")
