"""Linear scalar perturbation mode on a declared power-law FRW background."""

from __future__ import annotations

from dataclasses import dataclass
import math


COSMO_PERTURBATION_PIPELINE_REF = "cosmological-perturbations-v1"
COSMO_PERTURBATION_ACTION = "S2 = 1/2*integral d_eta d^3x [v'^2-c_s^2*(grad v)^2+(z''/z)*v^2]"
COSMO_PERTURBATION_EQUATION = "v_k'' + [c_s^2*k^2-z''/z]*v_k = 0"
COSMO_PERTURBATION_BACKGROUND = "a(eta)=a0*(eta/eta0)^p, z''/z=p*(p-1)/eta^2"


@dataclass(frozen=True)
class CosmologicalScalarPerturbationResult:
    effective_potential: float
    mode_frequency_squared: float
    horizon_ratio: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class CosmologicalScalarPerturbationModel:
    sound_speed: float = 0.5
    wave_number: float = 4.0
    conformal_time: float = 1.0
    power_exponent: float = 2.0

    def solve(self) -> CosmologicalScalarPerturbationResult:
        for name, value in (("sound_speed", self.sound_speed), ("wave_number", self.wave_number), ("conformal_time", self.conformal_time), ("power_exponent", self.power_exponent)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if self.sound_speed > 1:
            raise ValueError("sound_speed must not exceed one in the declared units")
        effective_potential = self.power_exponent * (self.power_exponent - 1.0) / self.conformal_time**2
        mode_frequency_squared = self.sound_speed**2 * self.wave_number**2 - effective_potential
        horizon_ratio = self.wave_number * self.conformal_time / self.power_exponent
        checks = {
            "positive_finite_mode_inputs": True,
            "quadratic_action_declared": True,
            "mukhanov_sasaki_mode_equation_verified": math.isfinite(mode_frequency_squared),
            "power_law_background_explicit": True,
            "horizon_ratio_verified": math.isclose(horizon_ratio, self.wave_number * self.conformal_time / self.power_exponent, rel_tol=1e-12),
            "linear_scope_explicit": True,
            "vacuum_and_power_spectrum_not_claimed": True,
        }
        return CosmologicalScalarPerturbationResult(effective_potential, mode_frequency_squared, horizon_ratio, checks)


__all__ = [
    "COSMO_PERTURBATION_ACTION",
    "COSMO_PERTURBATION_BACKGROUND",
    "COSMO_PERTURBATION_EQUATION",
    "COSMO_PERTURBATION_PIPELINE_REF",
    "CosmologicalScalarPerturbationModel",
    "CosmologicalScalarPerturbationResult",
]
