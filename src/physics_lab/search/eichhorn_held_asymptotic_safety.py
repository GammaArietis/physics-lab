"""Reproduction campaign for Eichhorn--Held, *Top mass from asymptotic safety*.

The published truncation couples an Einstein--Hilbert gravity sector to the
SM gauge couplings, top and bottom Yukawas and the Higgs quartic.  This module
implements the equations printed in Eqs. (1)--(9) of Phys. Lett. B 777,
217--221 (2018), including the explicit cosmological-constant threshold
functions.

The campaign keeps two gravitational references separate:

* the paper's quoted fixed-point anchor ``(G_N*, Lambda*)=(3.29,-4.51)``;
* the numerical root obtained by solving the printed beta functions with the
  stated Standard Model field counts.

That comparison is a reproducibility audit, not a fit.  The source paper
itself warns that the fixed point is truncation and regulator dependent.  No
experimental mass, alpha value, ranking or automatic selection is used.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from scipy.optimize import root


EICHHORN_HELD_AS_VERSION = "eichhorn-held-asymptotic-safety-v1"
LOOP_FACTOR = 16.0 * math.pi**2
MAX_STATE_BOUND = 20.0
ROOT_TOLERANCE = 1e-8
GRAVITY_POLE_TOLERANCE = 1e-8

N_SCALARS = 4.0
N_VECTORS = 12.0
N_WEYL_FERMIONS = 45.0

PUBLISHED_GRAVITY_ANCHOR = {"G_N": 3.29, "Lambda": -4.51}
DEFAULT_G_N_VALUES: tuple[float, ...] = (0.5, 1.0, 2.0, 3.29, 5.0)
DEFAULT_LAMBDA_VALUES: tuple[float, ...] = (-10.0, -5.0, -4.51, -4.0, -3.0, -1.0, 0.0, 0.25, 0.4)
DEFAULT_LOG_SCALE_OFFSETS: tuple[float, ...] = (-2.0, -1.0, 0.0, 1.0, 2.0)
DEFAULT_INITIAL_STATES: tuple[tuple[float, ...], ...] = (
    (3.29, -4.51, 0.40, 0.60, 1.00, 0.36, 0.02, 0.01),
    (1.00, -1.00, 0.20, 0.40, 0.80, 0.30, 0.05, 0.10),
    (0.50, -0.50, 0.10, 0.20, 0.30, 0.20, 0.01, 0.05),
)


class EichhornHeldError(ValueError):
    """Raised when a bounded campaign input is invalid."""


def _finite(value: float, name: str, *, lower: float = -MAX_STATE_BOUND, upper: float = MAX_STATE_BOUND) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise EichhornHeldError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _gravity_state(values: Sequence[float]) -> tuple[float, float]:
    if len(values) != 2:
        raise EichhornHeldError("gravity state must contain G_N and Lambda")
    return (_finite(values[0], "G_N", lower=-100.0, upper=100.0), _finite(values[1], "Lambda", lower=-100.0, upper=100.0))


def _full_state(values: Sequence[float], *, allow_intermediate: bool = False) -> tuple[float, ...]:
    if len(values) != 8:
        raise EichhornHeldError("full state must contain G_N, Lambda, g1, g2, g3, y_t, y_b and lambda_4")
    bound = 1e100 if allow_intermediate else MAX_STATE_BOUND
    return tuple(
        _finite(value, name, lower=-bound, upper=bound)
        for value, name in zip(values, ("G_N", "Lambda", "g1", "g2", "g3", "y_t", "y_b", "lambda_4"))
    )


def _check_lambda(value: float) -> float:
    result = _finite(value, "Lambda", lower=-100.0, upper=100.0)
    poles = (-1.0 / 8.0, 0.5, 0.75)
    if any(abs(result - pole) < GRAVITY_POLE_TOLERANCE for pole in poles):
        raise EichhornHeldError("Lambda is too close to a published threshold pole")
    return result


def f_g(Lambda: float) -> float:
    """Published gauge threshold function, Eq. (5)."""

    lam = _check_lambda(Lambda)
    return 5.0 * (1.0 - 4.0 * lam) / (18.0 * math.pi * (1.0 - 2.0 * lam) ** 2)


def f_y(Lambda: float) -> float:
    """Published Yukawa threshold function, Eq. (3)."""

    lam = _check_lambda(Lambda)
    numerator = 96.0 + lam * (-235.0 + lam * (103.0 + 56.0 * lam))
    denominator = 12.0 * math.pi * (3.0 + 2.0 * lam * (-5.0 + 4.0 * lam)) ** 2
    return numerator / denominator


def f_lambda(Lambda: float) -> float:
    """Published Higgs-quartic threshold function, Eq. (4)."""

    lam = _check_lambda(Lambda)
    numerator = 165.0 - 8.0 * lam * (61.0 + lam * (-49.0 + 4.0 * lam))
    denominator = 6.0 * math.pi * (3.0 + 2.0 * lam * (-5.0 + 4.0 * lam)) ** 2
    return numerator / denominator


def f_gravity(Lambda: float) -> float:
    """Published gravitational threshold function, Eq. (8)."""

    lam = _check_lambda(Lambda)
    return (
        5.0 / (6.0 * math.pi * (1.0 - 2.0 * lam))
        + 5.0 / (3.0 * math.pi * (1.0 - 2.0 * lam) ** 2)
        - 1.0 / (2.0 * math.pi * (3.0 - 4.0 * lam))
        + (11.0 + 32.0 * math.log(3.0 / 2.0)) / (12.0 * math.pi)
        - (N_WEYL_FERMIONS + N_SCALARS - 4.0 * N_VECTORS) / (6.0 * math.pi)
    )


def beta_gravity(state: Sequence[float]) -> tuple[float, float]:
    """Published beta functions for ``(G_N, Lambda)``, Eqs. (7)--(8)."""

    G_N, Lambda = _gravity_state(state)
    fg = f_gravity(Lambda)
    bracket = (
        3.0 / (7.0 - 2.0 * (3.0 - 4.0 * Lambda))
        + N_WEYL_FERMIONS
        - N_SCALARS / 2.0
        - N_VECTORS
        - 5.0 / (2.0 * (1.0 - 2.0 * Lambda))
        - 8.0 * math.log(3.0 / 2.0)
    )
    beta_G = 2.0 * G_N - G_N**2 * fg
    beta_lambda = -2.0 * Lambda - G_N / (2.0 * math.pi) * bracket - G_N * Lambda * fg
    return beta_G, beta_lambda


def beta_matter(state: Sequence[float], *, G_N: float, Lambda: float) -> tuple[float, ...]:
    """One-loop SM matter beta functions with the published gravity terms."""

    if len(state) != 6:
        raise EichhornHeldError("matter state must contain g1, g2, g3, y_t, y_b and lambda_4")
    g1, g2, g3, yt, yb, lam4 = tuple(
        _finite(value, name, lower=-1e100, upper=1e100)
        for value, name in zip(state, ("g1", "g2", "g3", "y_t", "y_b", "lambda_4"))
    )
    G = _finite(G_N, "G_N", lower=-1e100, upper=1e100)
    cosmological = _check_lambda(Lambda)
    fg, fy, fl = f_g(cosmological), f_y(cosmological), f_lambda(cosmological)
    beta_g1 = 41.0 / 10.0 * g1**3 / LOOP_FACTOR - G * g1 * fg
    beta_g2 = -19.0 / 6.0 * g2**3 / LOOP_FACTOR - G * g2 * fg
    beta_g3 = -7.0 * g3**3 / LOOP_FACTOR - G * g3 * fg
    beta_yt = (
        9.0 * yt**3
        + 3.0 * yt * yb**2
        + yt * (-16.0 * g3**2 - 9.0 / 2.0 * g2**2 - 17.0 / 10.0 * g1**2)
    ) / (2.0 * LOOP_FACTOR) + G * yt * fy
    beta_yb = (
        9.0 * yb**3
        + 3.0 * yb * yt**2
        + yb * (-16.0 * g3**2 - 9.0 / 2.0 * g2**2 - 1.0 / 2.0 * g1**2)
    ) / (2.0 * LOOP_FACTOR) + G * yb * fy
    beta_lam4 = (
        12.0 * lam4**2
        + 6.0 * lam4 * (yt**2 + yb**2 - 3.0 / 20.0 * g1**2 - 3.0 / 4.0 * g2**2)
        - 3.0 * (yt**4 + yb**4)
        + 27.0 / 400.0 * g1**4
        + 9.0 / 16.0 * g2**4
        + 9.0 / 40.0 * g1**2 * g2**2
    ) / (8.0 * math.pi**2) + G * lam4 * fl
    return beta_g1, beta_g2, beta_g3, beta_yt, beta_yb, beta_lam4


def beta_full(state: Sequence[float]) -> tuple[float, ...]:
    """Full eight-dimensional beta vector in the published truncation."""

    G_N, Lambda, g1, g2, g3, yt, yb, lam4 = _full_state(state, allow_intermediate=True)
    return (*beta_gravity((G_N, Lambda)), *beta_matter((g1, g2, g3, yt, yb, lam4), G_N=G_N, Lambda=Lambda))


def _unique_vectors(vectors: Sequence[Sequence[float]], *, tolerance: float = 1e-7) -> list[tuple[float, ...]]:
    result: list[tuple[float, ...]] = []
    for vector in vectors:
        candidate = tuple(float(value) for value in vector)
        if not any(max(abs(candidate[i] - previous[i]) for i in range(len(candidate))) < tolerance for previous in result):
            result.append(candidate)
    return sorted(result)


def gravity_equation_fixed_point(*, initial_guess: Sequence[float] = (3.29, -4.51)) -> dict[str, Any]:
    """Solve the printed gravitational beta functions without fitting counts."""

    guess = _gravity_state(initial_guess)
    solution = root(lambda values: beta_gravity(values), guess, method="hybr", tol=1e-12)
    if not solution.success or not all(math.isfinite(float(value)) for value in solution.x):
        return {"status": "NO_ROOT", "initial_guess": list(guess), "message": str(solution.message)}
    state = tuple(float(value) for value in solution.x)
    residual = beta_gravity(state)
    return {
        "status": "COMPLETE",
        "initial_guess": list(guess),
        "state": list(state),
        "residual": list(residual),
        "max_residual": max(abs(value) for value in residual),
        "positive_newton": state[0] > 0.0,
        "negative_cosmological_constant": state[1] < 0.0,
    }


def literature_anchor_audit() -> dict[str, Any]:
    anchor = (PUBLISHED_GRAVITY_ANCHOR["G_N"], PUBLISHED_GRAVITY_ANCHOR["Lambda"])
    residual = beta_gravity(anchor)
    solved = gravity_equation_fixed_point(initial_guess=anchor)
    return {
        "published_anchor": dict(PUBLISHED_GRAVITY_ANCHOR),
        "anchor_residual": list(residual),
        "anchor_max_residual": max(abs(value) for value in residual),
        "equation_root": solved,
        "interpretation": "The printed equations and the rounded fixed-point anchor are both retained; no parameter is adjusted to force equality.",
    }


def _gauge_branches(G_N: float, Lambda: float) -> list[tuple[float, float, float, list[str]]]:
    fg = G_N * f_g(Lambda)
    coefficients = (41.0 / 10.0, -19.0 / 6.0, -7.0)
    roots: list[list[float]] = []
    for coefficient in coefficients:
        values = [0.0]
        if fg / coefficient > 0.0:
            values.append(math.sqrt(LOOP_FACTOR * fg / coefficient))
        roots.append(values)
    branches = []
    for g1, g2, g3 in itertools.product(*roots):
        labels = [
            "GAUSSIAN_G1" if g1 == 0.0 else "INTERACTING_G1",
            "GAUSSIAN_G2" if g2 == 0.0 else "INTERACTING_G2",
            "GAUSSIAN_G3" if g3 == 0.0 else "INTERACTING_G3",
        ]
        branches.append((g1, g2, g3, labels))
    return branches


def matter_fixed_points(*, G_N: float, Lambda: float) -> list[dict[str, Any]]:
    """Enumerate real matter fixed points for a fixed gravity background."""

    G = _finite(G_N, "G_N", lower=-100.0, upper=100.0)
    cosmological = _check_lambda(Lambda)
    points: list[tuple[float, ...]] = []
    seeds = (-0.75, -0.25, 0.0, 0.25, 0.75)
    for g1, g2, g3, labels in _gauge_branches(G, cosmological):
        for seed in itertools.product(seeds, repeat=3):
            initial = (seed[0], seed[1], seed[2])

            def residual(values: Sequence[float]) -> np.ndarray:
                """Keep exploratory root iterations outside the domain harmless."""

                try:
                    result = beta_matter(
                        (g1, g2, g3, values[0], values[1], values[2]),
                        G_N=G,
                        Lambda=cosmological,
                    )[3:]
                    array = np.asarray(result, dtype=float)
                    if not np.all(np.isfinite(array)):
                        return np.full(3, 1e100, dtype=float)
                    return array
                except (EichhornHeldError, OverflowError, FloatingPointError):
                    return np.full(3, 1e100, dtype=float)

            result = root(
                residual,
                initial,
                method="hybr",
                tol=1e-11,
            )
            if not result.success or not all(math.isfinite(float(value)) for value in result.x):
                continue
            state = (g1, g2, g3, *(float(value) for value in result.x))
            if max(abs(value) for value in state) > MAX_STATE_BOUND:
                continue
            residual = beta_matter(state, G_N=G, Lambda=cosmological)
            if max(abs(value) for value in residual) < ROOT_TOLERANCE:
                points.append(state)
    unique = _unique_vectors(points)
    reports = []
    for state in unique:
        residual = beta_matter(state, G_N=G, Lambda=cosmological)
        reports.append({
            "state": list(state),
            "residual": list(residual),
            "max_residual": max(abs(value) for value in residual),
            "labels": [
                "NONZERO_G1" if state[0] > 1e-10 else "GAUSSIAN_G1",
                "NONZERO_G2" if state[1] > 1e-10 else "GAUSSIAN_G2",
                "NONZERO_G3" if state[2] > 1e-10 else "GAUSSIAN_G3",
                "NONZERO_TOP_YUKAWA" if abs(state[3]) > 1e-10 else "GAUSSIAN_TOP_YUKAWA",
                "NONZERO_BOTTOM_YUKAWA" if abs(state[4]) > 1e-10 else "GAUSSIAN_BOTTOM_YUKAWA",
                "NONZERO_HIGGS_QUARTIC" if abs(state[5]) > 1e-10 else "GAUSSIAN_HIGGS_QUARTIC",
            ],
            "physical_nonnegative": all(value >= -1e-10 for value in state),
            "perturbative": max(abs(value) for value in state) < 1.0,
        })
    return reports


def _rk4_step(beta: Callable[[tuple[float, ...]], tuple[float, ...]], state: tuple[float, ...], step: float) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta(state)
    k2 = beta(shifted(state, k1, step / 2.0))
    k3 = beta(shifted(state, k2, step / 2.0))
    k4 = beta(shifted(state, k3, step))
    return tuple(state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0 for index in range(len(state)))


def integrate_full_trajectory(initial_state: Sequence[float], *, log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS, steps_per_unit: int = 24) -> dict[str, Any]:
    state = _full_state(initial_state)
    ordered = sorted(set(float(value) for value in log_scale_offsets))
    if not ordered:
        raise EichhornHeldError("log-scale offsets cannot be empty")
    current = ordered[0]
    points: list[dict[str, Any]] = [{"log_scale_offset": current, "state": list(state)}]
    beta = lambda value: beta_full(value)
    try:
        for target in ordered[1:]:
            distance = target - current
            count = max(1, int(abs(distance) * steps_per_unit))
            step = distance / count
            for _ in range(count):
                state = _rk4_step(beta, state, step)
                if any(not math.isfinite(value) or abs(value) > MAX_STATE_BOUND for value in state):
                    return {"status": "BOUND_REACHED", "points": points, "final_state": list(state)}
            current = target
            points.append({"log_scale_offset": current, "state": list(state)})
    except EichhornHeldError as exc:
        return {"status": "THRESHOLD_POLE", "points": points, "final_state": list(state), "error": str(exc)}
    return {"status": "COMPLETE", "points": points, "final_state": list(state)}


def run_eichhorn_held_campaign(*, G_N_values: Sequence[float] = DEFAULT_G_N_VALUES, Lambda_values: Sequence[float] = DEFAULT_LAMBDA_VALUES, initial_states: Sequence[Sequence[float]] = DEFAULT_INITIAL_STATES, log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS) -> dict[str, Any]:
    G_values = [_finite(value, "G_N", lower=-100.0, upper=100.0) for value in G_N_values]
    Lambda_values = [_check_lambda(value) for value in Lambda_values]
    states = [_full_state(state) for state in initial_states]
    slices: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    for G_N in G_values:
        for Lambda in Lambda_values:
            points = matter_fixed_points(G_N=G_N, Lambda=Lambda)
            slices.append({
                "G_N": G_N,
                "Lambda": Lambda,
                "thresholds": {"f_g": f_g(Lambda), "f_y": f_y(Lambda), "f_lambda": f_lambda(Lambda), "f_gravity": f_gravity(Lambda)},
                "fixed_point_count": len(points),
                "fixed_points": points,
            })
    for state in states:
        trajectories.append({"initial_state": list(state), "trajectory": integrate_full_trajectory(state, log_scale_offsets=log_scale_offsets)})
    all_points = [point for record in slices for point in record["fixed_points"]]
    anchor_audit = literature_anchor_audit()
    return {
        "search_version": EICHHORN_HELD_AS_VERSION,
        "campaign_id": "eichhorn-held-top-mass-asymptotic-safety-reproduction",
        "stage": "EH_AS_REPRODUCTION_FULL_TRUNCATION",
        "execution_status": "COMPLETE",
        "scope": {
            "gravity_sector": "EINSTEIN_HILBERT_G_N_AND_COSMOLOGICAL_CONSTANT",
            "gauge_sector": "SM_G1_G2_G3_ONE_LOOP",
            "yukawa_sector": "TOP_AND_BOTTOM_ONE_LOOP",
            "higgs_sector": "QUARTIC_ONE_LOOP",
            "field_counts": {"N_S": N_SCALARS, "N_V": N_VECTORS, "N_W": N_WEYL_FERMIONS},
            "ir_matching": "NOT_IMPLEMENTED",
            "pole_mass_conversion": "NOT_IMPLEMENTED",
        },
        "equations": {
            "beta_G_N": "2*G_N - G_N^2*f_gravity(Lambda)",
            "beta_Lambda": "-2*Lambda - G_N/(2*pi)*matter_gravity_bracket(Lambda) - G_N*Lambda*f_gravity(Lambda)",
            "beta_gauge": "b_i*g_i^3/(16*pi^2) - G_N*g_i*f_g(Lambda), b=(41/10,-19/6,-7)",
            "beta_top": "[9*y_t^3+3*y_t*y_b^2+y_t*(-16*g3^2-9/2*g2^2-17/10*g1^2)]/(32*pi^2)+G_N*y_t*f_y(Lambda)",
            "beta_bottom": "top equation under y_t<->y_b and 17/10*g1^2 -> 1/2*g1^2",
            "beta_higgs": "published Eq. (2) + G_N*lambda_4*f_lambda(Lambda)",
        },
        "literature_anchor_audit": anchor_audit,
        "scan": {
            "G_N_values": G_values,
            "Lambda_values": Lambda_values,
            "parameter_slices": len(slices),
            "fixed_point_count": len(all_points),
            "initial_state_count": len(states),
            "trajectory_count": len(trajectories),
            "trajectory_status_counts": {status: sum(item["trajectory"]["status"] == status for item in trajectories) for status in sorted({item["trajectory"]["status"] for item in trajectories})},
        },
        "gravity_matter_slices": slices,
        "trajectories": trajectories,
        "observables": {
            "source_top_pole_mass_claim": "approximately 171 GeV",
            "source_top_pole_mass_used_as_target": False,
            "source_higgs_mass_claim": "approximately 132 GeV in the simple truncation",
            "ir_observable_recomputed": False,
            "empirical_comparison": "NOT_AUTHORIZED",
        },
        "conclusions": {
            "published_equations_implemented": True,
            "nonzero_cosmological_constant_included": True,
            "all_three_sm_gauge_couplings_included": True,
            "top_and_bottom_yukawa_included": True,
            "higgs_quartic_included": True,
            "literature_anchor_reproduced_without_adjustment": anchor_audit["anchor_max_residual"] < 1e-6,
            "alpha_one_over_137_derived": False,
            "interpretation": "The published Eichhorn--Held truncation is executable. The campaign preserves both the printed-equation root and the paper's quoted gravity fixed-point anchor without fitting one to the other.",
        },
        "bibliography": [
            {
                "id": "eichhorn-held-2018",
                "citation": "A. Eichhorn and A. Held, Top mass from asymptotic safety, Phys. Lett. B 777, 217--221 (2018)",
                "doi": "10.1016/j.physletb.2017.12.040",
                "role": "primary published truncation and fixed-point anchor",
            },
            {
                "id": "eichhorn-held-pawlowski-2016",
                "citation": "A. Eichhorn, A. Held and J. M. Pawlowski, Quantum-gravity effects on a Higgs-Yukawa model, Phys. Rev. D 94, 104027 (2016)",
                "doi": "10.1103/PhysRevD.94.104027",
                "role": "Higgs-Yukawa gravity-matter background",
            },
            {
                "id": "christiansen-eichhorn-2017",
                "citation": "N. Christiansen and A. Eichhorn, An asymptotically safe solution to the U(1) triviality problem, Phys. Lett. B 770, 154 (2017)",
                "doi": "10.1016/j.physletb.2017.04.047",
                "role": "Abelian gauge asymptotic-safety mechanism",
            },
        ],
        "authorization": {
            "finite_bounds": "AUTHORIZED",
            "target_blind_generation": True,
            "alpha_as_target": "DISABLED",
            "target_comparison": "NOT_AUTHORIZED",
            "external_data_used": False,
            "fitting": "DISABLED",
            "automatic_selection": "DISABLED",
            "automatic_ranking": "DISABLED",
        },
        "controls": {
            "published_equations_recorded": True,
            "literature_fixed_point_anchor_retained": True,
            "printed_equation_root_retained": True,
            "gravity_and_matter_coupled": True,
            "threshold_poles_guarded": True,
            "all_fixed_point_branches_retained": True,
            "trajectories_retained": True,
            "source_mass_claim_not_used_as_target": True,
            "alpha_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "negative_results_recorded": True,
        },
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "next_gate": "ADD_TARGET_BLIND_IR_MATCHING_ONLY_AFTER_THE_PUBLISHED_UV_TRUNCATION_REPRODUCTION_IS_ARCHIVED",
    }


def write_eichhorn_held_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_G_N_VALUES",
    "DEFAULT_INITIAL_STATES",
    "DEFAULT_LAMBDA_VALUES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "EICHHORN_HELD_AS_VERSION",
    "EichhornHeldError",
    "PUBLISHED_GRAVITY_ANCHOR",
    "beta_full",
    "beta_gravity",
    "beta_matter",
    "f_g",
    "f_gravity",
    "f_lambda",
    "f_y",
    "gravity_equation_fixed_point",
    "literature_anchor_audit",
    "matter_fixed_points",
    "run_eichhorn_held_campaign",
    "write_eichhorn_held_report",
]
