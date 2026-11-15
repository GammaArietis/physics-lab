"""W7 scalar completion of the literature-anchored gauge-Yukawa RG run.

This module adds the one-loop scalar quartic beta functions used in the
Litim-Sannino analysis to the W6 gauge-Yukawa plus Abelian spectator system.
The truncation is deliberately labelled mixed-order: gauge at two loops,
Yukawa at one loop, scalar quartics at one loop and Abelian QED at one loop.
It is a consistency run, not a full Standard Model or four-loop calculation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from physics_lab.search.gauge_yukawa_em_rg import (
    DEFAULT_ALPHA_EM_VALUES,
    DEFAULT_EPSILON_VALUES,
    DEFAULT_LOG_SCALE_OFFSETS,
    PERTURBATIVE_COUPLING_BOUND,
)
from physics_lab.search.qed_rg_pilot import QED_ONE_LOOP_BETA_COEFFICIENT


GAUGE_YUKAWA_SCALAR_EM_RG_VERSION = "gauge-yukawa-scalar-em-rg-v1"


class GaugeYukawaScalarEMRGError(ValueError):
    """Raised when a bounded scalar-completed RG input is invalid."""


def _epsilon(value: float) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0 or result > 1:
        raise GaugeYukawaScalarEMRGError("epsilon must be finite and in (0, 1]")
    return result


def _coupling(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1:
        raise GaugeYukawaScalarEMRGError(f"{name} must be finite and in [-1, 1]")
    return result


def _scalar_coupling(value: float, name: str = "alpha_v") -> float:
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1:
        raise GaugeYukawaScalarEMRGError(f"{name} must be finite and in [-1, 1]")
    return result


def _offsets(values: Sequence[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result or len(result) > 32 or any(not math.isfinite(value) or abs(value) > 32 for value in result):
        raise GaugeYukawaScalarEMRGError("log scale offsets must contain 1..32 values in [-32, 32]")
    return result


def beta_vector(epsilon: float, state: Sequence[float]) -> tuple[float, float, float, float, float]:
    """Return beta(alpha_em, alpha_g, alpha_y, alpha_h, alpha_v)."""
    eps = _epsilon(epsilon)
    if len(state) != 5:
        raise GaugeYukawaScalarEMRGError("state must contain alpha_em, alpha_g, alpha_y, alpha_h and alpha_v")
    alpha_em, alpha_g, alpha_y, alpha_h = tuple(
        _coupling(value, name) for value, name in zip(state[:4], ("alpha_em", "alpha_g", "alpha_y", "alpha_h"))
    )
    alpha_v = _scalar_coupling(state[4])
    return (
        QED_ONE_LOOP_BETA_COEFFICIENT * alpha_em**2,
        alpha_g**2 * (4.0 * eps / 3.0 + (25.0 + 26.0 * eps / 3.0) * alpha_g - 2.0 * (5.5 + eps) ** 2 * alpha_y),
        alpha_y * ((13.0 + 2.0 * eps) * alpha_y - 6.0 * alpha_g),
        -(11.0 + 2.0 * eps) * alpha_y**2 + 4.0 * alpha_h * (alpha_y + 2.0 * alpha_h),
        12.0 * alpha_h**2 + 4.0 * alpha_v * (alpha_v + 4.0 * alpha_h + alpha_y),
    )


def _gauge_yukawa_values(eps: float) -> tuple[float, float]:
    gauge_linear = 4.0 * eps / 3.0
    gauge_two_loop = 25.0 + 26.0 * eps / 3.0
    gauge_yukawa = 2.0 * (5.5 + eps) ** 2
    yukawa_self = 13.0 + 2.0 * eps
    alpha_g = -gauge_linear / (gauge_two_loop - gauge_yukawa * 6.0 / yukawa_self)
    alpha_y = 6.0 * alpha_g / yukawa_self
    return alpha_g, alpha_y


def fixed_point_branches(epsilon: float) -> dict[str, Any]:
    """Return Gaussian and both scalar-quartic branches at leading order."""
    eps = _epsilon(epsilon)
    alpha_g, alpha_y = _gauge_yukawa_values(eps)
    # Solve beta_h=0 exactly in this mixed-order truncation.  Its small-epsilon
    # expansion starts with (sqrt(23)-1)*epsilon/19, as in the literature.
    alpha_h = (-4.0 * alpha_y + math.sqrt(16.0 * alpha_y**2 + 32.0 * (11.0 + 2.0 * eps) * alpha_y**2)) / 16.0
    linear = 4.0 * alpha_h + alpha_y
    discriminant = linear**2 - 12.0 * alpha_h**2
    if discriminant < 0:
        raise GaugeYukawaScalarEMRGError("scalar quartic fixed-point discriminant is negative")
    alpha_v_stable = (-linear + math.sqrt(discriminant)) / 2.0
    alpha_v_unstable = (-linear - math.sqrt(discriminant)) / 2.0
    branches = []
    for label, alpha_v in (
        ("FP1_STABLE_POTENTIAL_CANDIDATE", alpha_v_stable),
        ("FP2_UNSTABLE_POTENTIAL_CANDIDATE", alpha_v_unstable),
    ):
        state = (0.0, alpha_g, alpha_y, alpha_h, alpha_v)
        branches.append(
            {
                "label": label,
                "alpha_em": 0.0,
                "alpha_g": alpha_g,
                "alpha_y": alpha_y,
                "alpha_h": alpha_h,
                "alpha_v": alpha_v,
                "physical_gauge_yukawa": alpha_g > 0 and alpha_y > 0,
                "quartic_potential_proxy_stable": alpha_h + alpha_v > 0,
                "perturbative": max(abs(value) for value in state) < PERTURBATIVE_COUPLING_BOUND,
                "residual": list(beta_vector(eps, state)),
            }
        )
    return {
        "epsilon": eps,
        "gaussian": {"label": "GAUSSIAN", "state": [0.0, 0.0, 0.0, 0.0, 0.0]},
        "branches": branches,
        "alpha_em_nonzero_fixed_point": False,
    }


def stability_matrix(epsilon: float, state: Sequence[float]) -> list[list[float]]:
    """Return the analytic 5x5 stability matrix."""
    eps = _epsilon(epsilon)
    alpha_em, alpha_g, alpha_y, alpha_h = tuple(
        _coupling(value, name) for value, name in zip(state[:4], ("alpha_em", "alpha_g", "alpha_y", "alpha_h"))
    )
    alpha_v = _scalar_coupling(state[4])
    matrix = [[0.0 for _ in range(5)] for _ in range(5)]
    matrix[0][0] = 2.0 * QED_ONE_LOOP_BETA_COEFFICIENT * alpha_em
    matrix[1][1] = 2.0 * alpha_g * (4.0 * eps / 3.0 + (25.0 + 26.0 * eps / 3.0) * alpha_g - 2.0 * (5.5 + eps) ** 2 * alpha_y) + alpha_g**2 * (25.0 + 26.0 * eps / 3.0)
    matrix[1][2] = -2.0 * (5.5 + eps) ** 2 * alpha_g**2
    matrix[2][1] = -6.0 * alpha_y
    matrix[2][2] = 2.0 * (13.0 + 2.0 * eps) * alpha_y - 6.0 * alpha_g
    matrix[3][2] = -2.0 * (11.0 + 2.0 * eps) * alpha_y + 4.0 * alpha_h
    matrix[3][3] = 4.0 * (alpha_y + 4.0 * alpha_h)
    matrix[4][2] = 4.0 * alpha_v
    matrix[4][3] = 24.0 * alpha_h + 16.0 * alpha_v
    matrix[4][4] = 8.0 * alpha_v + 16.0 * alpha_h + 4.0 * alpha_y
    return matrix


def _eigenvalues(matrix: Sequence[Sequence[float]]) -> list[float]:
    values = np.linalg.eigvals(np.asarray(matrix, dtype=float))
    return sorted(float(value.real) for value in values if abs(float(value.imag)) < 1e-10)


def _rk4_step(epsilon: float, state: tuple[float, ...], step: float) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta_vector(epsilon, state)
    k2 = beta_vector(epsilon, shifted(state, k1, step / 2.0))
    k3 = beta_vector(epsilon, shifted(state, k2, step / 2.0))
    k4 = beta_vector(epsilon, shifted(state, k3, step))
    return tuple(state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0 for index in range(len(state)))


def integrate_trajectory(
    epsilon: float,
    initial_state: Sequence[float],
    *,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
    steps_per_unit: int = 32,
) -> dict[str, Any]:
    eps = _epsilon(epsilon)
    state = tuple(_coupling(value, name) for value, name in zip(initial_state[:4], ("alpha_em", "alpha_g", "alpha_y", "alpha_h"))) + (_scalar_coupling(initial_state[4]),)
    ordered = sorted(set(_offsets(log_scale_offsets)))
    current_offset = ordered[0]
    current_state = state
    points: list[dict[str, Any]] = [{"log_scale_offset": current_offset, "state": list(current_state)}]
    for target in ordered[1:]:
        distance = target - current_offset
        step_count = max(1, int(abs(distance) * steps_per_unit))
        step = distance / step_count
        for _ in range(step_count):
            current_state = _rk4_step(eps, current_state, step)
            if any(not math.isfinite(value) or abs(value) > 10 for value in current_state):
                return {"status": "BOUND_REACHED", "points": points, "final_state": list(current_state)}
        current_offset = target
        points.append({"log_scale_offset": current_offset, "state": list(current_state)})
    return {"status": "COMPLETE", "points": points, "final_state": list(current_state)}


def run_gauge_yukawa_scalar_em_campaign(
    *,
    epsilon_values: Sequence[float] = DEFAULT_EPSILON_VALUES,
    alpha_em_values: Sequence[float] = DEFAULT_ALPHA_EM_VALUES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    epsilons = [_epsilon(value) for value in epsilon_values]
    alpha_em_seeds = [_coupling(value, "alpha_em_seed") for value in alpha_em_values]
    fixed_point_reports: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    for eps in epsilons:
        branch_set = fixed_point_branches(eps)
        branch_reports = []
        for branch in branch_set["branches"]:
            state = (0.0, branch["alpha_g"], branch["alpha_y"], branch["alpha_h"], branch["alpha_v"])
            eigenvalues = _eigenvalues(stability_matrix(eps, state))
            branch_reports.append(
                {
                    **branch,
                    "stability_eigenvalues": eigenvalues,
                    "uv_attractive_directions": sum(value < -1e-10 for value in eigenvalues),
                    "ir_attractive_directions": sum(value > 1e-10 for value in eigenvalues),
                    "marginal_directions": sum(abs(value) <= 1e-10 for value in eigenvalues),
                }
            )
            for alpha_em_seed in alpha_em_seeds:
                trajectory_state = (alpha_em_seed, branch["alpha_g"], branch["alpha_y"], branch["alpha_h"], branch["alpha_v"])
                trajectories.append(
                    {
                        "epsilon": eps,
                        "branch": branch["label"],
                        "initial_state": list(trajectory_state),
                        "trajectory": integrate_trajectory(eps, trajectory_state, log_scale_offsets=log_scale_offsets),
                    }
                )
        fixed_point_reports.append({"epsilon": eps, "gaussian": branch_set["gaussian"], "branches": branch_reports})

    return {
        "search_version": GAUGE_YUKAWA_SCALAR_EM_RG_VERSION,
        "campaign_id": "gauge-yukawa-scalar-electromagnetic-rg-broad-run",
        "stage": "W7_COUPLED_GAUGE_YUKAWA_SCALAR_EM_RG",
        "execution_status": "COMPLETE",
        "scope": {
            "base_theory": "Litim-Sannino gauge-Yukawa-scalar truncation plus decoupled one-loop QED spectator",
            "gauge_order": "TWO_LOOP",
            "yukawa_order": "ONE_LOOP",
            "scalar_quartic_order": "ONE_LOOP",
            "abelian_order": "ONE_LOOP",
            "full_standard_model": "NOT_CLAIMED",
            "quantum_gravity": "NOT_INCLUDED",
            "f4_operators": "NOT_ACTIVATED",
        },
        "equations": {
            "beta_alpha_em": "2*alpha_em^2/(3*pi)",
            "beta_alpha_h": "-(11+2*epsilon)*alpha_y^2 + 4*alpha_h*(alpha_y+2*alpha_h)",
            "beta_alpha_v": "12*alpha_h^2 + 4*alpha_v*(alpha_v+4*alpha_h+alpha_y)",
            "fixed_point_scalar_branches": "alpha_h*=(sqrt(23)-1)*epsilon/19; alpha_v solves beta_v=0",
        },
        "epsilon_count": len(epsilons),
        "fixed_point_count": len(fixed_point_reports),
        "trajectory_count": len(trajectories),
        "fixed_points": fixed_point_reports,
        "trajectories": trajectories,
        "electromagnetic_conclusion": {
            "nonzero_alpha_em_fixed_point_found": False,
            "alpha_em_fixed_point_value": 0.0,
            "alpha_em_constrained_by_scalar_completed_system": False,
            "reason": "The Abelian beta function remains positive and decoupled in this truncation.",
        },
        "bibliography": [
            {
                "id": "litim-sannino-2014",
                "citation": "D. F. Litim and F. Sannino, Asymptotic safety guaranteed, JHEP 12 (2014) 178",
                "doi": "10.1007/JHEP12(2014)178",
                "url": "https://arxiv.org/abs/1406.2337",
                "role": "gauge-Yukawa and scalar beta functions",
            },
            {
                "id": "bednyakov-mukhaeva-2024",
                "citation": "A. V. Bednyakov and I. A. Mukhaeva, Asymptotic safety in the Litim-Sannino model at four loops, Phys. Rev. D 109, 065030 (2024)",
                "doi": "10.1103/PhysRevD.109.065030",
                "url": "https://arxiv.org/abs/2312.12128",
                "role": "higher-loop confirmation and perturbative-control caveat",
            },
            {
                "id": "davies-herren-thomsen-2022",
                "citation": "J. Davies, F. Herren and A. E. Thomsen, General gauge-Yukawa-quartic beta-functions at 4-3-2-loop order, JHEP 01 (2022) 051",
                "doi": "10.1007/JHEP01(2022)051",
                "url": "https://doi.org/10.1007/JHEP01(2022)051",
                "role": "general higher-loop beta-function framework",
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
            "scalar_beta_functions_transcribed": True,
            "two_scalar_branches_recorded": True,
            "fixed_point_residuals_recorded": True,
            "stability_matrices_recorded": True,
            "alpha_em_nonzero_fixed_point_found": False,
            "alpha_em_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "f4_operators_not_promoted": True,
            "higher_loop_caveat_recorded": True,
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "COMPARE_MIXED_ORDER_RUN_WITH_HIGHER_LOOP_LITERATURE_OR_ACTIVATE_GRAVITY_MATTER_BETA_SYSTEM",
    }


def write_gauge_yukawa_scalar_em_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "GAUGE_YUKAWA_SCALAR_EM_RG_VERSION",
    "GaugeYukawaScalarEMRGError",
    "beta_vector",
    "fixed_point_branches",
    "integrate_trajectory",
    "run_gauge_yukawa_scalar_em_campaign",
    "stability_matrix",
    "write_gauge_yukawa_scalar_em_report",
]
