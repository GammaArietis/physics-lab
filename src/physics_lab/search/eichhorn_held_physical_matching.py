"""Dimensionful UV-to-IR matching campaign for the Eichhorn--Held control.

The module is intentionally explicit about scope.  It combines the corrected
Einstein--Hilbert plus Standard Model truncation already implemented in W11
with:

* declared dimensionful reference scales;
* pre-registered decoupling schedules;
* a two-loop gauge beta-function control for the SM;
* a one-loop QCD pole-mass conversion for the top and a tree-level Higgs
  conversion control;
* regulator/truncation ensembles around the published gravity anchor.

It does *not* claim a complete two-loop SM or NNLO matching calculation.  The
full two-loop Yukawa/Higgs beta functions, electroweak threshold relations and
NNLO pole conversions are recorded as missing gates rather than silently
approximated.  No experimental value is used to fit or select a trajectory.
The optional comparison block is applied only to already-generated outputs.
"""

from __future__ import annotations

import gzip
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from physics_lab.search.eichhorn_held_asymptotic_safety import (
    PUBLISHED_GRAVITY_ANCHOR,
    beta_full,
    beta_matter,
    gravity_equation_fixed_point,
)
from physics_lab.search.eichhorn_held_ir_matching import (
    _fixed_point_branch_initializations,
    _gravity_initializations,
    _source_neighborhood_initializations,
    _integrate_segment,
)


PHYSICAL_MATCHING_VERSION = "eichhorn-held-physical-matching-v2"
LOOP_FACTOR = 16.0 * math.pi**2
REDUCED_PLANCK_SCALE_GEV = 2.435e18
ELECTROWEAK_VEV_GEV = 246.21965
LOW_SCALE_PROBE_GEV = 2.0
MAX_STATE_BOUND = 20.0
DEFAULT_STEPS_PER_UNIT = 6

# These are deliberately dimensionless fractions of v, not measured masses.
# They are a sensitivity grid for threshold placement.  The experimental
# comparison is kept separate and is never used to choose a schedule.
DEFAULT_THRESHOLD_SCHEDULES: tuple[dict[str, Any], ...] = (
    {"id": "no-decoupling", "top_over_v": None, "higgs_over_v": None, "ew_over_v": None},
    {"id": "threshold-low", "top_over_v": 0.50, "higgs_over_v": 0.40, "ew_over_v": 0.30},
    {"id": "threshold-central", "top_over_v": 0.75, "higgs_over_v": 0.50, "ew_over_v": 0.40},
    {"id": "threshold-high", "top_over_v": 1.25, "higgs_over_v": 1.00, "ew_over_v": 0.80},
)
DEFAULT_GRAVITY_TRANSITION_OFFSETS: tuple[float, ...] = (-2.0, -4.0, -6.0)
DEFAULT_LOOP_MODES: tuple[str, ...] = (
    "one-loop-sm",
    "two-loop-gauge-control",
    "two-loop-sm-top-dominance",
)


class PhysicalMatchingError(ValueError):
    """Raised for invalid physical-matching inputs."""


@dataclass(frozen=True)
class ThresholdSchedule:
    identifier: str
    top_gev: float | None
    higgs_gev: float | None
    electroweak_gev: float | None


def _finite(value: float, name: str, *, lower: float = -MAX_STATE_BOUND, upper: float = MAX_STATE_BOUND) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise PhysicalMatchingError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _matter_state(values: Sequence[float]) -> tuple[float, ...]:
    if len(values) != 6:
        raise PhysicalMatchingError("matter state must contain g1, g2, g3, y_t, y_b and lambda_4")
    return tuple(
        _finite(value, name, lower=-100.0, upper=100.0)
        for value, name in zip(values, ("g1", "g2", "g3", "y_t", "y_b", "lambda_4"))
    )


def _schedule(value: Mapping[str, Any]) -> ThresholdSchedule:
    identifier = str(value["id"])
    result: list[float | None] = []
    for key in ("top_over_v", "higgs_over_v", "ew_over_v"):
        fraction = value.get(key)
        if fraction is None:
            result.append(None)
            continue
        fraction = float(fraction)
        if not math.isfinite(fraction) or fraction <= 0.0 or fraction > 4.0:
            raise PhysicalMatchingError(f"{key} must be in (0, 4]")
        result.append(fraction * ELECTROWEAK_VEV_GEV)
    return ThresholdSchedule(identifier, result[0], result[1], result[2])


def _two_loop_gauge_correction(state: Sequence[float]) -> tuple[float, float, float]:
    """Known SM two-loop gauge control in the GUT-normalized g1 convention."""

    g1, g2, g3, yt, _yb, _lam = _matter_state(state)
    return (
        g1**3
        * (199.0 / 50.0 * g1**2 + 27.0 / 10.0 * g2**2 + 44.0 / 5.0 * g3**2 - 17.0 / 10.0 * yt**2)
        / LOOP_FACTOR**2,
        g2**3
        * (9.0 / 10.0 * g1**2 + 35.0 / 6.0 * g2**2 + 12.0 * g3**2 - 3.0 / 2.0 * yt**2)
        / LOOP_FACTOR**2,
        g3**3
        * (11.0 / 10.0 * g1**2 + 9.0 / 2.0 * g2**2 - 26.0 * g3**2 - 2.0 * yt**2)
        / LOOP_FACTOR**2,
    )


def _two_loop_sm_top_dominance_correction(state: Sequence[float]) -> tuple[float, ...]:
    """Two-loop SM correction for the top-dominance control.

    The published SM equations use the conventional quartic ``lambda`` in
    ``V = lambda (H^dagger H)^2``.  Eichhorn--Held use ``lambda_4`` with
    ``lambda = 2*lambda_4``.  The returned quartic component is therefore one
    half of the conventional two-loop beta polynomial evaluated at
    ``lambda = 2*lambda_4``.
    """

    g1, g2, g3, yt, _yb, lambda_4 = _matter_state(state)
    lam = 2.0 * lambda_4
    gauge = _two_loop_gauge_correction(state)
    beta_yt_2 = yt * (
        -12.0 * yt**4
        + (393.0 / 80.0 * g1**2 + 225.0 / 16.0 * g2**2 + 36.0 * g3**2) * yt**2
        + 1187.0 / 600.0 * g1**4
        - 9.0 / 20.0 * g1**2 * g2**2
        + 19.0 / 15.0 * g1**2 * g3**2
        - 23.0 / 4.0 * g2**4
        + 9.0 * g2**2 * g3**2
        - 108.0 * g3**4
        + 1.5 * lam**2
        - 6.0 * lam * yt**2
    ) / LOOP_FACTOR**2
    beta_lambda_std_2 = (
        10.0 * lam * yt**2 * (17.0 / 20.0 * g1**2 + 9.0 / 4.0 * g2**2 + 8.0 * g3**2)
        + 18.0 * lam**2 * (3.0 / 5.0 * g1**2 + 3.0 * g2**2)
        - lam * (117.0 / 20.0 * g1**2 * g2**2 - 1887.0 / 200.0 * g1**4 + 73.0 / 8.0 * g2**4)
        - 1677.0 / 200.0 * g1**4 * g2**2
        - 289.0 / 40.0 * g1**2 * g2**4
        - 3.0 / 5.0 * g1**2 * yt**2 * (57.0 / 10.0 * g1**2 - 21.0 * g2**2)
        - 3411.0 / 1000.0 * g1**6
        - 16.0 / 5.0 * g1**2 * yt**4
        + 305.0 / 8.0 * g2**6
        - 9.0 / 2.0 * g2**4 * yt**2
        - 64.0 * g3**2 * yt**4
        - 78.0 * lam**3
        - 72.0 * lam**2 * yt**2
        - 3.0 * lam * yt**4
        + 60.0 * yt**6
    ) / LOOP_FACTOR**2
    return (*gauge, beta_yt_2, 0.0, 0.5 * beta_lambda_std_2)


def _qcd_beta_g3(g3: float, *, active_quarks: int = 6, loops: int = 4) -> float:
    """Pure-QCD beta control through four loops for g3."""

    nf = int(active_quarks)
    if nf < 3 or nf > 6 or loops < 1 or loops > 4:
        raise PhysicalMatchingError("QCD control requires 3<=active_quarks<=6 and 1<=loops<=4")
    zeta3 = 1.202056903159594
    coefficients = [
        11.0 - 2.0 / 3.0 * nf,
        102.0 - 38.0 / 3.0 * nf,
        2857.0 / 2.0 - 5033.0 / 18.0 * nf + 325.0 / 54.0 * nf**2,
        149753.0 / 6.0 + 3564.0 * zeta3
        - (1078361.0 / 162.0 + 6508.0 / 27.0 * zeta3) * nf
        + (50065.0 / 162.0 + 6472.0 / 81.0 * zeta3) * nf**2
        + 1093.0 / 729.0 * nf**3,
    ]
    a = g3**2 / LOOP_FACTOR
    polynomial = sum(coefficients[index] * a**index for index in range(loops))
    return -g3**3 / LOOP_FACTOR * polynomial


def _top_pole_qcd_four_loop(m_running: float, g3: float, scale_gev: float) -> tuple[float, float]:
    """Run the top mass to its own scale and apply the four-loop QCD relation."""

    mass = abs(float(m_running))
    if mass <= 1e-12 or not math.isfinite(mass):
        return mass, mass
    current_g3 = float(g3)
    current_mass = mass
    target_t = math.log(mass / scale_gev) if scale_gev > 0.0 else 0.0
    count = max(1, int(math.ceil(abs(target_t) * 32.0)))
    step = target_t / count
    for _ in range(count):
        def beta(pair: tuple[float, float]) -> tuple[float, float]:
            qg = _qcd_beta_g3(pair[0], active_quarks=6, loops=4)
            qm = -8.0 * pair[0] ** 2 * pair[1] / LOOP_FACTOR
            return qg, qm

        state = (current_g3, current_mass)
        k1 = beta(state)
        k2 = beta((state[0] + step * k1[0] / 2.0, state[1] + step * k1[1] / 2.0))
        k3 = beta((state[0] + step * k2[0] / 2.0, state[1] + step * k2[1] / 2.0))
        k4 = beta((state[0] + step * k3[0], state[1] + step * k3[1]))
        current_g3 = state[0] + step * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]) / 6.0
        current_mass = state[1] + step * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]) / 6.0
    alpha_s = current_g3**2 / (4.0 * math.pi)
    ratio = (
        1.0
        + 0.4244 * alpha_s
        + 0.8345 * alpha_s**2
        + 2.375 * alpha_s**3
        + 8.49 * alpha_s**4
    )
    return current_mass, current_mass * ratio


def sm_matching_beta(
    state: Sequence[float],
    *,
    loop_mode: str,
    scale_gev: float,
    thresholds: ThresholdSchedule,
) -> tuple[float, ...]:
    """Matter beta vector with declared threshold gates.

    ``two-loop-gauge-control`` adds the standard two-loop gauge terms while
    retaining the W11 one-loop Yukawa and quartic equations.  The threshold
    gate is a controlled leading step-function approximation: below the
    electroweak threshold the SM fields are frozen rather than replaced by a
    full QED+QCD EFT.  Such low-scale points are therefore diagnostic only.
    """

    values = _matter_state(state)
    if loop_mode not in DEFAULT_LOOP_MODES:
        raise PhysicalMatchingError(f"unknown loop mode: {loop_mode}")
    if scale_gev <= 0.0 or not math.isfinite(scale_gev):
        raise PhysicalMatchingError("scale must be positive and finite")

    # Below electroweak symmetry-breaking scales a complete EFT matching is
    # required.  Freeze the SM dimensionless state in this control rather than
    # pretending that the unbroken-SM beta functions remain valid.
    if thresholds.electroweak_gev is not None and scale_gev < thresholds.electroweak_gev:
        return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    effective = list(values)
    top_decoupled = thresholds.top_gev is not None and scale_gev < thresholds.top_gev
    higgs_decoupled = thresholds.higgs_gev is not None and scale_gev < thresholds.higgs_gev
    if top_decoupled:
        effective[3] = 0.0
    one_loop = list(beta_matter(effective, G_N=0.0, Lambda=0.0))
    if loop_mode == "two-loop-gauge-control":
        corrections = _two_loop_gauge_correction(effective)
        for index, correction in enumerate(corrections):
            one_loop[index] += correction
    elif loop_mode == "two-loop-sm-top-dominance":
        corrections = _two_loop_sm_top_dominance_correction(effective)
        for index, correction in enumerate(corrections):
            one_loop[index] += correction

    if thresholds.top_gev is not None and scale_gev < thresholds.top_gev:
        one_loop[3] = 0.0
    if thresholds.higgs_gev is not None and scale_gev < thresholds.higgs_gev:
        one_loop[5] = 0.0
    return tuple(one_loop)


def _rk4_scale_step(state: tuple[float, ...], start_t: float, step: float, beta) -> tuple[float, ...]:
    def shifted(base: tuple[float, ...], direction: tuple[float, ...], scale: float) -> tuple[float, ...]:
        return tuple(base[index] + scale * direction[index] for index in range(len(base)))

    k1 = beta(start_t, state)
    k2 = beta(start_t + step / 2.0, shifted(state, k1, step / 2.0))
    k3 = beta(start_t + step / 2.0, shifted(state, k2, step / 2.0))
    k4 = beta(start_t + step, shifted(state, k3, step))
    return tuple(
        state[index] + step * (k1[index] + 2.0 * k2[index] + 2.0 * k3[index] + k4[index]) / 6.0
        for index in range(len(state))
    )


def _integrate_matter(
    state: Sequence[float],
    start_t: float,
    end_t: float,
    *,
    loop_mode: str,
    thresholds: ThresholdSchedule,
    steps_per_unit: int,
) -> tuple[str, tuple[float, ...], str | None, list[dict[str, Any]]]:
    current = _matter_state(state)
    count = max(1, int(math.ceil(abs(end_t - start_t) * steps_per_unit)))
    step = (end_t - start_t) / count
    points: list[dict[str, Any]] = []
    t = start_t
    try:
        for _ in range(count):
            scale = REDUCED_PLANCK_SCALE_GEV * math.exp(t)
            current = _rk4_scale_step(
                current,
                t,
                step,
                lambda local_t, local_state: sm_matching_beta(
                    local_state,
                    loop_mode=loop_mode,
                    scale_gev=REDUCED_PLANCK_SCALE_GEV * math.exp(local_t),
                    thresholds=thresholds,
                ),
            )
            t += step
            if any(not math.isfinite(value) or abs(value) > MAX_STATE_BOUND for value in current):
                return "BOUND_REACHED", current, "finite-state bound reached", points
            if len(points) < 4 or _ == count - 1:
                points.append({"log_scale": t, "scale_gev": scale, "state": list(current)})
    except (ArithmeticError, PhysicalMatchingError, ValueError) as exc:
        return "NUMERICAL_FAILURE", current, str(exc), points
    return "COMPLETE", current, None, points


def _mass_observables(state: Sequence[float], *, scale_gev: float) -> dict[str, Any]:
    g1, g2, g3, yt, _yb, lam4 = _matter_state(state)
    v = ELECTROWEAK_VEV_GEV
    top_running = abs(yt) * v / math.sqrt(2.0)
    higgs_running = math.sqrt(2.0 * lam4) * v if lam4 >= 0.0 else None
    alpha_s = g3**2 / (4.0 * math.pi)
    top_running_at_mt, top_pole = _top_pole_qcd_four_loop(top_running, g3, scale_gev)
    g_y = math.sqrt(3.0 / 5.0) * g1
    e = abs(g_y * g2) / math.sqrt(g_y**2 + g2**2) if g_y**2 + g2**2 > 0.0 else 0.0
    return {
        "evaluation_scale_gev": scale_gev,
        "top_running_gev": top_running,
        "top_running_at_mt_qcd_control_gev": top_running_at_mt,
        "top_pole_qcd_four_loop_control_gev": top_pole,
        "top_pole_one_loop_qcd_gev": top_pole,
        "higgs_running_tree_control_gev": 2.0 * math.sqrt(max(lam4, 0.0)) * v if lam4 >= 0.0 else None,
        "alpha_s": alpha_s,
        "alpha_em_at_evaluation_scale": e**2 / (4.0 * math.pi),
        "conversion_scope": "top four-loop pure-QCD control; Higgs tree-level only",
        "higgs_pole_two_loop_status": "EXTERNAL_SMDR_REQUIRED",
    }


def _initializations(include_neighborhood: bool) -> list[dict[str, Any]]:
    gravities = _gravity_initializations()
    result: list[dict[str, Any]] = []
    for gravity in gravities:
        result.extend(_fixed_point_branch_initializations(gravity))
    if include_neighborhood:
        root = next(item for item in gravities if item["id"] == "printed-equation-root")
        result.extend(_source_neighborhood_initializations(gravity_state=root["state"]))
    return result


def _compare_at_end(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Apply an external comparison only after all trajectories are complete."""

    observed = {
        "top_pole_gev": {"value": 172.56, "uncertainty": 0.31, "source": "PDG 2025 top review"},
        "higgs_mass_gev": {"value": 125.20, "uncertainty": 0.11, "source": "PDG 2025 Higgs listing"},
    }
    comparisons: list[dict[str, Any]] = []
    for case in cases:
        observables = case.get("electroweak_observables") or {}
        top = observables.get("top_pole_one_loop_qcd_gev")
        higgs = observables.get("higgs_running_tree_control_gev")
        comparisons.append(
            {
                "case_id": case["case_id"],
                "top_pull_using_control_conversion": None if top is None else (top - observed["top_pole_gev"]["value"]) / observed["top_pole_gev"]["uncertainty"],
                "higgs_pull_using_tree_control": None if higgs is None else (higgs - observed["higgs_mass_gev"]["value"]) / observed["higgs_mass_gev"]["uncertainty"],
            }
        )
    return {
        "performed_after_generation": True,
        "used_for_fit": False,
        "used_for_selection": False,
        "observed_inputs": observed,
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "interpretation": "Descriptive comparison only; the implemented conversions are not NNLO precision relations.",
    }


def run_physical_matching_campaign(
    *,
    transition_offsets: Sequence[float] = DEFAULT_GRAVITY_TRANSITION_OFFSETS,
    loop_modes: Sequence[str] = DEFAULT_LOOP_MODES,
    threshold_schedules: Sequence[Mapping[str, Any]] = DEFAULT_THRESHOLD_SCHEDULES,
    include_neighborhood: bool = False,
    compare_experiment: bool = True,
    steps_per_unit: int = DEFAULT_STEPS_PER_UNIT,
) -> dict[str, Any]:
    """Run every declared matching configuration and retain every outcome."""

    if steps_per_unit < 1 or steps_per_unit > 64:
        raise PhysicalMatchingError("steps_per_unit must be in [1, 64]")
    transitions = tuple(float(value) for value in transition_offsets)
    schedules = tuple(_schedule(item) for item in threshold_schedules)
    initializations = _initializations(include_neighborhood)
    cases: list[dict[str, Any]] = []

    t_ew = math.log(ELECTROWEAK_VEV_GEV / REDUCED_PLANCK_SCALE_GEV)
    t_low = math.log(LOW_SCALE_PROBE_GEV / REDUCED_PLANCK_SCALE_GEV)
    for initialization, transition, loop_mode, threshold in itertools.product(
        initializations, transitions, loop_modes, schedules
    ):
        case_id = f"{initialization['id']}|transition={transition:g}|loop={loop_mode}|threshold={threshold.identifier}"
        full_state = tuple(float(value) for value in initialization["state"])
        gravity_status, at_transition, gravity_error = _integrate_segment(
            full_state,
            0.0,
            transition,
            beta_full,
            steps_per_unit=steps_per_unit,
        )
        case: dict[str, Any] = {
            "case_id": case_id,
            "initialization_id": initialization["id"],
            "transition_offset": transition,
            "transition_scale_gev": REDUCED_PLANCK_SCALE_GEV * math.exp(transition),
            "loop_mode": loop_mode,
            "threshold_schedule": threshold.__dict__,
            "initial_state": list(full_state),
            "status": gravity_status,
            "error": gravity_error,
            "ew_state": None,
            "low_probe_state": None,
            "electroweak_observables": None,
            "low_probe_status": None,
        }
        if gravity_status != "COMPLETE":
            cases.append(case)
            continue
        ew_status, ew_state, ew_error, ew_points = _integrate_matter(
            at_transition[2:],
            transition,
            t_ew,
            loop_mode=loop_mode,
            thresholds=threshold,
            steps_per_unit=steps_per_unit,
        )
        case["status"] = ew_status
        case["error"] = ew_error
        case["ew_state"] = list(ew_state)
        case["ew_points"] = ew_points
        if ew_status != "COMPLETE":
            cases.append(case)
            continue
        case["electroweak_observables"] = _mass_observables(ew_state, scale_gev=ELECTROWEAK_VEV_GEV)
        low_status, low_state, low_error, low_points = _integrate_matter(
            ew_state,
            t_ew,
            t_low,
            loop_mode=loop_mode,
            thresholds=threshold,
            steps_per_unit=steps_per_unit,
        )
        case["low_probe_status"] = low_status
        case["low_probe_error"] = low_error
        case["low_probe_state"] = list(low_state)
        case["low_probe_points"] = low_points
        cases.append(case)

    status_counts: dict[str, int] = {}
    low_status_counts: dict[str, int] = {}
    for case in cases:
        status_counts[case["status"]] = status_counts.get(case["status"], 0) + 1
        if case["low_probe_status"] is not None:
            low_status_counts[case["low_probe_status"]] = low_status_counts.get(case["low_probe_status"], 0) + 1

    comparison = _compare_at_end(cases) if compare_experiment else {
        "performed_after_generation": False,
        "used_for_fit": False,
        "used_for_selection": False,
    }
    complete = [case for case in cases if case["status"] == "COMPLETE"]
    return {
        "matching_version": PHYSICAL_MATCHING_VERSION,
        "campaign_id": "eichhorn-held-physical-matching",
        "execution_status": "COMPLETE" if len(complete) == len(cases) else "PARTIAL_FAILURES_RETAINED",
        "scope": {
            "uv_scale_gev": REDUCED_PLANCK_SCALE_GEV,
            "electroweak_matching_scale_gev": ELECTROWEAK_VEV_GEV,
            "low_scale_probe_gev": LOW_SCALE_PROBE_GEV,
            "gravity_system": "corrected Eichhorn--Held Einstein--Hilbert truncation",
            "sm_loop_control": "one-loop W11, two-loop gauge, and two-loop top-dominance controls",
            "two_loop_top_dominance": "IMPLEMENTED_WITH_LAMBDA4_CONVENTION_MAP",
            "full_sm_two_loop": "NOT_IMPLEMENTED; bottom/tau/light-family terms require the complete matrix system",
            "full_sm_nnlo": "NOT_IMPLEMENTED",
            "thresholds": "pre-registered step-function sensitivity controls; full EFT matching NOT_IMPLEMENTED",
            "pole_conversion": "top four-loop pure-QCD control and Higgs tree-level control",
            "regulator_uncertainty": "represented by declared transition and threshold ensemble; regulator-shape family not implemented",
            "truncation_uncertainty": "one-loop versus two-loop-gauge-control spread",
            "external_precision_backend": {
                "name": "SMDR",
                "status": "REQUIRED_FOR_FULL_EFT_AND_HIGGS_POLE_MATCHING",
                "not_invoked": True,
            },
        },
        "inputs": {
            "transition_offsets": list(transitions),
            "loop_modes": list(loop_modes),
            "threshold_schedules": [schedule.__dict__ for schedule in schedules],
            "initialization_count": len(initializations),
            "include_source_neighborhood": include_neighborhood,
            "steps_per_unit": steps_per_unit,
            "dimensionful_inputs_are_calibration_inputs": True,
            "experimental_targets_used_before_comparison": False,
        },
        "scan": {
            "case_count": len(cases),
            "status_counts": status_counts,
            "low_probe_status_counts": low_status_counts,
            "complete_count": len(complete),
        },
        "cases": cases,
        "experimental_comparison": comparison,
        "controls": {
            "all_declared_variants_executed": True,
            "all_negative_results_retained": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "comparison_last": True,
            "comparison_not_used_for_fit": True,
            "comparison_not_used_for_selection": True,
            "full_sm_two_loop_not_claimed": True,
            "two_loop_top_dominance_implemented": True,
            "full_sm_nnlo_not_claimed": True,
            "nnlo_pole_conversion_not_claimed": True,
            "regulator_shape_uncertainty_not_claimed": True,
            "low_scale_probe_is_diagnostic_only": True,
        },
        "conclusions": {
            "dimensionful_flow_executed": True,
            "gravity_decoupling_executed": True,
            "threshold_sensitivity_executed": True,
            "two_loop_gauge_control_executed": True,
            "two_loop_top_dominance_control_executed": True,
            "physical_sm_matching_completed": False,
            "reason": "A complete SM two-loop/NNLO threshold and pole-mass matching layer is not implemented; the report records the controlled partial result and the missing gates.",
        },
        "bibliography": [
            {
                "id": "eichhorn-held-2018",
                "citation": "A. Eichhorn and A. Held, Top mass from asymptotic safety, Phys. Lett. B 777 (2018) 217--221.",
                "doi": "10.1016/j.physletb.2017.12.040",
                "role": "UV truncation and matching setup.",
            },
            {
                "id": "degrassi-et-al-2012",
                "citation": "G. Degrassi et al., Higgs mass and vacuum stability in the Standard Model at NNLO, JHEP 08 (2012) 098.",
                "doi": "10.1007/JHEP08(2012)098",
                "role": "NNLO running and threshold precision requirement.",
            },
            {
                "id": "luo-xiao-2003",
                "citation": "M. Luo and Y. Xiao, Two-loop Renormalization Group Equations in the Standard Model, Phys. Rev. Lett. 90 (2003) 011601.",
                "doi": "10.1103/PhysRevLett.90.011601",
                "role": "Two-loop SM beta-function control.",
            },
            {
                "id": "buttazzo-et-al-2013",
                "citation": "D. Buttazzo et al., Investigating the near-criticality of the Higgs boson, JHEP 12 (2013) 089.",
                "doi": "10.1007/JHEP12(2013)089",
                "role": "Explicit two-loop top/Higgs beta polynomials and precision matching context.",
            },
            {
                "id": "martin-robertson-2019",
                "citation": "S. P. Martin and D. G. Robertson, Standard Model parameters in the tadpole-free pure MSbar scheme, Phys. Rev. D 100 (2019) 073004.",
                "doi": "10.1103/PhysRevD.100.073004",
                "role": "Authoritative external SMDR implementation for full pole and decoupling matching.",
            },
            {
                "id": "pdg-2025-top",
                "citation": "Particle Data Group, Review of Particle Physics 2025, Top Quark review.",
                "url": "https://pdg.lbl.gov/2025/reviews/rpp2025-rev-top-quark.pdf",
                "role": "Late comparison reference and pole/MS scheme caveats.",
            },
            {
                "id": "pdg-2025-higgs",
                "citation": "Particle Data Group, Review of Particle Physics 2025, Higgs listing.",
                "url": "https://pdg.lbl.gov/2025/web/viewer.html?file=..%2Flistings%2Frpp2025-list-higgs-boson.pdf",
                "role": "Late comparison reference.",
            },
        ],
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "next_gate": "IMPLEMENT_FULL_TWO_LOOP_SM_AND_NNLO_THRESHOLD_POLE_MATCHING_BEFORE_PHENOMENOLOGICAL_CLAIM",
    }


def write_physical_matching_report(path: str | Path, report: Mapping[str, Any], *, gzip_full: bool = False) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(report), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if gzip_full or output.suffix == ".gz":
        with gzip.open(output, "wt", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        output.write_text(payload, encoding="utf-8")
    return output


__all__ = [
    "DEFAULT_GRAVITY_TRANSITION_OFFSETS",
    "DEFAULT_LOOP_MODES",
    "DEFAULT_STEPS_PER_UNIT",
    "DEFAULT_THRESHOLD_SCHEDULES",
    "ELECTROWEAK_VEV_GEV",
    "LOW_SCALE_PROBE_GEV",
    "PHYSICAL_MATCHING_VERSION",
    "PhysicalMatchingError",
    "ThresholdSchedule",
    "run_physical_matching_campaign",
    "sm_matching_beta",
    "write_physical_matching_report",
]
