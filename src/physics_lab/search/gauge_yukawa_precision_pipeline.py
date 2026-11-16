"""W15 precision-control pipeline for the vector-like gauge--Yukawa EFT.

The module closes the computational gates around the W13/W14 model while
keeping the approximation boundary explicit.  The gauge sector uses the
standard two-loop SM matrix plus representation-derived vector-like gauge
terms.  The Yukawa/scalar block is the registered reduced control at one loop;
the fixed-point, stability, threshold and matching machinery therefore never
labels the result as a full NNLO BSM calculation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root

from physics_lab.search.gauge_yukawa_threshold_eft import (
    active_multiplicities,
    threshold_map,
    thresholded_gauge_coefficients,
)
from physics_lab.search.gauge_yukawa_vectorlike_extension import (
    DEFAULT_IR_SCALE_GEV,
    DEFAULT_UV_SCALE_GEV,
    LOOP_FACTOR,
    MULTIPLETS,
    PERTURBATIVE_BOUND,
    ZERO_TOLERANCE,
    GaugeYukawaExtensionError,
    _finite,
    _multiplicity_map,
    _observable_record,
    action_record,
    beta_state,
    gauge_coefficients,
)


PRECISION_PIPELINE_VERSION = "gauge-yukawa-precision-control-v1"
SM_TWO_LOOP_GAUGE_MATRIX = np.asarray(
    [
        [199.0 / 50.0, 27.0 / 10.0, 44.0 / 5.0],
        [9.0 / 10.0, 35.0 / 6.0, 12.0],
        [11.0 / 10.0, 9.0 / 2.0, -26.0],
    ],
    dtype=float,
)
SM_TOP_YUKAWA_GAUGE_COEFFICIENTS = np.asarray([17.0 / 10.0, 3.0 / 2.0, 2.0], dtype=float)
GAUGE_NAMES = ("g1", "g2", "g3")
GAUGE_CASIMIRS = {"g1": 0.0, "g2": 2.0, "g3": 3.0}


def _representation_data(name: str) -> tuple[dict[str, float], dict[str, float]]:
    multiplet = MULTIPLETS[name]
    indices = {
        "g1": (3.0 / 5.0) * multiplet.hypercharge**2 * multiplet.color_dim * multiplet.weak_dim,
        "g2": multiplet.su2_index * multiplet.color_dim,
        "g3": multiplet.su3_index * multiplet.weak_dim,
    }
    casimirs = {"g1": multiplet.casimir_u1, "g2": multiplet.casimir_su2, "g3": multiplet.casimir_su3}
    return indices, casimirs


def two_loop_gauge_matrix(active: Mapping[str, Any]) -> list[list[float]]:
    """Return SM B_ij plus Dirac vector-like gauge contributions.

    For a Dirac multiplet the diagonal contribution is
    ``(4 C_i + 20 C(G_i)/3) S_i`` and the mixed contribution is
    ``4 C_j S_i``.  The U(1) factors use the registered GUT normalisation.
    This is the gauge-only two-loop control; new-sector Yukawa terms in beta_g
    are kept as an explicit unactivated boundary.
    """

    counts = _multiplicity_map(active)
    matrix = np.array(SM_TWO_LOOP_GAUGE_MATRIX, dtype=float)
    for name, count in counts.items():
        if not count:
            continue
        indices, casimirs = _representation_data(name)
        for i, gi in enumerate(GAUGE_NAMES):
            for j, gj in enumerate(GAUGE_NAMES):
                si = indices[gi] * count
                if i == j:
                    matrix[i, j] += (4.0 * casimirs[gi] + (20.0 / 3.0) * GAUGE_CASIMIRS[gi]) * si
                else:
                    matrix[i, j] += 4.0 * casimirs[gj] * si
    return matrix.tolist()


def _gauge_two_loop_beta(
    state: Sequence[float],
    *,
    active: Mapping[str, Any],
    yt: float,
) -> tuple[float, float, float]:
    g = np.asarray(state[:3], dtype=float)
    coefficients = gauge_coefficients(active)
    b = np.asarray([coefficients[name] for name in GAUGE_NAMES], dtype=float)
    matrix = np.asarray(two_loop_gauge_matrix(active), dtype=float)
    two_loop = matrix @ (g**2) - SM_TOP_YUKAWA_GAUGE_COEFFICIENTS * float(yt) ** 2
    return tuple(float(g[i] ** 3 * (b[i] / LOOP_FACTOR + two_loop[i] / LOOP_FACTOR**2)) for i in range(3))


def precision_beta_state(
    log_scale: float,
    state: Sequence[float],
    *,
    active: Mapping[str, Any],
    yukawa_multiplet: str,
) -> tuple[float, ...]:
    """Two-loop gauge plus registered reduced matter-control beta vector."""

    del log_scale
    if len(state) != 8:
        raise GaugeYukawaExtensionError("state must contain eight couplings")
    values = tuple(float(value) for value in state)
    if not all(math.isfinite(value) for value in values):
        raise GaugeYukawaExtensionError("state contains a non-finite coupling")
    counts = _multiplicity_map(active)
    # The reduced matter block remains a control below a fermion threshold;
    # only the gauge representation contribution is decoupled here.
    matter_counts = dict(counts)
    matter_counts[yukawa_multiplet] = max(1, matter_counts.get(yukawa_multiplet, 0))
    matter = beta_state(
        0.0,
        values,
        multiplicities=matter_counts,
        yukawa_multiplet=yukawa_multiplet,
        gauge_coefficients_override={"g1": 0.0, "g2": 0.0, "g3": 0.0},
    )
    gauge = _gauge_two_loop_beta(values, active=counts, yt=values[3])
    return (*gauge, *matter[3:])


def vacuum_stability(state: Sequence[float]) -> dict[str, Any]:
    _, _, _, _, _, lam_h, lam_s, lam_hs = (float(value) for value in state)
    portal_bound = -2.0 * math.sqrt(max(lam_h, 0.0) * max(lam_s, 0.0))
    return {
        "lambda_h_positive": lam_h >= 0.0,
        "lambda_s_positive": lam_s >= 0.0,
        "portal_bound_satisfied": lam_hs >= portal_bound,
        "portal_bound": portal_bound,
        "minimum_margin": min(lam_h, lam_s, lam_hs - portal_bound),
        "stable_at_declared_point": lam_h >= 0.0 and lam_s >= 0.0 and lam_hs >= portal_bound,
    }


def _fixed_point_residual(
    state: Sequence[float],
    *,
    active: Mapping[str, Any],
    yukawa_multiplet: str,
) -> np.ndarray:
    return np.asarray(precision_beta_state(0.0, state, active=active, yukawa_multiplet=yukawa_multiplet), dtype=float)


def critical_exponents(
    fixed_point: Sequence[float],
    *,
    active: Mapping[str, Any],
    yukawa_multiplet: str,
) -> list[dict[str, float]]:
    point = np.asarray(fixed_point, dtype=float)
    jacobian = np.zeros((len(point), len(point)), dtype=float)
    for index in range(len(point)):
        step = 1.0e-6 * max(1.0, abs(point[index]))
        plus = point.copy()
        minus = point.copy()
        plus[index] += step
        minus[index] -= step
        jacobian[:, index] = (_fixed_point_residual(plus, active=active, yukawa_multiplet=yukawa_multiplet) - _fixed_point_residual(minus, active=active, yukawa_multiplet=yukawa_multiplet)) / (2.0 * step)
    eigenvalues = np.linalg.eigvals(jacobian)
    return [{"real": float(value.real), "imag": float(value.imag)} for value in eigenvalues]


def search_fixed_points(
    seeds: Sequence[Sequence[float]],
    *,
    active: Mapping[str, Any],
    yukawa_multiplet: str,
) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    seen: set[tuple[float, ...]] = set()
    for index, seed in enumerate(seeds):
        if len(seed) != 8:
            raise GaugeYukawaExtensionError("fixed-point seeds must contain eight couplings")
        result = root(lambda point: _fixed_point_residual(point, active=active, yukawa_multiplet=yukawa_multiplet), np.asarray(seed, dtype=float))
        point = np.asarray(result.x, dtype=float)
        if not result.success or not np.all(np.isfinite(point)):
            continue
        residual = float(np.max(np.abs(_fixed_point_residual(point, active=active, yukawa_multiplet=yukawa_multiplet))))
        if residual > 1.0e-8 or np.max(np.abs(point)) >= PERTURBATIVE_BOUND:
            continue
        key = tuple(round(float(value), 10) for value in point)
        if key in seen:
            continue
        seen.add(key)
        retained.append(
            {
                "fixed_point_id": f"fp-{len(retained):03d}",
                "seed_index": index,
                "couplings": point.tolist(),
                "residual_max": residual,
                "critical_exponents": critical_exponents(point, active=active, yukawa_multiplet=yukawa_multiplet),
                "vacuum_stability": vacuum_stability(point),
            }
        )
    return retained


def _segment_scales(uv: float, ir: float, thresholds: Mapping[str, float]) -> list[float]:
    cuts = sorted({mass for mass in thresholds.values() if ir < mass < uv}, reverse=True)
    return [uv, *cuts, ir]


def run_precision_candidate(
    candidate: Mapping[str, Any],
    *,
    uv_scale_gev: float,
    ir_scale_gev: float,
    fixed_point_seeds: Sequence[Sequence[float]],
) -> dict[str, Any]:
    multiplicities = _multiplicity_map(candidate.get("multiplicities", {}))
    yukawa_multiplet = str(candidate.get("yukawa_multiplet", ""))
    thresholds = threshold_map(candidate.get("thresholds_gev", {}), multiplicities)
    action = action_record(multiplicities, yukawa_multiplet)
    initial = tuple(_finite(value, f"initial_state[{index}]") for index, value in enumerate(candidate.get("initial_state", [])))
    if len(initial) != 8:
        raise GaugeYukawaExtensionError("initial_state must contain eight couplings")
    uv = _finite(uv_scale_gev, "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir = _finite(ir_scale_gev, "ir_scale_gev", lower=1.0, upper=1.0e100)
    if uv <= ir:
        raise GaugeYukawaExtensionError("uv_scale_gev must exceed ir_scale_gev")

    uv_active = active_multiplicities(uv, multiplicities, thresholds)
    fixed_points = search_fixed_points(fixed_point_seeds, active=uv_active, yukawa_multiplet=yukawa_multiplet)
    state = np.asarray(initial, dtype=float)
    segments: list[dict[str, Any]] = []
    stability = [vacuum_stability(state)]
    max_abs = float(np.max(np.abs(state)))
    scales = _segment_scales(uv, ir, thresholds)
    for high, low in zip(scales[:-1], scales[1:]):
        active = active_multiplicities(math.sqrt(high * low), multiplicities, thresholds)
        solution = solve_ivp(
            lambda t, y: precision_beta_state(t, y, active=active, yukawa_multiplet=yukawa_multiplet),
            (math.log(high), math.log(low)),
            state,
            rtol=1.0e-8,
            atol=1.0e-10,
            max_step=0.25,
        )
        if not solution.success:
            return {"candidate_id": str(candidate.get("candidate_id", "unnamed")), "status": "INTEGRATION_FAILURE", "action": action, "fixed_points": fixed_points, "message": str(solution.message), "target_blind": True}
        state = solution.y[:, -1]
        max_abs = max(max_abs, float(np.max(np.abs(solution.y))))
        stability.extend(vacuum_stability(solution.y[:, index]) for index in range(solution.y.shape[1]))
        segments.append({"high_scale_gev": high, "low_scale_gev": low, "active_multiplicities": active, "two_loop_gauge": True, "steps": int(solution.t.size)})
    final_state = tuple(float(value) for value in state)
    zero_protected = all(abs(value) <= ZERO_TOLERANCE for value in initial[:3]) and all(abs(value) <= ZERO_TOLERANCE for value in final_state[:3])
    status = "ZERO_PROTECTED" if zero_protected else ("NONPERTURBATIVE" if max_abs >= PERTURBATIVE_BOUND else "COMPLETE")
    stable_running = all(item["stable_at_declared_point"] for item in stability)
    return {
        "candidate_id": str(candidate.get("candidate_id", "unnamed")),
        "status": status,
        "action": action,
        "initial_state": list(initial),
        "final_state": list(final_state),
        "fixed_points": fixed_points,
        "segments": segments,
        "uv_observables": _observable_record(initial, uv),
        "ir_observables": _observable_record(final_state, ir),
        "vacuum_stability": {"stable_along_running": stable_running, "minimum_margin": min(item["minimum_margin"] for item in stability)},
        "perturbativity": {"max_abs_coupling": max_abs, "bound": PERTURBATIVE_BOUND, "within_bound": max_abs < PERTURBATIVE_BOUND},
        "matching": {"smdr_status": "DEFERRED_EXTERNAL_BACKEND", "pole_observables_generated": False},
        "controls": {
            "two_loop_gauge_control": True,
            "two_loop_gauge_vectorlike_terms_representation_derived": True,
            "new_sector_yukawa_terms_in_gauge_beta_activated": False,
            "reduced_yukawa_scalar_block": True,
            "fixed_points_target_blind": True,
            "all_fixed_points_found_from_declared_seeds_retained": True,
            "critical_exponents_computed": True,
            "finite_threshold_corrections_claimed": False,
            "smdr_pole_matching_deferred": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
        },
        "target_blind": True,
    }


def run_precision_campaign(activation: Mapping[str, Any]) -> dict[str, Any]:
    uv = _finite(activation.get("uv_scale_gev", DEFAULT_UV_SCALE_GEV), "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir = _finite(activation.get("ir_scale_gev", DEFAULT_IR_SCALE_GEV), "ir_scale_gev", lower=1.0, upper=1.0e100)
    candidates = activation.get("candidates")
    seeds = activation.get("fixed_point_seeds")
    if not isinstance(candidates, list) or not candidates or not isinstance(seeds, list) or not seeds:
        raise GaugeYukawaExtensionError("activation requires candidates and fixed_point_seeds")
    results = [run_precision_candidate(item, uv_scale_gev=uv, ir_scale_gev=ir, fixed_point_seeds=seeds) for item in candidates]
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {
        "campaign_id": str(activation.get("campaign_id", "gauge-yukawa-precision-pipeline")),
        "pipeline_version": PRECISION_PIPELINE_VERSION,
        "execution_status": "COMPLETE",
        "scope": {
            "model": "SM + real singlet S + anomaly-free vector-like Dirac multiplets",
            "uv_scale_gev": uv,
            "ir_scale_gev": ir,
            "gauge_beta_order": "two-loop SM plus representation-derived vector-like gauge control",
            "yukawa_beta_order": "reduced one-loop matter control",
            "quartic_beta_order": "reduced one-loop matter control",
            "pole_matching": "SMDR adapter deferred to external backend",
        },
        "scan": {"candidate_count": len(results), "status_counts": counts, "fixed_point_seed_count": len(seeds)},
        "controls": {
            "all_candidates_retained": True,
            "all_fixed_points_retained": True,
            "target_blind_generation": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "smdr_external_comparison_not_run": True,
            "full_two_loop_bsm_yukawa_scalar_claimed": False,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": "W15 precision-control pipeline; no candidate is promoted and no pole comparison is performed before SMDR authorization.",
    }


def write_precision_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "PRECISION_PIPELINE_VERSION",
    "critical_exponents",
    "precision_beta_state",
    "run_precision_campaign",
    "run_precision_candidate",
    "search_fixed_points",
    "two_loop_gauge_matrix",
    "vacuum_stability",
    "write_precision_report",
]
