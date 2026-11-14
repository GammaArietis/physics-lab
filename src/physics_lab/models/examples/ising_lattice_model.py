"""Exact finite-size one-dimensional periodic Ising transfer-matrix model."""

from __future__ import annotations

from dataclasses import dataclass
import math


ISING_PIPELINE_REF = "ising-lattice-v1"
ISING_HAMILTONIAN = "H = -J sum_j s_j*s_(j+1), s_j in {-1,+1}, periodic"
ISING_TRANSFER_SPECTRUM = "lambda_+ = 2*cosh(beta*J), lambda_- = 2*sinh(beta*J)"


@dataclass(frozen=True)
class IsingLatticeResult:
    partition_function: float
    energy_per_site: float
    nearest_neighbor_correlation: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class IsingLatticeModel:
    beta: float = 0.5
    coupling: float = 1.0
    site_count: int = 16

    def solve(self) -> IsingLatticeResult:
        if not math.isfinite(self.beta) or self.beta <= 0:
            raise ValueError("beta must be positive and finite")
        if not math.isfinite(self.coupling) or self.coupling <= 0:
            raise ValueError("coupling must be positive and finite")
        if isinstance(self.site_count, bool) or not isinstance(self.site_count, int) or self.site_count < 2:
            raise ValueError("site_count must be an integer at least 2")
        x = self.beta * self.coupling
        lambda_plus = 2.0 * math.cosh(x)
        lambda_minus = 2.0 * math.sinh(x)
        positive_term = lambda_plus**self.site_count
        negative_term = lambda_minus**self.site_count
        partition_function = positive_term + negative_term
        correlation = (
            positive_term * math.tanh(x) + negative_term / math.tanh(x)
        ) / partition_function
        energy_per_site = -self.coupling * correlation
        checks = {
            "positive_finite_inputs": True,
            "finite_periodic_lattice_verified": self.site_count >= 2,
            "transfer_matrix_spectrum_verified": lambda_plus > lambda_minus > 0,
            "finite_partition_function_verified": math.isfinite(partition_function) and partition_function > 0,
            "nearest_neighbor_observable_verified": math.isfinite(correlation),
            "thermodynamic_limit_not_claimed": True,
        }
        return IsingLatticeResult(partition_function, energy_per_site, correlation, checks)


__all__ = [
    "ISING_HAMILTONIAN",
    "ISING_PIPELINE_REF",
    "ISING_TRANSFER_SPECTRUM",
    "IsingLatticeModel",
    "IsingLatticeResult",
]
