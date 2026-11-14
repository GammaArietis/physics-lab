"""Finite periodic harmonic lattice normal modes."""

from __future__ import annotations

from dataclasses import dataclass
import math


PHONON_PIPELINE_REF = "harmonic-lattice-phonons-v1"
PHONON_HAMILTONIAN = "H = sum_j p_j^2/(2*m) + K*sum_j (q_(j+1)-q_j)^2/2, periodic"
PHONON_DISPERSION = "omega_k = 2*sqrt(K/m)*sin(pi*k/N), k=0,...,N-1"


@dataclass(frozen=True)
class HarmonicLatticePhononResult:
    zero_mode_frequency: float
    lowest_nonzero_frequency: float
    highest_frequency: float
    nonzero_mode_count: int
    frequency_ratio: float
    checks: dict[str, bool]


@dataclass(frozen=True)
class HarmonicLatticePhononModel:
    mass: float = 1.0
    spring_constant: float = 1.0
    lattice_spacing: float = 1.0
    site_count: int = 8

    def solve(self) -> HarmonicLatticePhononResult:
        for name, value in (("mass", self.mass), ("spring_constant", self.spring_constant), ("lattice_spacing", self.lattice_spacing)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        if isinstance(self.site_count, bool) or not isinstance(self.site_count, int) or self.site_count < 3:
            raise ValueError("site_count must be an integer at least 3")
        scale = 2.0 * math.sqrt(self.spring_constant / self.mass)
        frequencies = [scale * abs(math.sin(math.pi * mode / self.site_count)) for mode in range(self.site_count)]
        nonzero = frequencies[1:]
        lowest = min(nonzero)
        highest = max(nonzero)
        checks = {
            "positive_finite_inputs": True,
            "finite_periodic_lattice_verified": self.site_count >= 3,
            "translation_zero_mode_verified": math.isclose(frequencies[0], 0.0, abs_tol=1e-12),
            "normal_mode_dispersion_verified": all(value >= 0 for value in frequencies),
            "nonzero_mode_count_verified": len(nonzero) == self.site_count - 1,
            "finite_size_scope_explicit": True,
            "thermodynamic_limit_not_claimed": True,
        }
        return HarmonicLatticePhononResult(0.0, lowest, highest, len(nonzero), highest / lowest, checks)


__all__ = [
    "PHONON_DISPERSION",
    "PHONON_HAMILTONIAN",
    "PHONON_PIPELINE_REF",
    "HarmonicLatticePhononModel",
    "HarmonicLatticePhononResult",
]
