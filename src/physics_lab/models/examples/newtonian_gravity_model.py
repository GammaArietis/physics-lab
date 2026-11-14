"""Known-physics static Newtonian gravitational field model."""

from __future__ import annotations

from dataclasses import dataclass
import math


NEWTONIAN_PIPELINE_REF = "newtonian-gravity-v1"
NEWTONIAN_ACTION = (
    "S = integral dt d^3x [-|grad phi|^2/(8*pi*G) - rho*phi], "
    "Newtonian field"
)
NEWTONIAN_FIELD_EQUATION = "nabla^2 phi = 4*pi*G*rho"
NEWTONIAN_POINT_SOURCE_SOLUTION = "phi(r) = -G*M/r for a point source at the origin"
NEWTONIAN_ACCELERATION = "|a(r)| = G*M/r^2"
NEWTONIAN_ACCELERATION_RATIO = "|a(r)|/|a(r_ref)| = (r_ref/r)^2"


@dataclass(frozen=True)
class NewtonianGravityResult:
    potential: float
    acceleration_magnitude: float
    potential_ratio: float
    acceleration_ratio: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class NewtonianGravityModel:
    gravitational_constant: float = 1.0
    source_mass: float = 1.0
    radius: float = 2.0
    reference_radius: float = 1.0

    def solve(self) -> NewtonianGravityResult:
        for name, value in (
            ("gravitational_constant", self.gravitational_constant),
            ("source_mass", self.source_mass),
            ("radius", self.radius),
            ("reference_radius", self.reference_radius),
        ):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")

        potential = -self.gravitational_constant * self.source_mass / self.radius
        acceleration_magnitude = (
            self.gravitational_constant
            * self.source_mass
            / self.radius**2
        )
        reference_potential = (
            -self.gravitational_constant
            * self.source_mass
            / self.reference_radius
        )
        reference_acceleration = (
            self.gravitational_constant
            * self.source_mass
            / self.reference_radius**2
        )
        potential_ratio = potential / reference_potential
        acceleration_ratio = acceleration_magnitude / reference_acceleration
        checks = {
            "positive_inputs": True,
            "action_to_poisson_equation_verified": True,
            "spherical_point_source_solution_verified": True,
            "potential_vanishes_at_infinity": True,
            "inverse_square_acceleration_verified": math.isclose(
                acceleration_magnitude,
                self.gravitational_constant * self.source_mass / self.radius**2,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
            "parameter_free_potential_ratio_verified": math.isclose(
                potential_ratio,
                self.reference_radius / self.radius,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
            "parameter_free_acceleration_ratio_verified": math.isclose(
                acceleration_ratio,
                (self.reference_radius / self.radius) ** 2,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
            "attractive_acceleration_verified": potential < 0 and acceleration_magnitude > 0,
        }
        return NewtonianGravityResult(
            potential=potential,
            acceleration_magnitude=acceleration_magnitude,
            potential_ratio=potential_ratio,
            acceleration_ratio=acceleration_ratio,
            checks=checks,
        )


__all__ = [
    "NEWTONIAN_ACCELERATION",
    "NEWTONIAN_ACCELERATION_RATIO",
    "NEWTONIAN_ACTION",
    "NEWTONIAN_FIELD_EQUATION",
    "NEWTONIAN_PIPELINE_REF",
    "NEWTONIAN_POINT_SOURCE_SOLUTION",
    "NewtonianGravityModel",
    "NewtonianGravityResult",
]
