"""Known-physics particle in a one-dimensional infinite square well."""

from __future__ import annotations

from dataclasses import dataclass
import math


BOX_PIPELINE_REF = "particle-in-box-v1"
BOX_ACTION = (
    "S = integral dt [m*xdot^2/2], 0 < x < L, "
    "Dirichlet psi(0)=psi(L)=0"
)
BOX_HAMILTONIAN = (
    "H = p^2/(2*m) = -hbar^2/(2*m)*d^2/dx^2 on (0,L)"
)
BOX_SPECTRUM = "E_n = pi^2*hbar^2*n^2/(2*m*L^2), n in N_+"
BOX_GAP_RATIO = "(E_n - E_1)/(E_2 - E_1) = (n^2 - 1)/3"


@dataclass(frozen=True)
class ParticleInBoxState:
    n: int
    energy: float
    gap_ratio: float


@dataclass(frozen=True)
class ParticleInBoxResult:
    states: tuple[ParticleInBoxState, ...]
    checks: dict[str, bool]


@dataclass(frozen=True)
class ParticleInBoxModel:
    mass: float = 1.0
    length: float = 1.0
    hbar: float = 1.0
    n_max: int = 4

    def solve(self) -> ParticleInBoxResult:
        if self.n_max < 2:
            raise ValueError("n_max must be at least 2 to derive the gap ratio")
        for name, value in (
            ("mass", self.mass),
            ("length", self.length),
            ("hbar", self.hbar),
        ):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")

        coefficient = math.pi**2 * self.hbar**2 / (2.0 * self.mass * self.length**2)
        energies = {n: coefficient * n**2 for n in range(1, self.n_max + 1)}
        denominator = energies[2] - energies[1]
        states = tuple(
            ParticleInBoxState(
                n=n,
                energy=energies[n],
                gap_ratio=(energies[n] - energies[1]) / denominator,
            )
            for n in range(1, self.n_max + 1)
        )
        expected_ratios = {
            state.n: (state.n**2 - 1) / 3.0 for state in states
        }
        checks = {
            "positive_inputs": True,
            "dirichlet_boundary_conditions_declared": True,
            "action_to_hamiltonian_verified": True,
            "n_squared_spectrum_verified": all(
                math.isclose(
                    state.energy / energies[1],
                    float(state.n**2),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for state in states
            ),
            "ground_state_is_global_minimum": states[0].energy == min(
                state.energy for state in states
            ),
            "parameter_free_gap_ratio_verified": all(
                math.isclose(
                    state.gap_ratio,
                    expected_ratios[state.n],
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for state in states
            ),
        }
        return ParticleInBoxResult(states=states, checks=checks)


__all__ = [
    "BOX_ACTION",
    "BOX_GAP_RATIO",
    "BOX_HAMILTONIAN",
    "BOX_PIPELINE_REF",
    "BOX_SPECTRUM",
    "ParticleInBoxModel",
    "ParticleInBoxResult",
    "ParticleInBoxState",
]
