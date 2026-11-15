"""Target-blind UV-to-IR flow campaign for the Eichhorn--Held truncation.

This module closes the mathematical part of the W11 pipeline: dimensionless
UV states are evolved through a finite gravity window and then through the
one-loop matter system with gravity decoupled.  The transition and endpoint
windows are pre-registered logarithmic controls, not physical mass scales.

The campaign deliberately does not introduce the electroweak vev, measured
masses, pole-mass corrections, alpha, or experimental data.  It therefore
reports dimensionless IR states and structural observables only.  A physical
SM matching calculation would require additional relevant inputs and higher
loop threshold/matching data, as stated by Eichhorn and Held.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from physics_lab.search.eichhorn_held_asymptotic_safety import (
    EichhornHeldError,
    PUBLISHED_GRAVITY_ANCHOR,
    beta_full,
    beta_matter,
    gravity_equation_fixed_point,
    matter_fixed_points,
)


IR_MATCHING_VERSION = "eichhorn-held-ir-matching-v1"
MAX_ABS_STATE = 20.0
DEFAULT_STEPS_PER_UNIT = 12
INTEGRATION_TOLERANCE = 1e-10

SOURCE_UV_MATTER = {
    "g1": 0.0,
    "g2": 0.0,
    "g3": 0.0,
    "y_t": 0.36,
    "y_b": 0.0,
    "lambda_4": 0.01,
}

DEFAULT_GRAVITY_TRANSITION_OFFSETS: tuple[float, ...] = (-2.0, -4.0, -6.0)
DEFAULT_IR_ENDPOINT_OFFSETS: tuple[float, ...] = (-8.0, -16.0, -32.0)
DEFAULT_GAUGE_SEEDS: tuple[float, ...] = (0.0, 0.02, 0.05)
DEFAULT_TOP_DELTAS: tuple[float, ...] = (-0.06, 0.0, 0.06)
DEFAULT_BOTTOM_SEEDS: tuple[float, ...] = (-0.02, 0.0, 0.02)
DEFAULT_HIGGS_DELTAS: tuple[float, ...] = (-0.01, 0.0, 0.01)


class EichhornHeldIRMatchingError(ValueError):
    """Raised when an IR matching input is invalid."""


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or abs(result) > MAX_ABS_STATE:
        raise EichhornHeldIRMatchingError(f"{name} must be finite and bounded")
    return result


def _state(values: Sequence[float]) -> tuple[float, ...]:
    if len(values) != 8:
        raise EichhornHeldIRMatchingError("state must contain G_N, Lambda, g1, g2, g3, y_t, y_b and lambda_4")
    return tuple(
        _finite(value, name)
        for value, name in zip(values, ("G_N", "Lambda", "g1", "g2", "g3", "y_t", "y_b", "lambda_4"))
    )


def _ir_beta(values: Sequence[float]) -> tuple[float, ...]:
    state = _state(values)
    matter = beta_matter(state[2:], G_N=0.0, Lambda=0.0)
    return (0.0, 0.0, *matter)


def _rk4_step(beta, state: tuple[float, ...], step: float) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta(state)
    k2 = beta(shifted(state, k1, step / 2.0))
    k3 = beta(shifted(state, k2, step / 2.0))
    k4 = beta(shifted(state, k3, step))
    return tuple(
        state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0
        for index in range(len(state))
    )


def _integrate_segment(
    state: tuple[float, ...],
    start: float,
    end: float,
    beta,
    *,
    steps_per_unit: int,
) -> tuple[str, tuple[float, ...], str | None]:
    distance = end - start
    count = max(1, int(math.ceil(abs(distance) * steps_per_unit)))
    step = distance / count
    current = state
    try:
        for _ in range(count):
            current = _rk4_step(beta, current, step)
            if any(not math.isfinite(value) or abs(value) > MAX_ABS_STATE for value in current):
                return "BOUND_REACHED", current, "finite-state bound reached"
    except (EichhornHeldError, EichhornHeldIRMatchingError) as exc:
        return "THRESHOLD_POLE", current, str(exc)
    except (OverflowError, FloatingPointError, ZeroDivisionError) as exc:
        return "NUMERICAL_FAILURE", current, str(exc)
    return "COMPLETE", current, None


def dimensionless_ir_observables(state: Sequence[float]) -> dict[str, Any]:
    """Compute internal ratios without using a measured target."""

    try:
        values = _state(state)
    except EichhornHeldIRMatchingError as exc:
        return {
            "state_valid": False,
            "state_error": str(exc),
            "gauge_norm": None,
            "top_to_qcd_ratio": None,
            "bottom_to_top_ratio": None,
            "quartic_to_top_squared": None,
            "matter_state_nonnegative": None,
            "quartic_nonnegative": None,
            "perturbative_matter_state": False,
        }
    g1, g2, g3, yt, yb, lam4 = values[2:]
    gauge_norm = math.sqrt(g1 * g1 + g2 * g2 + g3 * g3)
    return {
        "state_valid": True,
        "gauge_norm": gauge_norm,
        "top_to_qcd_ratio": None if abs(g3) < 1e-12 else yt / g3,
        "bottom_to_top_ratio": None if abs(yt) < 1e-12 else yb / yt,
        "quartic_to_top_squared": None if abs(yt) < 1e-12 else lam4 / (yt * yt),
        "matter_state_nonnegative": all(value >= -1e-12 for value in values[2:]),
        "quartic_nonnegative": lam4 >= -1e-12,
        "perturbative_matter_state": max(abs(value) for value in values[2:]) < 1.0,
    }


def integrate_target_blind_trajectory(
    initial_state: Sequence[float],
    *,
    gravity_transition_offset: float,
    ir_endpoint_offset: float,
    steps_per_unit: int = DEFAULT_STEPS_PER_UNIT,
) -> dict[str, Any]:
    """Integrate UV gravity+matter, then IR matter-only, toward lower scales."""

    uv = _state(initial_state)
    transition = float(gravity_transition_offset)
    endpoint = float(ir_endpoint_offset)
    if not math.isfinite(transition) or not math.isfinite(endpoint):
        raise EichhornHeldIRMatchingError("scale offsets must be finite")
    if not endpoint < transition < 0.0:
        raise EichhornHeldIRMatchingError("require ir_endpoint_offset < gravity_transition_offset < 0")

    gravity_status, at_transition, gravity_error = _integrate_segment(
        uv,
        0.0,
        transition,
        beta_full,
        steps_per_unit=steps_per_unit,
    )
    points: list[dict[str, Any]] = [
        {"stage": "UV", "log_scale_offset": 0.0, "state": list(uv)},
    ]
    if gravity_status != "COMPLETE":
        return {
            "status": gravity_status,
            "error": gravity_error,
            "gravity_transition_offset": transition,
            "ir_endpoint_offset": endpoint,
            "points": points,
            "final_state": list(at_transition),
            "observables": dimensionless_ir_observables(at_transition),
        }

    points.append({"stage": "GRAVITY_MATCH", "log_scale_offset": transition, "state": list(at_transition)})
    decoupled = (0.0, 0.0, *at_transition[2:])
    ir_status, at_ir, ir_error = _integrate_segment(
        decoupled,
        transition,
        endpoint,
        _ir_beta,
        steps_per_unit=steps_per_unit,
    )
    points.append({"stage": "IR", "log_scale_offset": endpoint, "state": list(at_ir)})
    return {
        "status": ir_status,
        "error": ir_error,
        "gravity_transition_offset": transition,
        "ir_endpoint_offset": endpoint,
        "points": points,
        "final_state": list(at_ir),
        "observables": dimensionless_ir_observables(at_ir),
        "gravity_decoupled_below_transition": True,
    }


def _gravity_initializations() -> list[dict[str, Any]]:
    exact = gravity_equation_fixed_point()["state"]
    return [
        {
            "id": "published-rounded-anchor",
            "state": (PUBLISHED_GRAVITY_ANCHOR["G_N"], PUBLISHED_GRAVITY_ANCHOR["Lambda"]),
            "source": "Eichhorn--Held Eq. (9), rounded",
        },
        {
            "id": "printed-equation-root",
            "state": (exact[0], exact[1]),
            "source": "root of corrected printed beta functions",
        },
    ]


def _fixed_point_branch_initializations(gravity: Mapping[str, Any]) -> list[dict[str, Any]]:
    G_N, Lambda = gravity["state"]
    points = matter_fixed_points(G_N=G_N, Lambda=Lambda)
    branches: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        state = (G_N, Lambda, *point["state"])
        branches.append({
            "id": f"{gravity['id']}-matter-branch-{index:03d}",
            "kind": "enumerated-matter-fixed-point",
            "gravity_initialization": gravity["id"],
            "state": state,
            "fixed_point_residual": point["max_residual"],
            "labels": point["labels"],
        })
    return branches


def _source_neighborhood_initializations(
    *,
    gravity_state: Sequence[float],
    gauge_seeds: Sequence[float] = DEFAULT_GAUGE_SEEDS,
    top_deltas: Sequence[float] = DEFAULT_TOP_DELTAS,
    bottom_seeds: Sequence[float] = DEFAULT_BOTTOM_SEEDS,
    higgs_deltas: Sequence[float] = DEFAULT_HIGGS_DELTAS,
) -> list[dict[str, Any]]:
    G_N, Lambda = tuple(float(value) for value in gravity_state)
    initializations: list[dict[str, Any]] = []
    for index, (g1, g2, g3, top_delta, yb, higgs_delta) in enumerate(
        itertools.product(gauge_seeds, gauge_seeds, gauge_seeds, top_deltas, bottom_seeds, higgs_deltas)
    ):
        state = (G_N, Lambda, g1, g2, g3, 0.36 + top_delta, yb, 0.01 + higgs_delta)
        initializations.append({
            "id": f"source-neighborhood-{index:04d}",
            "kind": "source-uv-neighborhood",
            "gravity_initialization": "printed-equation-root",
            "state": state,
            "source_uv_reference": dict(SOURCE_UV_MATTER),
        })
    return initializations


def _run_case(initialization: Mapping[str, Any], transition: float, endpoint: float, steps_per_unit: int) -> dict[str, Any]:
    trajectory = integrate_target_blind_trajectory(
        initialization["state"],
        gravity_transition_offset=transition,
        ir_endpoint_offset=endpoint,
        steps_per_unit=steps_per_unit,
    )
    points = trajectory.get("points", [])
    gravity_match = next((point["state"] for point in points if point["stage"] == "GRAVITY_MATCH"), None)
    return {
        "initialization_id": initialization["id"],
        "initialization_kind": initialization["kind"],
        "gravity_initialization": initialization.get("gravity_initialization"),
        "gravity_transition_offset": transition,
        "ir_endpoint_offset": endpoint,
        "initial_state": list(initialization["state"]),
        "status": trajectory["status"],
        "error": trajectory.get("error"),
        "gravity_match_state": gravity_match,
        "final_state": trajectory["final_state"],
        "observables": trajectory["observables"],
    }


def run_ir_matching_campaign(
    *,
    transition_offsets: Sequence[float] = DEFAULT_GRAVITY_TRANSITION_OFFSETS,
    ir_endpoint_offsets: Sequence[float] = DEFAULT_IR_ENDPOINT_OFFSETS,
    include_neighborhood: bool = True,
    steps_per_unit: int = DEFAULT_STEPS_PER_UNIT,
) -> dict[str, Any]:
    """Run all declared branch, neighborhood and window combinations."""

    transitions = tuple(float(value) for value in transition_offsets)
    endpoints = tuple(float(value) for value in ir_endpoint_offsets)
    if not transitions or not endpoints:
        raise EichhornHeldIRMatchingError("transition and endpoint grids cannot be empty")
    gravities = _gravity_initializations()
    initializations: list[dict[str, Any]] = []
    for gravity in gravities:
        initializations.extend(_fixed_point_branch_initializations(gravity))
    if include_neighborhood:
        root_gravity = next(item for item in gravities if item["id"] == "printed-equation-root")
        initializations.extend(_source_neighborhood_initializations(gravity_state=root_gravity["state"]))

    cases: list[dict[str, Any]] = []
    for initialization in initializations:
        for transition, endpoint in itertools.product(transitions, endpoints):
            if endpoint < transition < 0.0:
                cases.append(_run_case(initialization, transition, endpoint, steps_per_unit))

    status_counts: dict[str, int] = {}
    for case in cases:
        status = case["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    complete = [case for case in cases if case["status"] == "COMPLETE"]
    positive_quartic = sum(case["observables"]["quartic_nonnegative"] for case in complete)
    nonzero_gauge = sum(case["observables"]["gauge_norm"] > 1e-12 for case in complete)
    return {
        "matching_version": IR_MATCHING_VERSION,
        "campaign_id": "eichhorn-held-target-blind-ir-matching",
        "execution_status": "COMPLETE",
        "scope": {
            "uv_system": "corrected Eichhorn--Held Einstein--Hilbert plus SM one-loop truncation",
            "gravity_window": "full coupled beta functions from log(k/k_UV)=0 to transition offset",
            "ir_window": "matter-only one-loop beta functions after explicit gravity decoupling",
            "scale_units": "dimensionless logarithmic offsets only",
            "mass_matching": "NOT_IMPLEMENTED",
            "electroweak_vev": "NOT_USED",
            "pole_mass_conversion": "NOT_IMPLEMENTED",
            "higher_loop_sm_matching": "NOT_IMPLEMENTED",
        },
        "inputs": {
            "gravity_initialization_count": len(gravities),
            "gravity_initializations": gravities,
            "gravity_transition_offsets": list(transitions),
            "ir_endpoint_offsets": list(endpoints),
            "window_combination_count": sum(endpoint < transition < 0.0 for transition, endpoint in itertools.product(transitions, endpoints)),
            "include_all_enumerated_matter_fixed_points": True,
            "include_source_uv_neighborhood": include_neighborhood,
            "source_neighborhood_size": 729 if include_neighborhood else 0,
            "steps_per_unit": steps_per_unit,
        },
        "scan": {
            "initialization_count": len(initializations),
            "trajectory_count": len(cases),
            "status_counts": status_counts,
            "complete_count": len(complete),
            "complete_nonnegative_quartic_count": positive_quartic,
            "complete_nonzero_gauge_count": nonzero_gauge,
        },
        "cases": cases,
        "observables": {
            "dimensionless_only": True,
            "gauge_norm": "sqrt(g1^2+g2^2+g3^2)",
            "top_to_qcd_ratio": "y_t/g3 when g3 is nonzero",
            "bottom_to_top_ratio": "y_b/y_t when y_t is nonzero",
            "quartic_to_top_squared": "lambda_4/y_t^2 when y_t is nonzero",
            "measured_mass_target": False,
            "alpha_target": False,
            "empirical_comparison": "NOT_AUTHORIZED",
        },
        "controls": {
            "target_blind_generation": True,
            "all_enumerated_matter_branches_retained": True,
            "source_uv_neighborhood_pre_registered": True,
            "gravity_transition_grid_pre_registered": True,
            "ir_endpoint_grid_pre_registered": True,
            "no_electroweak_vev_input": True,
            "no_measured_masses": True,
            "no_pole_mass_conversion": True,
            "no_external_data": True,
            "no_alpha_fit": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "negative_results_recorded": True,
        },
        "conclusions": {
            "mathematical_uv_to_ir_flow_executed": True,
            "gravity_decoupling_control_executed": True,
            "dimensionless_ir_states_generated": True,
            "physical_sm_mass_matching_completed": False,
            "alpha_one_over_137_derived": False,
            "interpretation": "The corrected W11 truncation can be evolved through declared dimensionless UV-to-IR windows without experimental targets. The result is a target-blind flow atlas, not yet a physical SM mass prediction.",
        },
        "bibliography": [
            {
                "id": "eichhorn-held-2018",
                "citation": "A. Eichhorn and A. Held, Top mass from asymptotic safety, Phys. Lett. B 777, 217--221 (2018).",
                "doi": "10.1016/j.physletb.2017.12.040",
                "role": "UV fixed-point branch, one-loop gravity-dressed matter flow and matching caveats.",
            },
            {
                "id": "degrassi-et-al-2012",
                "citation": "G. Degrassi et al., Higgs mass and vacuum stability in the Standard Model at NNLO, JHEP 08 (2012) 098.",
                "doi": "10.1007/JHEP08(2012)098",
                "role": "Primary reference for why precision IR Higgs matching requires higher-loop running and threshold relations; not executed here.",
            },
        ],
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "next_gate": "REQUIRE_EXPLICIT_IR_MATCHING_INPUTS_BEFORE_ANY_MASS_OR_EMPIRICAL_COMPARISON",
    }


def write_ir_matching_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_GRAVITY_TRANSITION_OFFSETS",
    "DEFAULT_IR_ENDPOINT_OFFSETS",
    "DEFAULT_STEPS_PER_UNIT",
    "EichhornHeldIRMatchingError",
    "IR_MATCHING_VERSION",
    "SOURCE_UV_MATTER",
    "dimensionless_ir_observables",
    "integrate_target_blind_trajectory",
    "run_ir_matching_campaign",
    "write_ir_matching_report",
]
