"""Literature-anchored coupled gauge-Yukawa plus Abelian RG campaign.

The gauge-Yukawa beta functions are the NLO equations of Litim and Sannino,
arXiv:1406.2337, Eq. (23).  The Abelian coupling is included as a deliberately
decoupled QED-like spectator at this order.  This lets the laboratory test two
different statements in one run:

* opposite-sign gauge/Yukawa contributions can generate a non-Gaussian UV
  fixed point in a controlled non-Abelian subsector;
* that fixed point does not automatically determine a non-zero electromagnetic
  coupling when the Abelian beta function remains positive.

No experimental value of alpha is used, and no claim is made for the full
Standard Model or quantum gravity.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from physics_lab.search.qed_rg_pilot import QED_ONE_LOOP_BETA_COEFFICIENT


GAUGE_YUKAWA_EM_RG_VERSION = "gauge-yukawa-em-rg-v1"
DEFAULT_EPSILON_VALUES = (0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50)
DEFAULT_ALPHA_EM_VALUES = (0.001, 0.01, 0.10)
DEFAULT_LOG_SCALE_OFFSETS = (-4.0, -2.0, 0.0, 2.0, 4.0)
PERTURBATIVE_COUPLING_BOUND = 0.1


class GaugeYukawaEMRGError(ValueError):
    """Raised when a bounded coupled RG input is invalid."""


def _validate_epsilon(value: float) -> float:
    epsilon = float(value)
    if not math.isfinite(epsilon) or epsilon <= 0 or epsilon > 1:
        raise GaugeYukawaEMRGError("epsilon must be finite and in (0, 1]")
    return epsilon


def _validate_alpha(value: float, name: str = "alpha") -> float:
    alpha = float(value)
    if not math.isfinite(alpha) or alpha < 0 or alpha > 1:
        raise GaugeYukawaEMRGError(f"{name} must be finite and in [0, 1]")
    return alpha


def _validate_offsets(values: Sequence[float]) -> list[float]:
    offsets = [float(value) for value in values]
    if not offsets or len(offsets) > 32 or any(not math.isfinite(value) or abs(value) > 32 for value in offsets):
        raise GaugeYukawaEMRGError("log scale offsets must contain 1..32 values in [-32, 32]")
    return offsets


def beta_vector(epsilon: float, state: Sequence[float]) -> tuple[float, float, float]:
    """Return beta(alpha_em, alpha_g, alpha_y) at the literature truncation."""
    epsilon_value = _validate_epsilon(epsilon)
    if len(state) != 3:
        raise GaugeYukawaEMRGError("state must contain alpha_em, alpha_g and alpha_y")
    alpha_em, alpha_g, alpha_y = (_validate_alpha(value, name) for value, name in zip(state, ("alpha_em", "alpha_g", "alpha_y")))
    gauge_linear = 4.0 * epsilon_value / 3.0
    gauge_two_loop = 25.0 + 26.0 * epsilon_value / 3.0
    gauge_yukawa = 2.0 * (5.5 + epsilon_value) ** 2
    yukawa_self = 13.0 + 2.0 * epsilon_value
    return (
        QED_ONE_LOOP_BETA_COEFFICIENT * alpha_em**2,
        alpha_g**2 * (gauge_linear + gauge_two_loop * alpha_g - gauge_yukawa * alpha_y),
        alpha_y * (yukawa_self * alpha_y - 6.0 * alpha_g),
    )


def gauge_yukawa_fixed_point(epsilon: float) -> dict[str, Any]:
    """Return the Gaussian and interacting fixed points for a given epsilon."""
    epsilon_value = _validate_epsilon(epsilon)
    gauge_linear = 4.0 * epsilon_value / 3.0
    gauge_two_loop = 25.0 + 26.0 * epsilon_value / 3.0
    gauge_yukawa = 2.0 * (5.5 + epsilon_value) ** 2
    yukawa_self = 13.0 + 2.0 * epsilon_value
    effective_gauge_coefficient = gauge_two_loop - gauge_yukawa * 6.0 / yukawa_self
    alpha_g = -gauge_linear / effective_gauge_coefficient
    alpha_y = 6.0 * alpha_g / yukawa_self

    gaussian = {"label": "GAUSSIAN", "alpha_em": 0.0, "alpha_g": 0.0, "alpha_y": 0.0}
    interacting = {
        "label": "GAUGE_YUKAWA_INTERACTING",
        "alpha_em": 0.0,
        "alpha_g": alpha_g,
        "alpha_y": alpha_y,
        "physical": alpha_g > 0 and alpha_y > 0,
        "perturbative": max(alpha_g, alpha_y) < PERTURBATIVE_COUPLING_BOUND,
    }
    return {
        "epsilon": epsilon_value,
        "gaussian": gaussian,
        "interacting": interacting,
        "effective_gauge_coefficient": effective_gauge_coefficient,
        "alpha_em_nonzero_fixed_point": False,
    }


def stability_matrix(epsilon: float, state: Sequence[float]) -> list[list[float]]:
    """Return the analytic Jacobian of the coupled beta vector."""
    epsilon_value = _validate_epsilon(epsilon)
    alpha_em, alpha_g, alpha_y = (_validate_alpha(value, name) for value, name in zip(state, ("alpha_em", "alpha_g", "alpha_y")))
    gauge_linear = 4.0 * epsilon_value / 3.0
    gauge_two_loop = 25.0 + 26.0 * epsilon_value / 3.0
    gauge_yukawa = 2.0 * (5.5 + epsilon_value) ** 2
    yukawa_self = 13.0 + 2.0 * epsilon_value
    return [
        [2.0 * QED_ONE_LOOP_BETA_COEFFICIENT * alpha_em, 0.0, 0.0],
        [0.0, 2.0 * alpha_g * (gauge_linear + gauge_two_loop * alpha_g - gauge_yukawa * alpha_y) + alpha_g**2 * gauge_two_loop, -gauge_yukawa * alpha_g**2],
        [0.0, -6.0 * alpha_y, 2.0 * yukawa_self * alpha_y - 6.0 * alpha_g],
    ]


def _eigenvalues(matrix: Sequence[Sequence[float]]) -> list[float]:
    values = np.linalg.eigvals(np.asarray(matrix, dtype=float))
    return sorted(float(value.real) for value in values if abs(float(value.imag)) < 1e-10)


def _rk4_step(epsilon: float, state: tuple[float, float, float], step: float) -> tuple[float, float, float]:
    def add(base: tuple[float, float, float], direction: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
        return tuple(base[index] + scale * direction[index] for index in range(3))

    k1 = beta_vector(epsilon, state)
    k2 = beta_vector(epsilon, add(state, k1, step / 2.0))
    k3 = beta_vector(epsilon, add(state, k2, step / 2.0))
    k4 = beta_vector(epsilon, add(state, k3, step))
    return tuple(state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0 for index in range(3))


def integrate_trajectory(
    epsilon: float,
    initial_state: Sequence[float],
    *,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
    steps_per_unit: int = 32,
) -> dict[str, Any]:
    """Integrate a bounded trajectory between the registered scale offsets."""
    epsilon_value = _validate_epsilon(epsilon)
    state = tuple(_validate_alpha(value, name) for value, name in zip(initial_state, ("alpha_em", "alpha_g", "alpha_y")))
    offsets = _validate_offsets(log_scale_offsets)
    ordered = sorted(set(offsets))
    current_offset = ordered[0]
    current_state = state
    points: list[dict[str, Any]] = [{"log_scale_offset": current_offset, "state": list(current_state)}]
    status = "COMPLETE"
    for target in ordered[1:]:
        distance = target - current_offset
        step_count = max(1, int(abs(distance) * steps_per_unit))
        step = distance / step_count
        for _ in range(step_count):
            current_state = _rk4_step(epsilon_value, current_state, step)
            if any(not math.isfinite(value) or value < 0 or value > 10 for value in current_state):
                status = "BOUND_REACHED"
                return {"status": status, "points": points, "final_state": list(current_state)}
        current_offset = target
        points.append({"log_scale_offset": current_offset, "state": list(current_state)})
    return {"status": status, "points": points, "final_state": list(current_state)}


def run_gauge_yukawa_em_campaign(
    *,
    epsilon_values: Sequence[float] = DEFAULT_EPSILON_VALUES,
    alpha_em_values: Sequence[float] = DEFAULT_ALPHA_EM_VALUES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    """Scan literature-anchored fixed points and bounded coupled trajectories."""
    epsilons = [_validate_epsilon(value) for value in epsilon_values]
    alpha_em_values_validated = [_validate_alpha(value, "alpha_em_seed") for value in alpha_em_values]
    offsets = _validate_offsets(log_scale_offsets)
    fixed_point_reports: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []

    for epsilon in epsilons:
        fixed_points = gauge_yukawa_fixed_point(epsilon)
        interacting = fixed_points["interacting"]
        interacting_state = (0.0, interacting["alpha_g"], interacting["alpha_y"])
        eigenvalues = _eigenvalues(stability_matrix(epsilon, interacting_state))
        fixed_point_reports.append(
            {
                **fixed_points,
                "interacting_stability_eigenvalues": eigenvalues,
                "interacting_uv_attractive_directions": sum(value < -1e-10 for value in eigenvalues),
                "interacting_ir_attractive_directions": sum(value > 1e-10 for value in eigenvalues),
                "interacting_marginal_directions": sum(abs(value) <= 1e-10 for value in eigenvalues),
                "interacting_residual": list(beta_vector(epsilon, interacting_state)),
            }
        )
        for alpha_em_seed in alpha_em_values_validated:
            state = (alpha_em_seed, interacting["alpha_g"], interacting["alpha_y"])
            trajectory = integrate_trajectory(epsilon, state, log_scale_offsets=offsets)
            trajectories.append(
                {
                    "epsilon": epsilon,
                    "initial_state": list(state),
                    "background_fixed_point": "GAUGE_YUKAWA_INTERACTING",
                    "trajectory": trajectory,
                }
            )

    physical_interacting = [item for item in fixed_point_reports if item["interacting"]["physical"]]
    perturbative_interacting = [item for item in physical_interacting if item["interacting"]["perturbative"]]
    return {
        "search_version": GAUGE_YUKAWA_EM_RG_VERSION,
        "campaign_id": "gauge-yukawa-electromagnetic-rg-broad-run",
        "stage": "W6_COUPLED_GAUGE_YUKAWA_EM_RG",
        "execution_status": "COMPLETE",
        "scope": {
            "base_theory": "Litim-Sannino gauge-Yukawa truncation plus decoupled one-loop QED spectator",
            "gauge_yukawa_order": "gauge two-loop plus Yukawa one-loop",
            "abelian_order": "QED one-loop",
            "epsilon_role": "VENEZIANO_EXPANSION_CONTROL_PARAMETER",
            "alpha_em_role": "DYNAMICAL_STATE_VARIABLE_ONLY",
            "full_standard_model": "NOT_CLAIMED",
            "quantum_gravity": "NOT_INCLUDED",
            "f4_operators": "NOT_ACTIVATED",
        },
        "equations": {
            "beta_alpha_em": "b_em*alpha_em^2 with b_em=2/(3*pi)",
            "beta_alpha_g": "alpha_g^2*[4*epsilon/3+(25+26*epsilon/3)*alpha_g-2*(11/2+epsilon)^2*alpha_y]",
            "beta_alpha_y": "alpha_y*[(13+2*epsilon)*alpha_y-6*alpha_g]",
            "interacting_fixed_point": "alpha_em*=0, alpha_y*=6*alpha_g*/(13+2*epsilon)",
        },
        "epsilon_count": len(epsilons),
        "fixed_point_count": len(fixed_point_reports),
        "trajectory_count": len(trajectories),
        "physical_interacting_fixed_point_count": len(physical_interacting),
        "perturbative_interacting_fixed_point_count": len(perturbative_interacting),
        "fixed_points": fixed_point_reports,
        "trajectories": trajectories,
        "electromagnetic_conclusion": {
            "nonzero_alpha_em_fixed_point_found": False,
            "alpha_em_fixed_point_value": 0.0,
            "alpha_em_is_constrained_by_gauge_yukawa_fixed_point": False,
            "reason": "The Abelian beta function is positive and decoupled at this truncation.",
        },
        "bibliography": [
            {
                "id": "litim-sannino-2014",
                "citation": "D. F. Litim and F. Sannino, Asymptotic safety guaranteed, JHEP 12 (2014) 178",
                "doi": "10.1007/JHEP12(2014)178",
                "url": "https://arxiv.org/abs/1406.2337",
                "role": "source of the coupled gauge-Yukawa beta functions",
            },
            {
                "id": "bond-litim-2017",
                "citation": "A. D. Bond and D. F. Litim, Theorems for Asymptotic Safety of Gauge Theories, Eur. Phys. J. C 77 (2017) 429",
                "doi": "10.1140/epjc/s10052-017-4976-5",
                "url": "https://arxiv.org/abs/1608.00519",
                "role": "fixed-point sign conditions and weak-coupling classification",
            },
            {
                "id": "held-2020",
                "citation": "A. Held, Effective asymptotic safety and its predictive power: Gauge-Yukawa theories, Front. Phys. 8 (2020) 341",
                "doi": "10.3389/fphy.2020.00341",
                "url": "https://arxiv.org/abs/2003.13642",
                "role": "predictivity and Abelian-sector caveats",
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
            "literature_beta_functions_transcribed": True,
            "interacting_gauge_yukawa_fixed_points_found": len(physical_interacting) == len(epsilons),
            "fixed_point_residuals_recorded": True,
            "stability_matrix_recorded": True,
            "alpha_em_nonzero_fixed_point_found": False,
            "alpha_em_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "f4_operators_not_promoted": True,
            "perturbative_validity_flagged": True,
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "ADD_SCALAR_QUARTIC_AND_FULL_ABELIAN_MIXING_OR_IMPORT_GRAVITY_BETA_FUNCTIONS",
    }


def write_gauge_yukawa_em_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_ALPHA_EM_VALUES",
    "DEFAULT_EPSILON_VALUES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "GAUGE_YUKAWA_EM_RG_VERSION",
    "GaugeYukawaEMRGError",
    "beta_vector",
    "gauge_yukawa_fixed_point",
    "integrate_trajectory",
    "run_gauge_yukawa_em_campaign",
    "stability_matrix",
    "write_gauge_yukawa_em_report",
]
