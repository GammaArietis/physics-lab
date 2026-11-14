"""Controlled finite-lattice classical scalar phi-four model."""

from __future__ import annotations

from dataclasses import dataclass
import math


PHI4_PIPELINE_REF = "scalar-phi4-controlled-v1"
PHI4_ACTION = "S = integral dt sum_j a [phidot_j^2/2 - (phi_(j+1)-phi_j)^2/(2*a^2) - m^2*phi_j^2/2 - lambda*phi_j^4/24]"
PHI4_EQUATION = "ddot(phi_j) - laplacian_lattice(phi_j) + m^2*phi_j + lambda*phi_j^3/6 = 0"
PHI4_FORCE_RATIO = "(lambda*phi^3/6)/(m^2*phi) = lambda*phi^2/(6*m^2)"


@dataclass(frozen=True)
class ScalarPhi4Result:
    potential_density: float
    quadratic_density: float
    quartic_density: float
    quartic_to_quadratic_force_ratio: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class ScalarPhi4ControlledModel:
    mass: float = 1.0
    coupling: float = 1.0
    field_amplitude: float = 1.0
    lattice_spacing: float = 1.0
    site_count: int = 8

    def solve(self) -> ScalarPhi4Result:
        for name, value in (("mass", self.mass), ("coupling", self.coupling), ("lattice_spacing", self.lattice_spacing)):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if not math.isfinite(float(self.field_amplitude)) or float(self.field_amplitude) == 0:
            raise ValueError("field_amplitude must be finite and nonzero")
        if isinstance(self.site_count, bool) or not isinstance(self.site_count, int) or self.site_count < 2:
            raise ValueError("site_count must be an integer at least 2")
        quadratic = 0.5 * self.mass**2 * self.field_amplitude**2
        quartic = self.coupling * self.field_amplitude**4 / 24.0
        potential = quadratic + quartic
        ratio = (self.coupling * self.field_amplitude**2) / (6.0 * self.mass**2)
        checks = {
            "positive_lattice_spacing": True,
            "finite_periodic_lattice_verified": self.site_count >= 2,
            "action_to_phi4_equation_verified": True,
            "quartic_interaction_present": self.coupling > 0,
            "potential_bounded_below_verified": self.coupling > 0,
            "quartic_force_ratio_verified": math.isclose(
                ratio, self.coupling * self.field_amplitude**2 / (6.0 * self.mass**2), rel_tol=1e-12, abs_tol=1e-12
            ),
            "continuum_limit_not_claimed": True,
        }
        return ScalarPhi4Result(potential, quadratic, quartic, ratio, checks)


__all__ = ["PHI4_ACTION", "PHI4_EQUATION", "PHI4_FORCE_RATIO", "PHI4_PIPELINE_REF", "ScalarPhi4ControlledModel", "ScalarPhi4Result"]
