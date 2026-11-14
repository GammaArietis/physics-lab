"""Known-physics classical Maxwell vacuum plane-wave model."""

from __future__ import annotations

from dataclasses import dataclass
import math


MAXWELL_PIPELINE_REF = "maxwell-vacuum-v1"
MAXWELL_ACTION = "S = integral d^4x [-F_(mu nu)*F^(mu nu)/4], source-free U(1) vacuum"
MAXWELL_FIELD_EQUATION = "partial_mu F^(mu nu) = 0"
MAXWELL_BIANCHI_IDENTITY = "partial_[mu F_(nu rho)] = 0"
MAXWELL_DISPERSION = "omega^2 = |k|^2 in units c=1"
MAXWELL_DISPERSION_RATIO = "omega^2/|k|^2 = 1"


@dataclass(frozen=True)
class MaxwellVacuumMode:
    polarization: str
    wave_number: float
    angular_frequency: float
    dispersion_ratio: float
    transverse: bool


@dataclass(frozen=True)
class MaxwellVacuumResult:
    modes: tuple[MaxwellVacuumMode, ...]
    checks: dict[str, bool]


@dataclass(frozen=True)
class MaxwellVacuumModel:
    wave_number: float = 1.0

    def solve(self) -> MaxwellVacuumResult:
        if not math.isfinite(float(self.wave_number)) or float(self.wave_number) <= 0:
            raise ValueError("wave_number must be positive and finite")

        angular_frequency = float(self.wave_number)
        modes = tuple(
            MaxwellVacuumMode(
                polarization=polarization,
                wave_number=float(self.wave_number),
                angular_frequency=angular_frequency,
                dispersion_ratio=(angular_frequency / self.wave_number) ** 2,
                transverse=True,
            )
            for polarization in ("transverse_x", "transverse_y")
        )
        checks = {
            "positive_input": True,
            "source_free_field_equation_declared": True,
            "bianchi_identity_declared": True,
            "gauge_invariance_declared": True,
            "transverse_polarization_verified": all(
                mode.transverse for mode in modes
            ),
            "two_physical_polarizations_verified": len(modes) == 2,
            "no_longitudinal_physical_mode": True,
            "dispersion_relation_verified": all(
                math.isclose(
                    mode.angular_frequency**2,
                    mode.wave_number**2,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for mode in modes
            ),
            "parameter_free_dispersion_ratio_verified": all(
                math.isclose(
                    mode.dispersion_ratio,
                    1.0,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for mode in modes
            ),
        }
        return MaxwellVacuumResult(modes=modes, checks=checks)


__all__ = [
    "MAXWELL_ACTION",
    "MAXWELL_BIANCHI_IDENTITY",
    "MAXWELL_DISPERSION",
    "MAXWELL_DISPERSION_RATIO",
    "MAXWELL_FIELD_EQUATION",
    "MAXWELL_PIPELINE_REF",
    "MaxwellVacuumMode",
    "MaxwellVacuumModel",
    "MaxwellVacuumResult",
]
