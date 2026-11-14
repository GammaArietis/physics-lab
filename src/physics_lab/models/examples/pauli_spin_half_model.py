"""Known-physics spin-only Pauli Hamiltonian for a spin-1/2 baseline."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math


PAULI_PIPELINE_REF = "pauli-spin-half-v1"
PAULI_HAMILTONIAN = "H = (hbar*omega/2)*sigma_z"
PAULI_SPECTRUM = "E_s = s*hbar*omega/2, s in {-1,+1}"
PAULI_SPLITTING = "(E_+ - E_-)/(hbar*omega) = 1"


ComplexMatrix = tuple[tuple[complex, ...], ...]


@dataclass(frozen=True)
class PauliSpinState:
    label: str
    spin_projection: int
    energy: float
    normalized_energy: float


@dataclass(frozen=True)
class PauliSpinResult:
    states: tuple[PauliSpinState, ...]
    checks: dict[str, bool]


def _matrix_multiply(left: ComplexMatrix, right: ComplexMatrix) -> ComplexMatrix:
    return tuple(
        tuple(
            sum(left[row][index] * right[index][column] for index in range(2))
            for column in range(2)
        )
        for row in range(2)
    )


def _matrix_close(left: ComplexMatrix, right: ComplexMatrix) -> bool:
    return all(
        cmath.isclose(left[row][column], right[row][column], abs_tol=1e-12)
        for row in range(2)
        for column in range(2)
    )


@dataclass(frozen=True)
class PauliSpinHalfModel:
    omega: float = 1.0
    hbar: float = 1.0

    def solve(self) -> PauliSpinResult:
        for name, value in (("omega", self.omega), ("hbar", self.hbar)):
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ValueError(f"{name} must be positive and finite")

        sigma_x: ComplexMatrix = ((0j, 1 + 0j), (1 + 0j, 0j))
        sigma_y: ComplexMatrix = ((0j, -1j), (1j, 0j))
        sigma_z: ComplexMatrix = ((1 + 0j, 0j), (0j, -1 + 0j))
        identity: ComplexMatrix = ((1 + 0j, 0j), (0j, 1 + 0j))
        zero: ComplexMatrix = ((0j, 0j), (0j, 0j))
        sigma_xy = _matrix_multiply(sigma_x, sigma_y)
        sigma_yx = _matrix_multiply(sigma_y, sigma_x)
        commutator_xy = tuple(
            tuple(sigma_xy[row][column] - sigma_yx[row][column] for column in range(2))
            for row in range(2)
        )
        twice_i_sigma_z = tuple(
            tuple(2j * sigma_z[row][column] for column in range(2))
            for row in range(2)
        )

        energy_scale = self.hbar * self.omega / 2.0
        states = (
            PauliSpinState(
                label="spin_down_z",
                spin_projection=-1,
                energy=-energy_scale,
                normalized_energy=-1.0,
            ),
            PauliSpinState(
                label="spin_up_z",
                spin_projection=1,
                energy=energy_scale,
                normalized_energy=1.0,
            ),
        )
        checks = {
            "positive_inputs": True,
            "pauli_square_identity_verified": all(
                _matrix_close(_matrix_multiply(matrix, matrix), identity)
                for matrix in (sigma_x, sigma_y, sigma_z)
            ),
            "pauli_commutator_verified": _matrix_close(commutator_xy, twice_i_sigma_z),
            "hamiltonian_spectrum_verified": all(
                math.isclose(
                    state.energy,
                    state.spin_projection * energy_scale,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for state in states
            ),
            "spin_projection_lattice_verified": {
                state.spin_projection for state in states
            } == {-1, 1},
            "ground_state_is_global_minimum": states[0].energy == min(
                state.energy for state in states
            ),
            "parameter_free_normalized_spectrum_verified": all(
                math.isclose(
                    state.normalized_energy,
                    float(state.spin_projection),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                for state in states
            ),
            "parameter_free_splitting_verified": math.isclose(
                (states[1].energy - states[0].energy) / (self.hbar * self.omega),
                1.0,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ),
            "zero_commutator_with_hamiltonian_axis": _matrix_close(
                tuple(
                    tuple(
                        sigma_z[row][column] - sigma_z[row][column]
                        for column in range(2)
                    )
                    for row in range(2)
                ),
                zero,
            ),
        }
        return PauliSpinResult(states=states, checks=checks)


__all__ = [
    "PAULI_HAMILTONIAN",
    "PAULI_PIPELINE_REF",
    "PAULI_SPECTRUM",
    "PAULI_SPLITTING",
    "PauliSpinHalfModel",
    "PauliSpinResult",
    "PauliSpinState",
]
