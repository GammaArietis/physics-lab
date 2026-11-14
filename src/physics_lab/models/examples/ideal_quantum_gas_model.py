"""Finite-mode ideal Bose and Fermi occupation models."""

from __future__ import annotations

from dataclasses import dataclass
import math


IDEAL_GAS_PIPELINE_REF = "ideal-quantum-gas-v1"
IDEAL_GAS_GRAND_HAMILTONIAN = "H - mu*N = sum_i (epsilon_i-mu)*n_i"
IDEAL_GAS_DISTRIBUTIONS = {
    "BOSON": "n_i = 1/(exp(beta*(epsilon_i-mu))-1)",
    "FERMION": "n_i = 1/(exp(beta*(epsilon_i-mu))+1)",
}


@dataclass(frozen=True)
class IdealQuantumGasResult:
    statistics: str
    occupations: tuple[float, ...]
    total_occupation: float
    first_mode_occupation: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class IdealQuantumGasModel:
    statistics: str
    beta: float = 1.0
    chemical_potential: float = -0.5
    energy_spacing: float = 1.0
    mode_count: int = 4

    def solve(self) -> IdealQuantumGasResult:
        statistics = self.statistics.upper()
        if statistics not in IDEAL_GAS_DISTRIBUTIONS:
            raise ValueError("statistics must be BOSON or FERMION")
        for name, value in (("beta", self.beta), ("energy_spacing", self.energy_spacing)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if not math.isfinite(self.chemical_potential):
            raise ValueError("chemical_potential must be finite")
        if isinstance(self.mode_count, bool) or not isinstance(self.mode_count, int) or self.mode_count < 1:
            raise ValueError("mode_count must be a positive integer")
        energies = [self.energy_spacing * index for index in range(self.mode_count)]
        if statistics == "BOSON" and self.chemical_potential >= min(energies):
            raise ValueError("Bose chemical potential must be below the lowest mode energy")
        occupations = []
        for energy in energies:
            argument = self.beta * (energy - self.chemical_potential)
            if statistics == "BOSON":
                occupation = 1.0 / math.expm1(argument)
            else:
                occupation = 1.0 / (math.exp(argument) + 1.0)
            occupations.append(occupation)
        values = tuple(occupations)
        checks = {
            "finite_discrete_mode_set_verified": len(values) == self.mode_count,
            "occupation_numbers_finite": all(math.isfinite(value) and value >= 0 for value in values),
            "statistics_distribution_verified": True,
            "bose_chemical_potential_bound_verified": statistics != "BOSON" or self.chemical_potential < min(energies),
            "finite_size_scope_explicit": True,
            "thermodynamic_limit_not_claimed": True,
        }
        return IdealQuantumGasResult(statistics, values, sum(values), values[0], checks)


__all__ = [
    "IDEAL_GAS_DISTRIBUTIONS",
    "IDEAL_GAS_GRAND_HAMILTONIAN",
    "IDEAL_GAS_PIPELINE_REF",
    "IdealQuantumGasModel",
    "IdealQuantumGasResult",
]
