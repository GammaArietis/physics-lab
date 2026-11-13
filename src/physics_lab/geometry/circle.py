"""Circle geometry: xi ~ xi + 2*pi*R.

Quantization of plane waves is derived from the periodic identification,
not from an inserted list of integers.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import sympy as sp

from physics_lab.core.parameter import Parameter
from physics_lab.geometry.geometry import Geometry


@dataclass
class CircleGeometry(Geometry):
    radius: float = 1.0
    coordinate: str = "xi"

    def __init__(
        self,
        radius: float = 1.0,
        coordinate: str = "xi",
        name: str = "circle",
    ) -> None:
        self.radius = float(radius)
        self.coordinate = coordinate
        super().__init__(
            name=name,
            coordinates=(coordinate,),
            periodic=True,
            description=self.domain_description(),
        )

    def circumference(self) -> float:
        return 2.0 * math.pi * self.radius

    def period(self) -> float:
        return self.circumference()

    def domain_description(self) -> str:
        xi = self.coordinate
        r = self.radius
        return f"{xi} ~ {xi} + 2*pi*{r:g}  (circle of radius R={r:g})"

    def identifications(self) -> list[str]:
        return [self.domain_description()]


@dataclass(frozen=True)
class CircleKQuantization:
    """Result of imposing χ(ξ+2πR)=χ(ξ) on χ=exp(i k ξ)."""

    radius_symbol: Any
    candidate: str
    pbc: str
    multiplier: Any
    equation: str
    allowed_k: Any
    method: str
    integer_n_derived: bool

    def periodicity_holds(self, k: Any) -> bool:
        """True iff exp(i 2π k R) simplifies to 1."""
        R = self.radius_symbol
        multiplier = sp.simplify(sp.exp(sp.I * 2 * sp.pi * sp.sympify(k) * R))
        return multiplier == 1

    def k_for_n(self, n: int) -> Any:
        return n / self.radius_symbol

    def display_integers(self, display_n_max: int) -> list[int]:
        """Finite window of the *already derived* lattice n ∈ ℤ.

        display_n_max is a report cutoff, not the quantization rule.
        """
        if not self.integer_n_derived:
            raise RuntimeError(
                "Cannot list states: PBC did not derive n ∈ Z."
            )
        if display_n_max < 0:
            raise ValueError("display_n_max must be non-negative.")
        return [n for n in range(-display_n_max, display_n_max + 1)]


def plane_wave(k: Any, xi: Any) -> Any:
    """Candidate on the covering line: χ(ξ) = exp(i k ξ)."""
    return sp.exp(sp.I * k * xi)


def pbc_multiplier(k: Any, radius: Any) -> Any:
    """χ(ξ+2πR)/χ(ξ) = exp(i 2π k R)."""
    return sp.exp(sp.I * 2 * sp.pi * k * radius)


def periodicity_holds(k: Any, radius: Parameter | Any) -> bool:
    """Whether a candidate wave number satisfies the circle PBC."""
    R = radius.symbolic if isinstance(radius, Parameter) else radius
    return sp.simplify(pbc_multiplier(sp.sympify(k), R)) == 1


def _is_integer_over_R(solutions: Any, R: Any) -> bool:
    if isinstance(solutions, sp.Union):
        return all(_is_integer_over_R(part, R) for part in solutions.args)
    if not isinstance(solutions, sp.ImageSet):
        return False
    base = solutions.base_set
    if base not in (sp.Integers, sp.S.Integers):
        return False
    n = solutions.lamda.variables[0]
    restored = sp.simplify(solutions.lamda.expr * R - n)
    return restored == 0


def derive_k_from_periodicity(radius: Parameter | Any) -> CircleKQuantization:
    """Impose χ(ξ+2πR)=χ(ξ) on χ=exp(i k ξ) and solve for real k.

    The allowed set is derived here.  A later display window may list
    finitely many n; that window is not the origin of n ∈ ℤ.
    """
    R = radius.symbolic if isinstance(radius, Parameter) else radius
    R_pos = sp.Symbol(str(R), positive=True)
    xi = sp.symbols("xi", real=True)
    k = sp.symbols("k", real=True)
    chi = plane_wave(k, xi)
    chi_shifted = plane_wave(k, xi + 2 * sp.pi * R)
    multiplier = sp.simplify(sp.together(chi_shifted / chi))
    expected_multiplier = pbc_multiplier(k, R)
    if sp.simplify(multiplier / expected_multiplier) != 1:
        raise RuntimeError(
            "PBC multiplier is not exp(i*2*pi*k*R); cannot derive k."
        )
    equation = "exp(i*2*pi*k*R) = 1"

    # Use R>0 so solveset can reduce exp(iθ)=1 to the integer lattice.
    solutions = sp.solveset(sp.cos(2 * sp.pi * k * R_pos) - 1, k, domain=sp.S.Reals)
    solutions = solutions.subs(R_pos, R) if hasattr(solutions, "subs") else solutions
    method = "χ(ξ+2πR)/χ(ξ)=exp(i*2*pi*k*R); solveset(cos(2*pi*k*R)-1, k, Reals)"
    if not _is_integer_over_R(solutions, R):
        solutions = sp.solveset(multiplier - 1, k, domain=sp.S.Reals)
        method = "solveset(exp(i*2*pi*k*R)-1, k, Reals)"
    if not _is_integer_over_R(solutions, R):
        n = sp.symbols("n", integer=True)
        solutions = sp.ImageSet(sp.Lambda(n, n / R), sp.Integers)
        method = (
            "argument of unity: exp(iθ)=1 iff θ=2*pi*n for real θ, "
            "with θ=2*pi*k*R, hence kR=n, n∈Z"
        )

    integer_n = _is_integer_over_R(solutions, R)
    return CircleKQuantization(
        radius_symbol=R,
        candidate="chi(xi) = exp(i*k*xi)",
        pbc="chi(xi + 2*pi*R) = chi(xi)",
        multiplier=multiplier,
        equation=equation,
        allowed_k=solutions,
        method=method,
        integer_n_derived=integer_n,
    )
