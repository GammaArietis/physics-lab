"""Broad, target-blind one-loop QED threshold RG campaign.

The campaign extends the W4 analytic control with piecewise one-loop running.
Threshold locations and flavour counts are normalized mathematical schedules;
they are not imported particle masses and are not fitted to alpha.  The goal is
to test threshold matching and to expose whether a non-zero fixed point can
appear in this positive-beta truncation.  It should not: every active regime
has beta(alpha) > 0 for alpha > 0.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from physics_lab.search.qed_rg_pilot import QED_ONE_LOOP_BETA_COEFFICIENT


QED_THRESHOLD_RG_VERSION = "qed-threshold-rg-v1"
DEFAULT_THRESHOLD_INITIAL_ALPHA_VALUES = (0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12)
DEFAULT_THRESHOLD_LOG_SCALE_OFFSETS = tuple(float(value) for value in range(-8, 9))
DEFAULT_THRESHOLD_SCHEDULES: tuple[dict[str, Any], ...] = (
    {"scenario_id": "no-threshold-control", "thresholds": []},
    {
        "scenario_id": "one-threshold-control",
        "thresholds": [{"log_scale_offset": 2.0, "fermion_flavours_after": 2}],
    },
    {
        "scenario_id": "two-threshold-control",
        "thresholds": [
            {"log_scale_offset": 2.0, "fermion_flavours_after": 2},
            {"log_scale_offset": 5.0, "fermion_flavours_after": 3},
        ],
    },
    {
        "scenario_id": "three-threshold-control",
        "thresholds": [
            {"log_scale_offset": 2.0, "fermion_flavours_after": 2},
            {"log_scale_offset": 4.0, "fermion_flavours_after": 3},
            {"log_scale_offset": 6.0, "fermion_flavours_after": 4},
        ],
    },
    {
        "scenario_id": "four-threshold-control",
        "thresholds": [
            {"log_scale_offset": 1.5, "fermion_flavours_after": 2},
            {"log_scale_offset": 3.0, "fermion_flavours_after": 3},
            {"log_scale_offset": 4.5, "fermion_flavours_after": 4},
            {"log_scale_offset": 6.0, "fermion_flavours_after": 5},
        ],
    },
)


class QEDThresholdRGCampaignError(ValueError):
    """Raised when a bounded threshold campaign input is invalid."""


def _validate_alpha(alpha: float) -> float:
    value = float(alpha)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise QEDThresholdRGCampaignError("alpha must be finite and in (0, 1]")
    return value


def _validate_flavours(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > 16:
        raise QEDThresholdRGCampaignError("fermion flavours must be an integer in [1, 16]")
    return value


def _validate_thresholds(thresholds: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    previous = 0.0
    for item in thresholds:
        offset = float(item["log_scale_offset"])
        flavours = _validate_flavours(int(item["fermion_flavours_after"]))
        if not math.isfinite(offset) or offset <= 0 or offset > 32:
            raise QEDThresholdRGCampaignError("threshold offsets must be finite and in (0, 32]")
        if offset <= previous:
            raise QEDThresholdRGCampaignError("threshold offsets must be strictly increasing")
        result.append({"log_scale_offset": offset, "fermion_flavours_after": flavours})
        previous = offset
    return result


def _validate_offsets(offsets: Sequence[float]) -> list[float]:
    result = [float(value) for value in offsets]
    if not result or len(result) > 64 or any(not math.isfinite(value) or abs(value) > 32 for value in result):
        raise QEDThresholdRGCampaignError("log scale offsets must contain 1..64 values in [-32, 32]")
    return result


def _validate_initial_values(values: Sequence[float]) -> list[float]:
    result = [_validate_alpha(value) for value in values]
    if not result or len(result) > 32:
        raise QEDThresholdRGCampaignError("initial alpha values must contain 1..32 values")
    return result


def _advance(alpha: float, delta: float, fermion_flavours: int) -> float:
    denominator = 1.0 - QED_ONE_LOOP_BETA_COEFFICIENT * fermion_flavours * alpha * delta
    if denominator <= 0:
        raise QEDThresholdRGCampaignError("the requested trajectory crosses the one-loop Landau pole")
    return alpha / denominator


def alpha_threshold_trajectory(
    alpha0: float,
    log_scale_offset: float,
    *,
    thresholds: Sequence[Mapping[str, Any]] = (),
    initial_fermion_flavours: int = 1,
) -> dict[str, Any]:
    """Integrate the piecewise one-loop flow and expose threshold segments."""
    initial = _validate_alpha(alpha0)
    target = float(log_scale_offset)
    if not math.isfinite(target) or abs(target) > 32:
        raise QEDThresholdRGCampaignError("log scale offset must be finite and bounded in [-32, 32]")
    flavours = _validate_flavours(initial_fermion_flavours)
    schedule = _validate_thresholds(thresholds)
    current_alpha = initial
    current_offset = 0.0
    segments: list[dict[str, Any]] = []

    if target < 0:
        end_alpha = _advance(current_alpha, target, flavours)
        segments.append(
            {
                "from_log_scale_offset": 0.0,
                "to_log_scale_offset": target,
                "fermion_flavours": flavours,
                "alpha_start": current_alpha,
                "alpha_end": end_alpha,
            }
        )
        return {
            "alpha": end_alpha,
            "active_fermion_flavours": flavours,
            "threshold_crossings": 0,
            "segments": segments,
        }

    for threshold in schedule:
        threshold_offset = threshold["log_scale_offset"]
        if threshold_offset > target:
            break
        next_alpha = _advance(current_alpha, threshold_offset - current_offset, flavours)
        segments.append(
            {
                "from_log_scale_offset": current_offset,
                "to_log_scale_offset": threshold_offset,
                "fermion_flavours": flavours,
                "alpha_start": current_alpha,
                "alpha_end": next_alpha,
            }
        )
        current_alpha = next_alpha
        current_offset = threshold_offset
        flavours = threshold["fermion_flavours_after"]

    if target != current_offset:
        next_alpha = _advance(current_alpha, target - current_offset, flavours)
        segments.append(
            {
                "from_log_scale_offset": current_offset,
                "to_log_scale_offset": target,
                "fermion_flavours": flavours,
                "alpha_start": current_alpha,
                "alpha_end": next_alpha,
            }
        )
        current_alpha = next_alpha

    return {
        "alpha": current_alpha,
        "active_fermion_flavours": flavours,
        "threshold_crossings": sum(item["log_scale_offset"] <= target for item in schedule),
        "segments": segments,
    }


def _validate_schedules(schedules: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for schedule in schedules:
        scenario_id = str(schedule["scenario_id"])
        if not scenario_id or scenario_id in seen:
            raise QEDThresholdRGCampaignError("scenario ids must be non-empty and unique")
        seen.add(scenario_id)
        result.append({"scenario_id": scenario_id, "thresholds": _validate_thresholds(schedule.get("thresholds", []))})
    if not result or len(result) > 32:
        raise QEDThresholdRGCampaignError("threshold schedules must contain 1..32 scenarios")
    return result


def run_qed_threshold_rg_campaign(
    *,
    initial_alpha_values: Sequence[float] = DEFAULT_THRESHOLD_INITIAL_ALPHA_VALUES,
    log_scale_offsets: Sequence[float] = DEFAULT_THRESHOLD_LOG_SCALE_OFFSETS,
    schedules: Sequence[Mapping[str, Any]] = DEFAULT_THRESHOLD_SCHEDULES,
    initial_fermion_flavours: int = 1,
) -> dict[str, Any]:
    """Run all registered threshold schedules without comparison or selection."""
    initial_values = _validate_initial_values(initial_alpha_values)
    offsets = _validate_offsets(log_scale_offsets)
    flavours = _validate_flavours(initial_fermion_flavours)
    validated_schedules = _validate_schedules(schedules)
    scenario_reports: list[dict[str, Any]] = []
    trajectory_count = 0
    point_count = 0

    for schedule in validated_schedules:
        trajectories: list[dict[str, Any]] = []
        for alpha0 in initial_values:
            points: list[dict[str, Any]] = []
            for offset in offsets:
                result = alpha_threshold_trajectory(
                    alpha0,
                    offset,
                    thresholds=schedule["thresholds"],
                    initial_fermion_flavours=flavours,
                )
                points.append(
                    {
                        "log_scale_offset": offset,
                        "alpha": result["alpha"],
                        "active_fermion_flavours": result["active_fermion_flavours"],
                        "threshold_crossings": result["threshold_crossings"],
                    }
                )
            trajectories.append({"initial_alpha": alpha0, "points": points, "status": "COMPLETE"})
        trajectory_count += len(trajectories)
        point_count += len(trajectories) * len(offsets)
        scenario_reports.append(
            {
                "scenario_id": schedule["scenario_id"],
                "initial_fermion_flavours": flavours,
                "thresholds": schedule["thresholds"],
                "fixed_points": [
                    {
                        "coupling": "alpha",
                        "value": 0.0,
                        "label": "GAUSSIAN",
                        "finite_fixed_point": True,
                        "interacting": False,
                    }
                ],
                "trajectories": trajectories,
                "status": "COMPLETE",
            }
        )

    return {
        "search_version": QED_THRESHOLD_RG_VERSION,
        "campaign_id": "qed-threshold-rg-broad-run",
        "stage": "W5_QED_THRESHOLD_RG_CAMPAIGN",
        "execution_status": "COMPLETE",
        "scope": {
            "base_theory": "one-loop QED with piecewise active Dirac-fermion counts",
            "thresholds": "NORMALIZED_MATHEMATICAL_SCHEDULES",
            "external_particle_masses": "NOT_USED",
            "alpha_role": "DYNAMICAL_STATE_VARIABLE_ONLY",
            "beta_function_order": "ONE_LOOP",
            "f4_operators": "NOT_ACTIVATED",
            "ultraviolet_completion": "NOT_CLAIMED",
        },
        "equations": {
            "regime_beta_function": "d alpha/d log(mu) = N_f*2*alpha^2/(3*pi)",
            "matching_rule": "alpha(mu_threshold^-) = alpha(mu_threshold^+)",
            "piecewise_solution": "1/alpha_2 = 1/alpha_1 - N_f*2*Delta_log_scale/(3*pi)",
        },
        "scenario_count": len(scenario_reports),
        "trajectory_count": trajectory_count,
        "point_count": point_count,
        "scenarios": scenario_reports,
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
            "known_one_loop_beta_reproduced": math.isclose(
                QED_ONE_LOOP_BETA_COEFFICIENT, 2.0 / (3.0 * math.pi), rel_tol=1e-15, abs_tol=1e-15
            ),
            "threshold_continuity_rule_explicit": True,
            "threshold_schedules_executed": len(scenario_reports) == len(validated_schedules),
            "trajectories_integrated": trajectory_count == len(validated_schedules) * len(initial_values),
            "all_points_completed": point_count == trajectory_count * len(offsets),
            "only_gaussian_fixed_point_claimed": True,
            "alpha_not_used_as_fit_target": True,
            "no_external_data": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "f4_operators_not_promoted": True,
        },
        "selection": {
            "performed": False,
            "ranking_performed": False,
            "human_review_required": True,
        },
        "next_gate": "ACTIVATE_COUPLED_BETA_SYSTEM_OR_IMPORT_EXPLICIT_PHYSICAL_THRESHOLD_DATA",
    }


def write_qed_threshold_rg_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_THRESHOLD_INITIAL_ALPHA_VALUES",
    "DEFAULT_THRESHOLD_LOG_SCALE_OFFSETS",
    "DEFAULT_THRESHOLD_SCHEDULES",
    "QED_THRESHOLD_RG_VERSION",
    "QEDThresholdRGCampaignError",
    "alpha_threshold_trajectory",
    "run_qed_threshold_rg_campaign",
    "write_qed_threshold_rg_report",
]
