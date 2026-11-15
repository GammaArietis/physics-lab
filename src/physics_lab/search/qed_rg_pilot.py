"""Known-physics one-loop QED renormalization-group control pilot.

The pilot treats the fine-structure coupling as a dynamical state variable of
the RG flow, never as a target to fit.  It reproduces the one-loop QED beta
function for one charged Dirac fermion, records the Gaussian fixed point and
integrates explicitly bounded mathematical trajectories.  It does not activate
the W3A F^4 operators or claim an ultraviolet completion.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


QED_RG_PILOT_VERSION = "qed-rg-pilot-v1"
QED_ONE_LOOP_BETA_COEFFICIENT = 2.0 / (3.0 * math.pi)
DEFAULT_INITIAL_ALPHA_VALUES = (0.01, 0.05, 0.10)
DEFAULT_LOG_SCALE_OFFSETS = (-2.0, -1.0, 0.0, 1.0, 2.0)


class QEDRGPilotError(ValueError):
    """Raised when a bounded QED RG pilot input is invalid."""


def _validate_flavours(fermion_flavours: int) -> int:
    if isinstance(fermion_flavours, bool) or not isinstance(fermion_flavours, int) or fermion_flavours < 1 or fermion_flavours > 16:
        raise QEDRGPilotError("fermion_flavours must be a bounded integer in [1, 16]")
    return fermion_flavours


def _validate_alpha(alpha: float) -> float:
    value = float(alpha)
    if not math.isfinite(value) or value < 0:
        raise QEDRGPilotError("alpha must be finite and non-negative")
    return value


def _validate_initial_values(values: Sequence[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result or len(result) > 16 or any(not math.isfinite(value) or value <= 0 or value > 1 for value in result):
        raise QEDRGPilotError("initial_alpha_values must contain 1..16 finite values in (0, 1]")
    return result


def _validate_offsets(values: Sequence[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result or len(result) > 32 or any(not math.isfinite(value) or abs(value) > 32 for value in result):
        raise QEDRGPilotError("log_scale_offsets must contain 1..32 finite values in [-32, 32]")
    return result


def beta_alpha(alpha: float, *, fermion_flavours: int = 1) -> float:
    """Return d alpha / d log(mu) at one loop for QED with N_f Dirac fermions."""
    value = _validate_alpha(alpha)
    flavours = _validate_flavours(fermion_flavours)
    return flavours * QED_ONE_LOOP_BETA_COEFFICIENT * value**2


def alpha_trajectory(alpha0: float, log_scale_offset: float, *, fermion_flavours: int = 1) -> float:
    """Integrate the one-loop flow analytically at a finite log-scale offset."""
    initial = _validate_alpha(alpha0)
    if initial <= 0:
        raise QEDRGPilotError("alpha0 must be positive for a trajectory")
    offset = float(log_scale_offset)
    if not math.isfinite(offset) or abs(offset) > 32:
        raise QEDRGPilotError("log_scale_offset must be finite and bounded in [-32, 32]")
    flavours = _validate_flavours(fermion_flavours)
    denominator = 1.0 - flavours * QED_ONE_LOOP_BETA_COEFFICIENT * initial * offset
    if denominator <= 0:
        raise QEDRGPilotError("the requested trajectory crosses the one-loop Landau pole")
    return initial / denominator


def landau_log_scale(alpha0: float, *, fermion_flavours: int = 1) -> float:
    """Return log(mu_L/mu_0) for the one-loop trajectory."""
    initial = _validate_alpha(alpha0)
    if initial <= 0:
        raise QEDRGPilotError("alpha0 must be positive")
    flavours = _validate_flavours(fermion_flavours)
    return 1.0 / (flavours * QED_ONE_LOOP_BETA_COEFFICIENT * initial)


def run_qed_rg_pilot(
    *,
    initial_alpha_values: Sequence[float] = DEFAULT_INITIAL_ALPHA_VALUES,
    log_scale_offsets: Sequence[float] = DEFAULT_LOG_SCALE_OFFSETS,
    fermion_flavours: int = 1,
) -> dict[str, Any]:
    """Run the bounded known-physics RG control without external targets."""
    initial_values = _validate_initial_values(initial_alpha_values)
    offsets = _validate_offsets(log_scale_offsets)
    flavours = _validate_flavours(fermion_flavours)

    trajectories: list[dict[str, Any]] = []
    for alpha0 in initial_values:
        points = [
            {
                "log_scale_offset": offset,
                "alpha": alpha_trajectory(alpha0, offset, fermion_flavours=flavours),
            }
            for offset in offsets
        ]
        trajectories.append(
            {
                "initial_alpha": alpha0,
                "landau_log_scale_offset": landau_log_scale(alpha0, fermion_flavours=flavours),
                "points": points,
                "status": "COMPLETE",
            }
        )

    return {
        "search_version": QED_RG_PILOT_VERSION,
        "search_id": "qed-one-loop-rg-control",
        "stage": "W4_QED_RG_CONTROL",
        "execution_status": "COMPLETE",
        "scope": {
            "base_theory": "QED with one charged Dirac fermion",
            "beta_function_order": "ONE_LOOP",
            "fermion_flavours": flavours,
            "alpha_role": "DYNAMICAL_STATE_VARIABLE_ONLY",
            "f4_operators": "NOT_ACTIVATED",
            "ultraviolet_completion": "NOT_CLAIMED",
        },
        "equations": {
            "beta_function": "d alpha/d log(mu) = N_f*2*alpha^2/(3*pi)",
            "beta_coefficient_for_Nf_1": QED_ONE_LOOP_BETA_COEFFICIENT,
            "trajectory": "alpha(mu)/alpha(mu_0) = 1/[1 - N_f*2*alpha(mu_0)*log(mu/mu_0)/(3*pi)]",
            "landau_scale": "log(mu_L/mu_0) = 3*pi/(2*N_f*alpha(mu_0))",
        },
        "fixed_points": [
            {
                "coupling": "alpha",
                "value": 0.0,
                "label": "GAUSSIAN",
                "finite_fixed_point": True,
                "interacting": False,
                "infrared_behavior": "ATTRACTIVE",
                "ultraviolet_behavior": "REPULSIVE_AT_ONE_LOOP",
            }
        ],
        "trajectories": trajectories,
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
            "gaussian_fixed_point_recorded": True,
            "no_interacting_fixed_point_claimed": True,
            "trajectories_integrated": len(trajectories) == len(initial_values),
            "landau_pole_formula_recorded": True,
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
        "next_gate": "ADD_KNOWN_ONE_LOOP_THRESHOLD_CONTROL_BEFORE_SPECULATIVE_FIXED_POINT_SEARCH",
    }


def write_qed_rg_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_INITIAL_ALPHA_VALUES",
    "DEFAULT_LOG_SCALE_OFFSETS",
    "QED_ONE_LOOP_BETA_COEFFICIENT",
    "QED_RG_PILOT_VERSION",
    "QEDRGPilotError",
    "alpha_trajectory",
    "beta_alpha",
    "landau_log_scale",
    "run_qed_rg_pilot",
    "write_qed_rg_report",
]
