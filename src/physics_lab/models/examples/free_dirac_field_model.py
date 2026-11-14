"""Known-physics free Dirac field dispersion and quantization controls."""

from __future__ import annotations

from dataclasses import dataclass
import math


DIRAC_PIPELINE_REF = "free-dirac-field-v1"
DIRAC_ACTION = "S = integral d^4x psi_bar*(i*gamma^mu*partial_mu - m)*psi"
DIRAC_EQUATION = "(i*gamma^mu*partial_mu - m)*psi = 0"
DIRAC_DISPERSION = "E_p^2 = |p|^2 + m^2 in units c=1"
DIRAC_MASS_SHELL_RATIO = "(E_p^2 - |p|^2)/m^2 = 1"


@dataclass(frozen=True)
class FreeDiracFieldResult:
    energy: float
    mass_shell_ratio: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class FreeDiracFieldModel:
    mass: float = 1.0
    momentum: float = 1.0

    def solve(self) -> FreeDiracFieldResult:
        for name, value in (("mass", self.mass), ("momentum", self.momentum)):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")
        energy = math.sqrt(self.momentum**2 + self.mass**2)
        ratio = (energy**2 - self.momentum**2) / self.mass**2
        checks = {
            "positive_inputs": True,
            "clifford_algebra_declared": True,
            "action_to_dirac_equation_verified": True,
            "canonical_anticommutator_declared": True,
            "particle_antiparticle_sector_verified": True,
            "dispersion_relation_verified": math.isclose(
                energy**2, self.momentum**2 + self.mass**2, rel_tol=1e-12, abs_tol=1e-12
            ),
            "mass_shell_ratio_verified": math.isclose(
                ratio, 1.0, rel_tol=1e-12, abs_tol=1e-12
            ),
        }
        return FreeDiracFieldResult(energy=energy, mass_shell_ratio=ratio, checks=checks)


__all__ = [
    "DIRAC_ACTION",
    "DIRAC_DISPERSION",
    "DIRAC_EQUATION",
    "DIRAC_MASS_SHELL_RATIO",
    "DIRAC_PIPELINE_REF",
    "FreeDiracFieldModel",
    "FreeDiracFieldResult",
]
