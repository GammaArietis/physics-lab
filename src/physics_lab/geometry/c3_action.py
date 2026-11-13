"""C3 action on a circle: θ → θ + 2π/3, or ξ → ξ + 2πR/3.

C3 means the cyclic group of order 3.  The generator is rotation by
one-third of the S¹ period.  That 3 is the group order, not a charge
fraction and not a model parameter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter


# Cyclic group C3 has order 3 by definition of the name "C3".
C3_ORDER = 3


def c3_shift(radius: Any) -> Any:
    """Displacement along the circle that generates C3: one C3-step of the period."""
    R = radius.symbolic if isinstance(radius, Parameter) else radius
    return 2 * sp.pi * R / C3_ORDER


def plane_wave_n(n: Any, xi: Any, radius: Any) -> Any:
    """χ_n(ξ) = exp(i n ξ / R), the S¹ eigenfunctions in the covering coordinate."""
    R = radius.symbolic if isinstance(radius, Parameter) else radius
    return sp.exp(sp.I * n * xi / R)


def act_c3(chi: Any, xi: Any, radius: Any, times: int = 1) -> Any:
    """(T^times χ)(ξ) = χ(ξ + times * 2πR/3)."""
    return chi.subs(xi, xi + times * c3_shift(radius))


def c3_multiplier(n: Any) -> Any:
    """χ_n(ξ + 2πR/3) / χ_n(ξ) = exp(i n 2π / 3).  Independent of R."""
    return sp.exp(sp.I * n * 2 * sp.pi / C3_ORDER)


def c3_cube_roots() -> tuple[Any, Any, Any]:
    """The three values of exp(2π i r / 3) for r = 0, 1, 2."""
    omega = sp.exp(sp.I * 2 * sp.pi / C3_ORDER)
    return (sp.Integer(1), sp.simplify(omega), sp.simplify(omega ** 2))


def classify_c3_phase(phase: Any) -> int | None:
    """Which cube root is this phase?  None if it is not a cube root of unity.

    Compare by multiplying with the inverse root: ω^{-r} * phase == 1.
    This does not insert n mod 3; it only asks which character the phase is.
    """
    reduced = sp.simplify(phase)
    for r in range(C3_ORDER):
        ratio = sp.simplify(reduced * sp.exp(-sp.I * 2 * sp.pi * r / C3_ORDER))
        if ratio == 1:
            return r
    return None


@dataclass(frozen=True)
class C3ActionResult:
    n: int
    phase: Any
    sector: int | None
    cubed_is_identity: bool
    provenance_phase: str = "DERIVED"
    provenance_sector: str = "DERIVED FROM C3 SYMMETRY"


def analyze_c3_on_n(n: int, radius: Any) -> C3ActionResult:
    """Compute T χ_n and T³ χ_n from the formulae, then classify the phase.

    The C3 multiplier is independent of R, so the identity is checked with a
    symbolic positive radius rather than a float (which would expand 2π/3).
    """
    del radius  # R cancels; kept in the signature because the geometric shift is 2πR/3.
    xi = sp.symbols("xi", real=True)
    R = sp.symbols("R", positive=True)
    chi = plane_wave_n(n, xi, R)
    shifted = act_c3(chi, xi, R, times=1)
    phase = sp.simplify(sp.together(shifted / chi))
    expected = sp.simplify(c3_multiplier(int(n)))
    if sp.simplify(phase / expected) != 1:
        raise RuntimeError(f"C3 phase for n={n} is {phase}, expected {expected}.")
    cubed = act_c3(chi, xi, R, times=C3_ORDER)
    cubed_is_identity = sp.simplify(sp.together(cubed / chi)) == 1
    sector = classify_c3_phase(expected)
    return C3ActionResult(
        n=n,
        phase=expected,
        sector=sector,
        cubed_is_identity=cubed_is_identity,
    )


def c3_order_is_three() -> bool:
    """T³ = id on plane waves iff ω³ = 1 for ω = exp(2π i / 3)."""
    omega = sp.exp(sp.I * 2 * sp.pi / C3_ORDER)
    return sp.simplify(omega ** C3_ORDER) == 1
