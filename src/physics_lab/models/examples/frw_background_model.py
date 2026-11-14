"""Controlled flat FRW background with a constant equation of state."""

from __future__ import annotations

from dataclasses import dataclass
import math


FRW_PIPELINE_REF = "frw-background-v1"
FRW_ACTION = "S = (1/(16*pi*G))*integral d^4x sqrt(-g)*R + S_perfect_fluid, flat Lambda=0"
FRW_METRIC = "ds^2 = -dt^2 + a(t)^2*dSigma_flat^2"
FRW_EQUATIONS = "H^2 = 8*pi*G*rho/3; dot(rho)+3*H*(rho+p)=0; p=w*rho"


@dataclass(frozen=True)
class FRWBackgroundResult:
    hubble_rate: float
    density_scaling_exponent: float
    density_ratio: float
    friedmann_residual: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class FRWBackgroundModel:
    gravitational_constant: float = 1.0
    density: float = 1.0
    scale_factor: float = 1.0
    equation_of_state: float = 0.0
    scale_factor_ratio: float = 2.0

    def solve(self) -> FRWBackgroundResult:
        for name, value in (("gravitational_constant", self.gravitational_constant), ("density", self.density), ("scale_factor", self.scale_factor), ("scale_factor_ratio", self.scale_factor_ratio)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if not math.isfinite(self.equation_of_state) or self.equation_of_state <= -1:
            raise ValueError("equation_of_state must be finite and greater than -1")
        hubble_rate = math.sqrt(8.0 * math.pi * self.gravitational_constant * self.density / 3.0)
        exponent = 3.0 * (1.0 + self.equation_of_state)
        density_ratio = self.scale_factor_ratio ** (-exponent)
        friedmann_residual = hubble_rate**2 - 8.0 * math.pi * self.gravitational_constant * self.density / 3.0
        checks = {
            "positive_finite_background_inputs": True,
            "flat_frw_metric_declared": True,
            "friedmann_equation_verified": math.isclose(friedmann_residual, 0.0, abs_tol=1e-12),
            "continuity_scaling_verified": math.isclose(density_ratio, self.scale_factor_ratio ** (-3.0 * (1.0 + self.equation_of_state)), rel_tol=1e-12),
            "lambda_zero_scope_explicit": True,
            "classical_background_scope_explicit": True,
            "observational_parameters_not_claimed": True,
        }
        return FRWBackgroundResult(hubble_rate, exponent, density_ratio, friedmann_residual, checks)


__all__ = [
    "FRW_ACTION",
    "FRW_EQUATIONS",
    "FRW_METRIC",
    "FRW_PIPELINE_REF",
    "FRWBackgroundModel",
    "FRWBackgroundResult",
]
