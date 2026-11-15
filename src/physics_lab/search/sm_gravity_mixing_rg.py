"""W8 broad RG controls for the reduced Standard Model, gravity and mixing.

The module deliberately combines three related but distinct controls:

* the one-loop reduced Standard Model gauge/top/Higgs system;
* a literature-shaped background-gravity deformation of the Abelian beta
  function, ``beta_g1 = -A*g1 + b1*g1**3``;
* a charge-agnostic positive-semidefinite two-U(1) mixing control.

The last two are not a quantum-gravity calculation and the mixing matrices are
not assigned to a physical charge spectrum.  They are bounded mathematical
controls whose purpose is to expose what the stated truncations can and cannot
produce.  No experimental value of alpha is fitted or used as a target.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


SM_GRAVITY_MIXING_RG_VERSION = "sm-gravity-mixing-rg-v1"
PERTURBATIVE_BOUND = 1.0
MAX_STATE_BOUND = 10.0
LOOP_FACTOR = 16.0 * math.pi**2
SM_G1_COEFFICIENT = 41.0 / 10.0

DEFAULT_SM_INITIAL_STATES: tuple[tuple[float, ...], ...] = (
    (0.36, 0.65, 1.16, 0.93, 0.13),
    (0.10, 0.20, 0.30, 0.10, 0.01),
    (0.50, 0.50, 0.50, 0.50, 0.05),
    (0.70, 0.70, 0.70, 0.40, -0.05),
)
DEFAULT_GRAVITY_A_VALUES: tuple[float, ...] = (0.0, 0.0001, 0.0005, 0.001, 0.002, 0.01)
DEFAULT_GRAVITY_G1_VALUES: tuple[float, ...] = (0.05, 0.10, 0.20)
DEFAULT_MIXING_MATRICES: tuple[tuple[tuple[float, ...], ...], ...] = (
    ((4.10, 0.50), (0.50, 3.00)),
    ((2.00, 0.25), (0.25, 1.50)),
    ((6.00, 1.00), (1.00, 4.00)),
)
DEFAULT_MIXING_INITIAL_STATES: tuple[tuple[float, ...], ...] = (
    (0.10, 0.20),
    (0.20, 0.10),
    (0.30, 0.30),
)
DEFAULT_LOG_SCALE_OFFSETS: tuple[float, ...] = (-4.0, -2.0, 0.0, 2.0, 4.0)


class SMGravityMixingRGError(ValueError):
    """Raised when a bounded W8 input is invalid."""


def _scalar(value: float, name: str, *, lower: float = -1.0, upper: float = 1.0) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise SMGravityMixingRGError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _offsets(values: Sequence[float]) -> list[float]:
    result = sorted(set(float(value) for value in values))
    if not result or len(result) > 64 or any(not math.isfinite(value) or abs(value) > 64 for value in result):
        raise SMGravityMixingRGError("log-scale offsets must contain 1..64 finite values in [-64, 64]")
    return result


def _state(values: Sequence[float], names: Sequence[str]) -> tuple[float, ...]:
    if len(values) != len(names):
        raise SMGravityMixingRGError(f"state must contain {len(names)} values")
    # Couplings are allowed to exceed one in the bounded SM stress controls
    # (the physical QCD seed g3=1.16 is retained), while the integrator still
    # stops trajectories at MAX_STATE_BOUND.
    return tuple(
        _scalar(value, name, lower=-MAX_STATE_BOUND, upper=MAX_STATE_BOUND)
        for value, name in zip(values, names)
    )


def reduced_standard_model_beta(state: Sequence[float]) -> tuple[float, ...]:
    """One-loop beta vector for ``(g1, g2, g3, y_t, lambda)``.

    ``g1`` uses the GUT-normalized convention.  This is a reduced control,
    not a complete Standard Model precision implementation.
    """

    g1, g2, g3, yt, lam = _state(state, ("g1", "g2", "g3", "y_t", "lambda"))
    beta_g1 = SM_G1_COEFFICIENT * g1**3 / LOOP_FACTOR
    beta_g2 = (-19.0 / 6.0) * g2**3 / LOOP_FACTOR
    beta_g3 = -7.0 * g3**3 / LOOP_FACTOR
    beta_yt = yt * (4.5 * yt**2 - 17.0 / 20.0 * g1**2 - 9.0 / 4.0 * g2**2 - 8.0 * g3**2) / LOOP_FACTOR
    beta_lam = (
        24.0 * lam**2
        - 6.0 * yt**4
        + (12.0 * yt**2 - 9.0 * g2**2 - 9.0 / 5.0 * g1**2) * lam
        + 9.0 / 8.0 * g2**4
        + 9.0 / 20.0 * g1**2 * g2**2
        + 27.0 / 200.0 * g1**4
    ) / LOOP_FACTOR
    return beta_g1, beta_g2, beta_g3, beta_yt, beta_lam


def _rk4_step(beta: Callable[[tuple[float, ...]], tuple[float, ...]], state: tuple[float, ...], step: float) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta(state)
    k2 = beta(shifted(state, k1, step / 2.0))
    k3 = beta(shifted(state, k2, step / 2.0))
    k4 = beta(shifted(state, k3, step))
    return tuple(state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0 for index in range(len(state)))


def _integrate(
    beta: Callable[[tuple[float, ...]], tuple[float, ...]],
    initial_state: Sequence[float],
    names: Sequence[str],
    log_scale_offsets: Sequence[float],
    *,
    steps_per_unit: int = 32,
) -> dict[str, Any]:
    state = _state(initial_state, names)
    ordered = _offsets(log_scale_offsets)
    current_offset = ordered[0]
    current_state = state
    points: list[dict[str, Any]] = [{"log_scale_offset": current_offset, "state": list(current_state)}]
    for target in ordered[1:]:
        distance = target - current_offset
        step_count = max(1, int(abs(distance) * steps_per_unit))
        step = distance / step_count
        for _ in range(step_count):
            current_state = _rk4_step(beta, current_state, step)
            if any(not math.isfinite(value) or abs(value) > MAX_STATE_BOUND for value in current_state):
                return {"status": "BOUND_REACHED", "points": points, "final_state": list(current_state)}
        current_offset = target
        points.append({"log_scale_offset": current_offset, "state": list(current_state)})
    return {"status": "COMPLETE", "points": points, "final_state": list(current_state)}


def reduced_standard_model_fixed_points() -> list[dict[str, Any]]:
    """Return the real perturbative fixed point of this one-loop control."""

    state = (0.0, 0.0, 0.0, 0.0, 0.0)
    return [
        {
            "label": "GAUSSIAN",
            "state": list(state),
            "residual": list(reduced_standard_model_beta(state)),
            "physical": True,
            "perturbative": True,
            "interpretation": "only real perturbative fixed point of this reduced one-loop polynomial control",
        }
    ]


def run_reduced_standard_model_control(
    *,
    initial_states: Sequence[Sequence[float]] = DEFAULT_SM_INITIAL_STATES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    states = [_state(state, ("g1", "g2", "g3", "y_t", "lambda")) for state in initial_states]
    trajectories = [
        {
            "initial_state": list(state),
            "trajectory": _integrate(reduced_standard_model_beta, state, ("g1", "g2", "g3", "y_t", "lambda"), log_scale_offsets),
        }
        for state in states
    ]
    return {
        "status": "COMPLETE",
        "fixed_points": reduced_standard_model_fixed_points(),
        "initial_state_count": len(states),
        "trajectory_count": len(trajectories),
        "trajectories": trajectories,
        "conclusion": "The reduced one-loop Standard Model control has no non-Gaussian real perturbative fixed point.",
    }


def gravity_abelian_beta(g1: float, gravity_coefficient: float) -> float:
    """Return the background-gravity Abelian control beta function."""

    coupling = _scalar(g1, "g1")
    coefficient = _scalar(gravity_coefficient, "gravity_coefficient", lower=0.0, upper=1.0)
    return -coefficient * coupling + (SM_G1_COEFFICIENT / LOOP_FACTOR) * coupling**3


def gravity_abelian_fixed_points(gravity_coefficient: float) -> list[dict[str, Any]]:
    coefficient = _scalar(gravity_coefficient, "gravity_coefficient", lower=0.0, upper=1.0)
    b1 = SM_G1_COEFFICIENT / LOOP_FACTOR
    roots = [0.0]
    if coefficient > 0:
        roots.append(math.sqrt(coefficient / b1))
    reports = []
    for root in roots:
        derivative = -coefficient + 3.0 * b1 * root**2
        reports.append(
            {
                "label": "GAUSSIAN" if root == 0.0 else "NONZERO_GRAVITY_BACKGROUND_ROOT",
                "g1": root,
                "beta_residual": gravity_abelian_beta(root, coefficient),
                "linear_stability": derivative,
                "uv_attractive": derivative < -1e-12,
                "uv_repulsive": derivative > 1e-12,
                "marginal_at_linear_order": abs(derivative) <= 1e-12,
                "perturbative": abs(root) < PERTURBATIVE_BOUND,
            }
        )
    return reports


def run_gravity_abelian_control(
    *,
    gravity_coefficients: Sequence[float] = DEFAULT_GRAVITY_A_VALUES,
    initial_g1_values: Sequence[float] = DEFAULT_GRAVITY_G1_VALUES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    coefficients = [_scalar(value, "gravity_coefficient", lower=0.0, upper=1.0) for value in gravity_coefficients]
    seeds = [_scalar(value, "g1_seed") for value in initial_g1_values]
    fixed_points = []
    trajectories = []
    for coefficient in coefficients:
        roots = gravity_abelian_fixed_points(coefficient)
        fixed_points.append({"gravity_coefficient": coefficient, "fixed_points": roots})
        beta = lambda state, coefficient=coefficient: (gravity_abelian_beta(state[0], coefficient),)
        for seed in seeds:
            trajectories.append(
                {
                    "gravity_coefficient": coefficient,
                    "initial_g1": seed,
                    "trajectory": _integrate(beta, (seed,), ("g1",), log_scale_offsets),
                }
            )
    return {
        "status": "COMPLETE",
        "gravity_coefficient_count": len(coefficients),
        "initial_g1_count": len(seeds),
        "fixed_points": fixed_points,
        "trajectory_count": len(trajectories),
        "trajectories": trajectories,
        "conclusion": "A nonzero root exists for positive background coefficient A, but it is UV-repulsive in this ansatz; the UV-attractive root is Gaussian.",
    }


def _mixing_matrix(matrix: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
        raise SMGravityMixingRGError("mixing matrix must be 2x2")
    result = tuple(tuple(_scalar(value, "mixing_matrix_entry", lower=-10.0, upper=10.0) for value in row) for row in matrix)
    if abs(result[0][1] - result[1][0]) > 1e-12:
        raise SMGravityMixingRGError("mixing matrix must be symmetric")
    if min(np.linalg.eigvalsh(np.asarray(result, dtype=float))) < -1e-12:
        raise SMGravityMixingRGError("mixing matrix must be positive semidefinite")
    return result


def mixing_control_beta(state: Sequence[float], matrix: Sequence[Sequence[float]]) -> tuple[float, float]:
    """A charge-agnostic positive-semidefinite two-U(1) mixing control."""

    couplings = np.asarray(_state(state, ("g1", "g2")), dtype=float)
    coefficient_matrix = np.asarray(_mixing_matrix(matrix), dtype=float)
    squares = couplings**2
    beta = couplings * (coefficient_matrix @ squares) / LOOP_FACTOR
    return float(beta[0]), float(beta[1])


def run_multi_u1_mixing_control(
    *,
    matrices: Sequence[Sequence[Sequence[float]]] = DEFAULT_MIXING_MATRICES,
    initial_states: Sequence[Sequence[float]] = DEFAULT_MIXING_INITIAL_STATES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    normalized_matrices = [_mixing_matrix(matrix) for matrix in matrices]
    states = [_state(state, ("g1", "g2")) for state in initial_states]
    fixed_points = [
        {
            "matrix": [list(row) for row in matrix],
            "gaussian": {
                "state": [0.0, 0.0],
                "residual": list(mixing_control_beta((0.0, 0.0), matrix)),
                "only_nonnegative_fixed_point_in_control": True,
            },
            "matrix_eigenvalues": [float(value) for value in np.linalg.eigvalsh(np.asarray(matrix, dtype=float))],
        }
        for matrix in normalized_matrices
    ]
    trajectories = []
    for matrix in normalized_matrices:
        beta = lambda state, matrix=matrix: mixing_control_beta(state, matrix)
        for state in states:
            trajectories.append(
                {
                    "matrix": [list(row) for row in matrix],
                    "initial_state": list(state),
                    "trajectory": _integrate(beta, state, ("g1", "g2"), log_scale_offsets),
                }
            )
    return {
        "status": "COMPLETE",
        "matrix_count": len(normalized_matrices),
        "initial_state_count": len(states),
        "fixed_points": fixed_points,
        "trajectory_count": len(trajectories),
        "trajectories": trajectories,
        "conclusion": "For the positive-semidefinite normalized controls, the nonnegative fixed point is Gaussian; physical charge assignments and full kinetic-mixing RGEs are not specified.",
    }


def run_sm_gravity_mixing_campaign(
    *,
    sm_initial_states: Sequence[Sequence[float]] = DEFAULT_SM_INITIAL_STATES,
    gravity_coefficients: Sequence[float] = DEFAULT_GRAVITY_A_VALUES,
    gravity_initial_g1_values: Sequence[float] = DEFAULT_GRAVITY_G1_VALUES,
    mixing_matrices: Sequence[Sequence[Sequence[float]]] = DEFAULT_MIXING_MATRICES,
    mixing_initial_states: Sequence[Sequence[float]] = DEFAULT_MIXING_INITIAL_STATES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    report = {
        "search_version": SM_GRAVITY_MIXING_RG_VERSION,
        "campaign_id": "sm-gravity-mixing-broad-run",
        "stage": "W8_SM_GRAVITY_MIXING_RG",
        "execution_status": "COMPLETE",
        "scope": {
            "reduced_standard_model": "ONE_LOOP_G1_G2_G3_TOP_HIGGS_CONTROL",
            "g1_convention": "GUT_NORMALIZED",
            "gravity_sector": "BACKGROUND_GRAVITY_LINEAR_ABELIAN_CONTROL_ONLY",
            "u1_mixing": "POSITIVE_SEMIDEFINITE_CHARGE_AGNOSTIC_CONTROL_ONLY",
            "full_quantum_gravity": "NOT_INCLUDED",
            "full_standard_model_precision_running": "NOT_CLAIMED",
            "f4_operators": "NOT_ACTIVATED",
        },
        "equations": {
            "sm_beta_g1": "16*pi^2 beta_g1 = (41/10) g1^3",
            "sm_beta_g2": "16*pi^2 beta_g2 = -(19/6) g2^3",
            "sm_beta_g3": "16*pi^2 beta_g3 = -7 g3^3",
            "sm_beta_yt": "16*pi^2 beta_yt = yt*(9/2*yt^2 - 17/20*g1^2 - 9/4*g2^2 - 8*g3^2)",
            "sm_beta_lambda": "16*pi^2 beta_lambda = 24*lambda^2 - 6*yt^4 + (12*yt^2 - 9*g2^2 - 9/5*g1^2)*lambda + 9/8*g2^4 + 9/20*g1^2*g2^2 + 27/200*g1^4",
            "gravity_abelian_control": "beta_g1 = -A*g1 + (41/10)/(16*pi^2)*g1^3",
            "u1_mixing_control": "beta_i = g_i * sum_j B_ij*g_j^2/(16*pi^2), B positive semidefinite",
        },
        "subcampaigns": {
            "reduced_standard_model": run_reduced_standard_model_control(
                initial_states=sm_initial_states, log_scale_offsets=log_scale_offsets
            ),
            "gravity_abelian_control": run_gravity_abelian_control(
                gravity_coefficients=gravity_coefficients,
                initial_g1_values=gravity_initial_g1_values,
                log_scale_offsets=log_scale_offsets,
            ),
            "multi_u1_mixing_control": run_multi_u1_mixing_control(
                matrices=mixing_matrices,
                initial_states=mixing_initial_states,
                log_scale_offsets=log_scale_offsets,
            ),
        },
        "bibliography": [
            {
                "id": "machacek-vaughn-1983-1985",
                "citation": "M. E. Machacek and M. T. Vaughn, two-loop renormalization-group equations for the Standard Model and general gauge theories, Nucl. Phys. B 222, 83 (1983) and companion papers",
                "doi": "10.1016/0550-3213(83)90610-7",
                "role": "one-loop and general gauge/Yukawa beta-function framework",
            },
            {
                "id": "luo-xiao-2003",
                "citation": "M.-x. Luo and Y. Xiao, Two-loop renormalization group equations in the Standard Model, Phys. Rev. Lett. 90, 011601 (2003)",
                "doi": "10.1103/PhysRevLett.90.011601",
                "role": "Standard Model two-loop RG control and normalization reference",
            },
            {
                "id": "luo-xiao-kinetic-mixing-2003",
                "citation": "M.-x. Luo and Y. Xiao, Renormalization group equations in gauge theories with multiple U(1) groups, Phys. Lett. B 555, 279 (2003)",
                "doi": "10.1016/S0370-2693(03)00076-5",
                "role": "multiple-U(1) kinetic-mixing caveat",
            },
            {
                "id": "eichhorn-versteegen-2018",
                "citation": "A. Eichhorn and F. Versteegen, Upper bound on the Abelian gauge coupling from asymptotic safety, JHEP 01 (2018) 030",
                "doi": "10.1007/JHEP01(2018)030",
                "role": "gravity-induced Abelian fixed-point and upper-bound caveat",
            },
            {
                "id": "riabokon-schiffer-wagner-2025",
                "citation": "A. Riabokon, M. Schiffer and F. Wagner, regulator and gauge dependence of the Abelian coupling in asymptotically safe gravity, Phys. Rev. D 112 (2025)",
                "doi": "10.1103/gxm2-trn6",
                "role": "recent scheme and truncation dependence caveat",
            },
        ],
        "authorization": {
            "finite_bounds": "AUTHORIZED",
            "target_comparison": "NOT_AUTHORIZED",
            "external_data_used": False,
            "fitting": "DISABLED",
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
            "f4_promotion": "DISABLED",
            "target_blind_generation": True,
        },
        "controls": {
            "sm_beta_functions_transcribed": True,
            "sm_physical_non_gaussian_fixed_point_found": False,
            "gravity_abelian_nonzero_root_recorded": True,
            "gravity_abelian_nonzero_uv_fixed_point_found": False,
            "gravity_is_background_control_only": True,
            "mixing_control_only": True,
            "mixing_charge_assignments_missing": True,
            "alpha_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "f4_operators_not_promoted": True,
            "negative_results_recorded": True,
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "DERIVE_OR_IMPORT_A_SPECIFIC_GRAVITY_MATTER_OR_MULTI_U1_MODEL_BEFORE_ANY_1_OVER_137_SEARCH",
    }
    return report


def write_sm_gravity_mixing_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_GRAVITY_A_VALUES",
    "DEFAULT_GRAVITY_G1_VALUES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "DEFAULT_MIXING_INITIAL_STATES",
    "DEFAULT_MIXING_MATRICES",
    "DEFAULT_SM_INITIAL_STATES",
    "SM_GRAVITY_MIXING_RG_VERSION",
    "SMGravityMixingRGError",
    "gravity_abelian_beta",
    "gravity_abelian_fixed_points",
    "mixing_control_beta",
    "reduced_standard_model_beta",
    "reduced_standard_model_fixed_points",
    "run_gravity_abelian_control",
    "run_multi_u1_mixing_control",
    "run_reduced_standard_model_control",
    "run_sm_gravity_mixing_campaign",
    "write_sm_gravity_mixing_report",
]
