"""Threshold-resolved IR control for the vector-like gauge--Yukawa EFT.

This is the next controlled extension of the W13 model.  Each vector-like
multiplet receives an explicit mass threshold, the one-loop gauge coefficients
are recomputed from the representations active at each scale, and the
dimensionless state is matched continuously across thresholds.  The
Yukawa/scalar block remains the reduced W13 control; finite one-loop matching
corrections and a precision SM/BSM fit are intentionally outside this module.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.integrate import solve_ivp

from physics_lab.search.gauge_yukawa_vectorlike_extension import (
    DEFAULT_IR_SCALE_GEV,
    DEFAULT_UV_SCALE_GEV,
    LOOP_FACTOR,
    MULTIPLETS,
    PERTURBATIVE_BOUND,
    REFERENCE_ALPHA_ZERO,
    SM_GAUGE_B,
    ZERO_TOLERANCE,
    GaugeYukawaExtensionError,
    _finite,
    _multiplicity_map,
    _observable_record,
    action_record,
    beta_state,
    gauge_coefficients,
)


THRESHOLD_EFT_VERSION = "gauge-yukawa-threshold-eft-v1"


def threshold_map(values: Mapping[str, Any], multiplicities: Mapping[str, Any]) -> dict[str, float]:
    """Validate one positive decoupling scale for every present multiplet."""

    counts = _multiplicity_map(multiplicities)
    if not isinstance(values, Mapping):
        raise GaugeYukawaExtensionError("thresholds_gev must be a mapping")
    unknown = set(values) - set(MULTIPLETS)
    if unknown:
        raise GaugeYukawaExtensionError(f"unknown threshold multiplet: {sorted(unknown)}")
    result: dict[str, float] = {}
    for name, count in counts.items():
        if count and name not in values:
            raise GaugeYukawaExtensionError(f"missing threshold for present multiplet {name}")
        if name in values:
            result[name] = _finite(values[name], f"thresholds_gev[{name}]", lower=1.0e-9, upper=1.0e100)
    return result


def active_multiplicities(
    scale_gev: float,
    multiplicities: Mapping[str, Any],
    thresholds_gev: Mapping[str, float],
) -> dict[str, int]:
    """Return the representations active at a renormalisation scale."""

    scale = _finite(scale_gev, "scale_gev", lower=1.0e-9, upper=1.0e100)
    counts = _multiplicity_map(multiplicities)
    return {
        name: count if count and scale >= float(thresholds_gev[name]) else 0
        for name, count in counts.items()
    }


def thresholded_gauge_coefficients(
    scale_gev: float,
    multiplicities: Mapping[str, Any],
    thresholds_gev: Mapping[str, float],
) -> dict[str, float]:
    """Derive one-loop b_i from the representations active at ``scale_gev``."""

    return gauge_coefficients(active_multiplicities(scale_gev, multiplicities, thresholds_gev))


def _segment_boundaries(uv_scale: float, ir_scale: float, thresholds: Mapping[str, float]) -> list[float]:
    interior = sorted(
        {float(mass) for mass in thresholds.values() if ir_scale < float(mass) < uv_scale},
        reverse=True,
    )
    return [uv_scale, *interior, ir_scale]


def _threshold_events(
    multiplicities: Mapping[str, Any],
    thresholds: Mapping[str, float],
    uv_scale: float,
    ir_scale: float,
) -> list[dict[str, Any]]:
    events = []
    for name, mass in sorted(thresholds.items(), key=lambda item: (float(item[1]), item[0])):
        if ir_scale < float(mass) < uv_scale and _multiplicity_map(multiplicities)[name]:
            high = thresholded_gauge_coefficients(float(mass) * (1.0 + 1.0e-9), multiplicities, thresholds)
            low = thresholded_gauge_coefficients(float(mass) * (1.0 - 1.0e-9), multiplicities, thresholds)
            events.append(
                {
                    "multiplet": name,
                    "threshold_gev": float(mass),
                    "coefficients_above": high,
                    "coefficients_below": low,
                    "matching": "continuous_dimensionless_state_at_declared_threshold",
                }
            )
    return events


def run_threshold_candidate(
    candidate: Mapping[str, Any],
    *,
    uv_scale_gev: float,
    ir_scale_gev: float,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "unnamed"))
    multiplicities = _multiplicity_map(candidate.get("multiplicities", {}))
    yukawa_multiplet = str(candidate.get("yukawa_multiplet", ""))
    action = action_record(multiplicities, yukawa_multiplet)
    thresholds = threshold_map(candidate.get("thresholds_gev", {}), multiplicities)
    initial = tuple(
        _finite(value, f"initial_state[{index}]", lower=-PERTURBATIVE_BOUND, upper=PERTURBATIVE_BOUND)
        for index, value in enumerate(candidate.get("initial_state", []))
    )
    if len(initial) != 8:
        raise GaugeYukawaExtensionError("initial_state must have eight entries")
    uv_scale = _finite(uv_scale_gev, "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir_scale = _finite(ir_scale_gev, "ir_scale_gev", lower=1.0, upper=1.0e100)
    if uv_scale <= ir_scale:
        raise GaugeYukawaExtensionError("uv_scale_gev must exceed ir_scale_gev")

    state = np.asarray(initial, dtype=float)
    segments: list[dict[str, Any]] = []
    max_abs = float(np.max(np.abs(state)))
    boundaries = _segment_boundaries(uv_scale, ir_scale, thresholds)
    for high, low in zip(boundaries[:-1], boundaries[1:]):
        midpoint = math.sqrt(high * low)
        coefficients = thresholded_gauge_coefficients(midpoint, multiplicities, thresholds)
        solution = solve_ivp(
            lambda t, y: beta_state(
                t,
                y,
                multiplicities=multiplicities,
                yukawa_multiplet=yukawa_multiplet,
                gauge_coefficients_override=coefficients,
            ),
            (math.log(high), math.log(low)),
            state,
            rtol=1.0e-8,
            atol=1.0e-10,
            max_step=0.25,
        )
        if not solution.success or solution.y.size == 0:
            return {
                "candidate_id": candidate_id,
                "status": "INTEGRATION_FAILURE",
                "action": action,
                "thresholds_gev": thresholds,
                "segments": segments,
                "message": str(solution.message),
                "target_blind": True,
            }
        state = solution.y[:, -1]
        max_abs = max(max_abs, float(np.max(np.abs(solution.y))))
        segments.append(
            {
                "high_scale_gev": high,
                "low_scale_gev": low,
                "active_multiplicities": active_multiplicities(midpoint, multiplicities, thresholds),
                "gauge_coefficients": coefficients,
                "steps": int(solution.t.size),
                "matching": "continuous_state",
            }
        )

    final_state = tuple(float(value) for value in state)
    zero_protected = all(abs(value) <= ZERO_TOLERANCE for value in initial[:3]) and all(
        abs(value) <= ZERO_TOLERANCE for value in final_state[:3]
    )
    status = "ZERO_PROTECTED" if zero_protected else ("NONPERTURBATIVE" if max_abs >= PERTURBATIVE_BOUND else "COMPLETE")
    return {
        "candidate_id": candidate_id,
        "status": status,
        "action": action,
        "initial_state": list(initial),
        "final_state": list(final_state),
        "thresholds_gev": thresholds,
        "threshold_events": _threshold_events(multiplicities, thresholds, uv_scale, ir_scale),
        "segments": segments,
        "uv_observables": _observable_record(initial, uv_scale),
        "ir_observables": _observable_record(final_state, ir_scale),
        "controls": {
            "all_present_multiplet_thresholds_declared": True,
            "gauge_coefficients_derived_from_active_representations": True,
            "continuous_dimensionless_matching": True,
            "finite_threshold_corrections_claimed": False,
            "reduced_yukawa_scalar_block_explicit": True,
            "exact_zero_gauge_seed_inserted": False,
            "target_blind_generation": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
        },
        "integration": {"max_abs_coupling": max_abs, "segment_count": len(segments)},
        "target_blind": True,
    }


def run_threshold_campaign(activation: Mapping[str, Any]) -> dict[str, Any]:
    uv_scale = _finite(activation.get("uv_scale_gev", DEFAULT_UV_SCALE_GEV), "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir_scale = _finite(activation.get("ir_scale_gev", DEFAULT_IR_SCALE_GEV), "ir_scale_gev", lower=1.0, upper=1.0e100)
    candidates = activation.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GaugeYukawaExtensionError("activation must contain a non-empty candidates list")
    results = [run_threshold_candidate(candidate, uv_scale_gev=uv_scale, ir_scale_gev=ir_scale) for candidate in candidates]
    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "campaign_id": str(activation.get("campaign_id", "gauge-yukawa-threshold-eft")),
        "extension_version": THRESHOLD_EFT_VERSION,
        "execution_status": "COMPLETE",
        "scope": {
            "uv_scale_gev": uv_scale,
            "ir_scale_gev": ir_scale,
            "model": "W13 SM + singlet S + anomaly-free vector-like Dirac multiplets with explicit thresholds",
            "gauge_loop_order": "one-loop",
            "matter_block": "reduced one-loop Yukawa-scalar control",
            "matching": "continuous dimensionless one-loop control; finite threshold corrections not included",
        },
        "scan": {"candidate_count": len(results), "status_counts": status_counts},
        "controls": {
            "all_candidates_retained": True,
            "target_blind_generation": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "no_alpha_target_used": True,
            "no_precision_sm_matching_claimed": True,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": "Threshold-resolved EFT control only; no candidate is promoted and no alpha target is used.",
    }


def write_threshold_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "THRESHOLD_EFT_VERSION",
    "active_multiplicities",
    "run_threshold_candidate",
    "run_threshold_campaign",
    "threshold_map",
    "thresholded_gauge_coefficients",
    "write_threshold_report",
]
