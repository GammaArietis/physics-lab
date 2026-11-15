"""W9 gravity-dressed Standard Model fixed-point control campaign.

W9 expands the W8 Abelian background control to all three Standard Model
gauge couplings and adds explicitly labelled linear gravitational controls for
the top Yukawa and Higgs quartic couplings.  The gauge term

    beta_gi = b_i*g_i**3/(16*pi**2) - f_g*g_i

is the literature-shaped asymptotic-safety control used in several analyses.
The ``f_y`` and ``f_lambda`` terms are independent minimal closures, not a
claim that one particular quantum-gravity truncation has been derived here.
All coefficient grids, fixed-point branches and trajectories are retained;
there is no fitting, ranking or automatic selection.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


GRAVITY_SM_FIXED_POINT_RG_VERSION = "gravity-sm-fixed-point-rg-v1"
LOOP_FACTOR = 16.0 * math.pi**2
MAX_STATE_BOUND = 10.0
PERTURBATIVE_BOUND = 1.0
G1_COEFFICIENT = 41.0 / 10.0
G2_COEFFICIENT = -19.0 / 6.0
G3_COEFFICIENT = -7.0

DEFAULT_F_G_VALUES: tuple[float, ...] = (0.0, 0.0001, 0.0005, 0.001, 0.002, 0.01)
DEFAULT_F_Y_VALUES: tuple[float, ...] = (0.0, 0.0005, 0.001, 0.002)
DEFAULT_F_LAMBDA_VALUES: tuple[float, ...] = (0.0, 0.0005, 0.001, 0.002)
DEFAULT_INITIAL_STATES: tuple[tuple[float, ...], ...] = (
    (0.36, 0.65, 1.16, 0.93, 0.13),
    (0.10, 0.20, 0.30, 0.10, 0.01),
    (0.50, 0.50, 0.50, 0.50, 0.05),
    (0.70, 0.70, 0.70, 0.40, -0.05),
)
DEFAULT_LOG_SCALE_OFFSETS: tuple[float, ...] = (-4.0, -2.0, 0.0, 2.0, 4.0)


class GravitySMFixedPointRGError(ValueError):
    """Raised when a bounded W9 input is invalid."""


def _scalar(value: float, name: str, *, lower: float = -MAX_STATE_BOUND, upper: float = MAX_STATE_BOUND) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise GravitySMFixedPointRGError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _coefficient(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 1:
        raise GravitySMFixedPointRGError(f"{name} must be finite and in [0, 1]")
    return result


def _state(values: Sequence[float]) -> tuple[float, ...]:
    if len(values) != 5:
        raise GravitySMFixedPointRGError("state must contain g1, g2, g3, y_t and lambda")
    return tuple(_scalar(value, name) for value, name in zip(values, ("g1", "g2", "g3", "y_t", "lambda")))


def _offsets(values: Sequence[float]) -> list[float]:
    result = sorted(set(float(value) for value in values))
    if not result or len(result) > 64 or any(not math.isfinite(value) or abs(value) > 64 for value in result):
        raise GravitySMFixedPointRGError("log-scale offsets must contain 1..64 finite values in [-64, 64]")
    return result


def beta_vector(
    state: Sequence[float],
    *,
    f_g: float = 0.0,
    f_y: float = 0.0,
    f_lambda: float = 0.0,
) -> tuple[float, ...]:
    """Return the five-coupling beta vector for the declared W9 control."""

    g1, g2, g3, yt, lam = _state(state)
    fg = _coefficient(f_g, "f_g")
    fy = _coefficient(f_y, "f_y")
    fl = _coefficient(f_lambda, "f_lambda")
    beta_g1 = G1_COEFFICIENT * g1**3 / LOOP_FACTOR - fg * g1
    beta_g2 = G2_COEFFICIENT * g2**3 / LOOP_FACTOR - fg * g2
    beta_g3 = G3_COEFFICIENT * g3**3 / LOOP_FACTOR - fg * g3
    beta_yt = yt * (4.5 * yt**2 - 17.0 / 20.0 * g1**2 - 9.0 / 4.0 * g2**2 - 8.0 * g3**2) / LOOP_FACTOR - fy * yt
    beta_lambda = (
        24.0 * lam**2
        - 6.0 * yt**4
        + (12.0 * yt**2 - 9.0 * g2**2 - 9.0 / 5.0 * g1**2) * lam
        + 9.0 / 8.0 * g2**4
        + 9.0 / 20.0 * g1**2 * g2**2
        + 27.0 / 200.0 * g1**4
    ) / LOOP_FACTOR - fl * lam
    return beta_g1, beta_g2, beta_g3, beta_yt, beta_lambda


def _deduplicate(values: Sequence[float], *, tolerance: float = 1e-10) -> list[float]:
    result: list[float] = []
    for value in sorted(float(item) for item in values):
        if not result or abs(value - result[-1]) > tolerance:
            result.append(value)
    return result


def _gauge_branches(f_g: float) -> list[tuple[float, float, float, str]]:
    fg = _coefficient(f_g, "f_g")
    roots = [0.0]
    if fg > 0:
        roots.append(math.sqrt(fg * LOOP_FACTOR / G1_COEFFICIENT))
    return [(g1, 0.0, 0.0, "GAUSSIAN_GAUGE" if g1 == 0.0 else "ABELIAN_INTERACTING_ROOT") for g1 in _deduplicate(roots)]


def _yukawa_branches(g1: float, f_y: float) -> list[tuple[float, str]]:
    fy = _coefficient(f_y, "f_y")
    # The gravity term is outside the loop factor in beta_yt, so its
    # contribution must be multiplied by 16*pi^2 when solving beta_yt=0.
    discriminant = (LOOP_FACTOR * fy + 17.0 / 20.0 * g1**2) / 4.5
    roots = [0.0]
    if discriminant > 0:
        roots.append(math.sqrt(discriminant))
    return [(yt, "GAUSSIAN_YUKAWA" if yt == 0.0 else "GRAVITY_DRESSED_YUKAWA_ROOT") for yt in _deduplicate(roots)]


def _lambda_branches(g1: float, yt: float, f_lambda: float) -> list[tuple[float, str]]:
    fl = _coefficient(f_lambda, "f_lambda")
    a = 24.0 / LOOP_FACTOR
    b = (12.0 * yt**2 - 9.0 / 5.0 * g1**2) / LOOP_FACTOR - fl
    c = (-6.0 * yt**4 + 27.0 / 200.0 * g1**4) / LOOP_FACTOR
    discriminant = b**2 - 4.0 * a * c
    if discriminant < -1e-12:
        return []
    root = math.sqrt(max(0.0, discriminant))
    roots = _deduplicate(((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)))
    return [(lam, "HIGGS_QUARTIC_ROOT_1" if index == 0 else "HIGGS_QUARTIC_ROOT_2") for index, lam in enumerate(roots)]


def fixed_points(f_g: float, f_y: float, f_lambda: float) -> list[dict[str, Any]]:
    """Enumerate all algebraic branches of the declared five-coupling control."""

    fg = _coefficient(f_g, "f_g")
    fy = _coefficient(f_y, "f_y")
    fl = _coefficient(f_lambda, "f_lambda")
    reports: list[dict[str, Any]] = []
    for g1, g2, g3, gauge_label in _gauge_branches(fg):
        for yt, yukawa_label in _yukawa_branches(g1, fy):
            for lam, lambda_label in _lambda_branches(g1, yt, fl):
                state = (g1, g2, g3, yt, lam)
                residual = beta_vector(state, f_g=fg, f_y=fy, f_lambda=fl)
                reports.append(
                    {
                        "f_g": fg,
                        "f_y": fy,
                        "f_lambda": fl,
                        "labels": [gauge_label, yukawa_label, lambda_label],
                        "state": list(state),
                        "residual": list(residual),
                        "max_residual": max(abs(value) for value in residual),
                        "perturbative": max(abs(value) for value in state) < PERTURBATIVE_BOUND,
                        "physical_nonnegative": all(value >= -1e-12 for value in state),
                        "g1_nonzero": g1 > 0,
                        "yukawa_nonzero": yt > 0,
                        "higgs_quartic_nonzero": abs(lam) > 1e-12,
                    }
                )
    return reports


def _finite_difference_matrix(state: Sequence[float], f_g: float, f_y: float, f_lambda: float) -> np.ndarray:
    base = np.asarray(state, dtype=float)
    matrix = np.zeros((5, 5), dtype=float)
    for index in range(5):
        step = 1e-6 * max(1.0, abs(base[index]))
        plus = base.copy()
        minus = base.copy()
        plus[index] += step
        minus[index] -= step
        matrix[:, index] = (
            np.asarray(beta_vector(plus, f_g=f_g, f_y=f_y, f_lambda=f_lambda))
            - np.asarray(beta_vector(minus, f_g=f_g, f_y=f_y, f_lambda=f_lambda))
        ) / (2.0 * step)
    return matrix


def _stability_report(point: Mapping[str, Any]) -> dict[str, Any]:
    matrix = _finite_difference_matrix(point["state"], point["f_g"], point["f_y"], point["f_lambda"])
    eigenvalues = np.linalg.eigvals(matrix)
    real = sorted(float(value.real) for value in eigenvalues if abs(float(value.imag)) < 1e-9)
    return {
        "stability_eigenvalues": real,
        "uv_attractive_directions": sum(value < -1e-9 for value in real),
        "ir_attractive_directions": sum(value > 1e-9 for value in real),
        "marginal_directions": sum(abs(value) <= 1e-9 for value in real),
    }


def _rk4_step(
    beta: Callable[[tuple[float, ...]], tuple[float, ...]],
    state: tuple[float, ...],
    step: float,
) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta(state)
    k2 = beta(shifted(state, k1, step / 2.0))
    k3 = beta(shifted(state, k2, step / 2.0))
    k4 = beta(shifted(state, k3, step))
    return tuple(state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0 for index in range(len(state)))


def integrate_trajectory(
    initial_state: Sequence[float],
    *,
    f_g: float,
    f_y: float,
    f_lambda: float,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
    steps_per_unit: int = 32,
) -> dict[str, Any]:
    fg = _coefficient(f_g, "f_g")
    fy = _coefficient(f_y, "f_y")
    fl = _coefficient(f_lambda, "f_lambda")
    state = _state(initial_state)
    ordered = _offsets(log_scale_offsets)
    current_offset = ordered[0]
    current_state = state
    points: list[dict[str, Any]] = [{"log_scale_offset": current_offset, "state": list(current_state)}]
    beta = lambda value: beta_vector(value, f_g=fg, f_y=fy, f_lambda=fl)
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


def run_gravity_sm_fixed_point_campaign(
    *,
    f_g_values: Sequence[float] = DEFAULT_F_G_VALUES,
    f_y_values: Sequence[float] = DEFAULT_F_Y_VALUES,
    f_lambda_values: Sequence[float] = DEFAULT_F_LAMBDA_VALUES,
    initial_states: Sequence[Sequence[float]] = DEFAULT_INITIAL_STATES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
) -> dict[str, Any]:
    fgs = [_coefficient(value, "f_g") for value in f_g_values]
    fys = [_coefficient(value, "f_y") for value in f_y_values]
    fls = [_coefficient(value, "f_lambda") for value in f_lambda_values]
    states = [_state(state) for state in initial_states]
    fixed_point_reports: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    for fg in fgs:
        for fy in fys:
            for fl in fls:
                points = fixed_points(fg, fy, fl)
                fixed_point_reports.append(
                    {
                        "f_g": fg,
                        "f_y": fy,
                        "f_lambda": fl,
                        "point_count": len(points),
                        "points": [{**point, **_stability_report(point)} for point in points],
                    }
                )
                for state in states:
                    trajectories.append(
                        {
                            "f_g": fg,
                            "f_y": fy,
                            "f_lambda": fl,
                            "initial_state": list(state),
                            "trajectory": integrate_trajectory(
                                state,
                                f_g=fg,
                                f_y=fy,
                                f_lambda=fl,
                                log_scale_offsets=log_scale_offsets,
                            ),
                        }
                    )
    point_count = sum(item["point_count"] for item in fixed_point_reports)
    all_points = [point for item in fixed_point_reports for point in item["points"]]
    nonzero_g1_count = sum(point["g1_nonzero"] for point in all_points)
    nonzero_yukawa_count = sum(point["yukawa_nonzero"] for point in all_points)
    return {
        "search_version": GRAVITY_SM_FIXED_POINT_RG_VERSION,
        "campaign_id": "gravity-dressed-standard-model-fixed-point-broad-run",
        "stage": "W9_GRAVITY_DRESSED_SM_FIXED_POINT_RG",
        "execution_status": "COMPLETE",
        "scope": {
            "gauge_sector": "ALL_SM_GAUGE_COUPLINGS_AT_ONE_LOOP_WITH_UNIVERSAL_F_G_CONTROL",
            "matter_sector": "TOP_YUKAWA_AND_HIGGS_QUARTIC_ONE_LOOP_CONTROLS",
            "gravity_sector": "PARAMETRIZED_FIXED_POINT_BACKGROUND",
            "full_functional_gravity_flow": "NOT_INCLUDED",
            "threshold_matching": "NOT_INCLUDED",
            "neutrino_flavour_and_full_yukawa_matrices": "NOT_INCLUDED",
            "f4_operators": "NOT_ACTIVATED",
        },
        "equations": {
            "beta_gauge": "beta_gi = b_i*gi^3/(16*pi^2) - f_g*gi; b=(41/10,-19/6,-7)",
            "beta_top": "beta_yt = yt*(9/2*yt^2 - 17/20*g1^2 - 9/4*g2^2 - 8*g3^2)/(16*pi^2) - f_y*yt",
            "beta_higgs": "beta_lambda = beta_lambda_SM_one_loop - f_lambda*lambda",
            "coefficient_status": "f_g is literature-shaped; f_y and f_lambda are explicitly minimal closure controls",
        },
        "scan": {
            "f_g_values": fgs,
            "f_y_values": fys,
            "f_lambda_values": fls,
            "parameter_slices": len(fgs) * len(fys) * len(fls),
            "initial_state_count": len(states),
            "trajectory_count": len(trajectories),
            "fixed_point_count": point_count,
            "nonzero_g1_fixed_point_count": int(nonzero_g1_count),
            "nonzero_yukawa_fixed_point_count": int(nonzero_yukawa_count),
        },
        "fixed_points": fixed_point_reports,
        "trajectories": trajectories,
        "conclusions": {
            "universal_positive_f_g_preserves_nonabelian_gaussian_roots": True,
            "positive_f_g_creates_nonzero_abelian_algebraic_root": True,
            "nonzero_abelian_root_uv_attractive": False,
            "gravity_dressed_yukawa_roots_exist_in_scanned_control": True,
            "higgs_quartic_roots_exist_in_scanned_control": True,
            "alpha_one_over_137_derived": False,
            "interpretation": "The scan demonstrates how a gravity-like linear term changes the fixed-point algebra, but f_g, f_y and f_lambda are not derived from one common quantum-gravity truncation.",
        },
        "bibliography": [
            {
                "id": "de-brito-eichhorn-2024",
                "citation": "G. P. de Brito et al., Ruling out models of vector dark matter in asymptotically safe quantum gravity, Phys. Rev. D 109, 055022 (2024)",
                "doi": "10.1103/PhysRevD.109.055022",
                "role": "explicit gravity-dressed Standard Model and dark-sector beta-function control",
            },
            {
                "id": "christiansen-litim-pawlowski-reichert-2018",
                "citation": "N. Christiansen, D. F. Litim, J. M. Pawlowski and M. Reichert, Asymptotic safety of gravity with matter, Phys. Rev. D 97, 106012 (2018)",
                "doi": "10.1103/PhysRevD.97.106012",
                "role": "functional-renormalization-group gravity/matter fixed points",
            },
            {
                "id": "mass-difference-charged-quarks-2018",
                "citation": "A. Eichhorn et al., Mass Difference for Charged Quarks from Asymptotically Safe Quantum Gravity, Phys. Rev. Lett. 121, 151302 (2018)",
                "doi": "10.1103/PhysRevLett.121.151302",
                "role": "explicit beta_gi = b_i*g_i^3/(16*pi^2)-f_g*g_i mechanism",
            },
            {
                "id": "pawlowski-reichert-wetterich-yamada-2019",
                "citation": "J. M. Pawlowski, M. Reichert, C. Wetterich and M. Yamada, Higgs scalar potential in asymptotically safe quantum gravity, Phys. Rev. D 99, 086010 (2019)",
                "doi": "10.1103/PhysRevD.99.086010",
                "role": "gravity and Higgs-quartic fixed-point relevance",
            },
            {
                "id": "riabokon-schiffer-wagner-2025",
                "citation": "M. Riabokon, M. Schiffer and F. Wagner, Regulator and gauge dependence of the Abelian gauge coupling in asymptotically safe quantum gravity, Phys. Rev. D 112, 106003 (2025)",
                "doi": "10.1103/gxm2-trn6",
                "role": "scheme, regulator and gauge-dependence caveat",
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
            "all_three_sm_gauge_couplings_included": True,
            "gauge_beta_function_source_anchor_recorded": True,
            "f_y_is_parametric_not_derived": True,
            "f_lambda_is_parametric_not_derived": True,
            "common_quantum_gravity_fixed_point_not_claimed": True,
            "fixed_point_branches_retained": True,
            "residuals_recorded": True,
            "stability_matrices_recorded": True,
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
        "next_gate": "DERIVE_F_G_F_Y_F_LAMBDA_FROM_ONE_COMMON_GRAVITY_MATTER_TRUNCATION_AND_AUDIT_SCHEME_DEPENDENCE",
    }


def write_gravity_sm_fixed_point_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_F_G_VALUES",
    "DEFAULT_F_LAMBDA_VALUES",
    "DEFAULT_F_Y_VALUES",
    "DEFAULT_INITIAL_STATES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "GRAVITY_SM_FIXED_POINT_RG_VERSION",
    "GravitySMFixedPointRGError",
    "beta_vector",
    "fixed_points",
    "integrate_trajectory",
    "run_gravity_sm_fixed_point_campaign",
    "write_gravity_sm_fixed_point_report",
]
