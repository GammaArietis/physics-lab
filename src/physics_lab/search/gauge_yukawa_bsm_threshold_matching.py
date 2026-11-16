"""W17 one-loop BSM threshold matching control.

This module adds the first explicit BSM threshold layer to W16.  It uses the
W15 piecewise vector-like thresholds and the Z2-even real-singlet Higgs portal
to construct a target-blind low-energy MSbar projection before calling SMDR.

The gauge decoupling term is the one-loop logarithmic matching implied by the
heavy-field contribution to the gauge beta coefficient.  For the unbroken
Z2 singlet, the one-loop effective-potential threshold shifts the Higgs
quartic by the portal-squared logarithm.  The calculation is intentionally
not labelled a full BSM pole calculation: wave-function, vertex and complete
new-sector self-energy terms are not supplied to the pure-SM SMDR executable.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from physics_lab.search.gauge_yukawa_smdr_matching import (
    SMDR_KNOWN_COMMIT,
    SMDR_MATCHING_VERSION,
    SMDR_OFFICIAL_REPOSITORY,
    SMDRMatchingError,
    _backend_commit,
    _binary_sha256,
    w15_state_to_smdr_input,
)
from physics_lab.search.gauge_yukawa_vectorlike_extension import LOOP_FACTOR, MULTIPLETS
from physics_lab.search.smdr_backend import (
    ELECTROWEAK_VEV_GEV,
    SMDR_BRIDGE_VERSION,
    SMDRBackendError,
    run_smdr_calc_all,
)


BSM_THRESHOLD_MATCHING_VERSION = "gauge-yukawa-bsm-threshold-matching-v1"
DEFAULT_SINGLET_MASS_GRID_GEV = (1.0e3, 1.0e5, 1.0e8)


class BSMThresholdMatchingError(ValueError):
    """Raised for malformed threshold matching inputs."""


def _finite(value: Any, name: str, *, positive: bool = False) -> float:
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0.0):
        requirement = "finite and positive" if positive else "finite"
        raise BSMThresholdMatchingError(f"{name} must be {requirement}")
    return result


def w15_threshold_events(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract heavy vector-like decoupling events from W15 segments."""

    segments = candidate.get("segments", [])
    if not isinstance(segments, list):
        raise BSMThresholdMatchingError("W15 segments must be a list")
    events: list[dict[str, Any]] = []
    for index in range(len(segments) - 1):
        upper = segments[index]
        lower = segments[index + 1]
        upper_active = dict(upper.get("active_multiplicities", {}))
        lower_active = dict(lower.get("active_multiplicities", {}))
        mass = _finite(upper.get("low_scale_gev"), f"segments[{index}].low_scale_gev", positive=True)
        for name, count_above in upper_active.items():
            count_below = int(lower_active.get(name, 0))
            count = int(count_above) - count_below
            if count > 0:
                if name not in MULTIPLETS:
                    raise BSMThresholdMatchingError(f"unknown vector-like multiplet in W15 segments: {name}")
                events.append(
                    {
                        "multiplet": name,
                        "multiplicity_decoupled": count,
                        "mass_gev": mass,
                        "source_segment_index": index,
                    }
                )
    return events


def vectorlike_threshold_delta_b(events: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Return the heavy-field Δb_i entering one-loop gauge decoupling."""

    result = {"g1": 0.0, "g2": 0.0, "g3": 0.0}
    for event in events:
        name = str(event["multiplet"])
        count = int(event["multiplicity_decoupled"])
        if name not in MULTIPLETS or count < 1:
            raise BSMThresholdMatchingError("invalid vector-like threshold event")
        delta = MULTIPLETS[name].gauge_b_delta(count)
        for key in result:
            result[key] += float(delta[key])
    return result


def apply_one_loop_bsm_thresholds(
    state: Sequence[float],
    candidate: Mapping[str, Any],
    *,
    matching_scale_gev: float,
    singlet_mass_gev: float,
) -> tuple[list[float], dict[str, Any]]:
    r"""Apply explicit one-loop logarithmic gauge and portal thresholds.

    The state is the W15 EFT IR state.  Canonical \(\overline{MS}\) matching
    is performed at each heavy mass, so the one-loop logarithm is evaluated
    at ``mu=M`` for each vector-like field.  For the unbroken singlet portal
    the analogous canonical scale is ``mu=m_S``.  Both logarithms therefore
    vanish in this specific scheme; recording that zero is important because
    applying the same logarithms again at the IR endpoint would double-count
    the W15 piecewise running.

    The generic decoupling relation is

    ``1/g_i^2 -> 1/g_i^2 + Δb_i/(16π²) log(μ²/M²)``.

    For the W15 convention ``V ⊃ λ_h(H†H)^2 + λ_hs S²H†H`` and an unbroken
    Z2 singlet, the one-loop portal contribution is

    ``λ_h -> λ_h + λ_hs²/(16π²) log(m_S²/μ²)``.

    These are leading-log one-loop matching controls; complete finite BSM
    self-energy and wave-function corrections remain outside SMDR.
    """

    if len(state) != 8:
        raise BSMThresholdMatchingError("W15 state must contain eight couplings")
    values = [_finite(value, f"state[{index}]") for index, value in enumerate(state)]
    matching_scale = _finite(matching_scale_gev, "matching_scale_gev", positive=True)
    singlet_mass = _finite(singlet_mass_gev, "singlet_mass_gev", positive=True)
    events = w15_threshold_events(candidate)
    delta_b = vectorlike_threshold_delta_b(events)
    gauge_logs: list[dict[str, Any]] = []
    for index, key in enumerate(("g1", "g2", "g3")):
        coupling = values[index]
        # The vector-like event logs are evaluated at each event's canonical
        # matching scale M.  W15 already contains the running below M, so
        # evaluating these logs at the IR endpoint would double-count it.
        delta_inverse = 0.0
        event_terms = []
        for event in events:
            mass = float(event["mass_gev"])
            contribution = MULTIPLETS[str(event["multiplet"])].gauge_b_delta(int(event["multiplicity_decoupled"]))[key]
            term = float(contribution) / LOOP_FACTOR * math.log((mass / mass) ** 2)
            delta_inverse += term
            event_terms.append({"mass_gev": mass, "matching_scale_gev": mass, "delta_b": float(contribution), "delta_inverse_g2": term})
        if abs(coupling) <= 1.0e-14:
            values[index] = 0.0
            transformed = "ZERO_PROTECTED"
        else:
            inverse_squared = 1.0 / coupling**2 + delta_inverse
            if inverse_squared <= 0.0:
                raise BSMThresholdMatchingError(f"non-positive matched inverse coupling for {key}")
            values[index] = math.copysign(1.0 / math.sqrt(inverse_squared), coupling)
            transformed = "INVERSE_SQUARED_MATCHED"
        gauge_logs.append(
            {
                "coupling": key,
                "delta_b_total": float(delta_b[key]),
                "delta_inverse_g2": delta_inverse,
                "event_terms": event_terms,
                "transformation": transformed,
            }
        )
    portal = values[7]
    portal_shift = portal**2 / LOOP_FACTOR * math.log((singlet_mass / singlet_mass) ** 2)
    values[5] += portal_shift
    metadata = {
        "matching_scale_gev": matching_scale,
        "singlet_mass_gev": singlet_mass,
        "canonical_threshold_matching_scales": True,
        "low_scale_endpoint_logs_reapplied": False,
        "vectorlike_threshold_events": events,
        "vectorlike_delta_b": delta_b,
        "gauge_matching": gauge_logs,
        "portal_convention": "V contains lambda_h*(H^dagger H)^2 + lambda_hs*S^2*H^dagger H",
        "higgs_quartic_shift": portal_shift,
        "top_yukawa_shift": 0.0,
        "top_yukawa_shift_reason": "zero at this order for the registered Z2 singlet plus Psi-only Yukawa action",
        "finite_matching_order": "one-loop logarithmic control at canonical MSbar thresholds",
        "complete_bsm_self_energies_included": False,
        "experimental_data_used": False,
    }
    return values, metadata


def _run_case(
    candidate: Mapping[str, Any],
    *,
    smdr_root: Path,
    matching_scale_gev: float,
    singlet_mass_gev: float,
    timeout_seconds: int,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "unnamed"))
    case_id = f"{candidate_id}|singlet-mass={singlet_mass_gev:g}"
    w15_status = str(candidate.get("status", "UNKNOWN"))
    if w15_status not in {"COMPLETE", "ZERO_PROTECTED"} or not isinstance(candidate.get("final_state"), list):
        return {"case_id": case_id, "candidate_id": candidate_id, "status": "NOT_ELIGIBLE", "w15_status": w15_status, "target_blind_input": True}
    try:
        corrected, matching = apply_one_loop_bsm_thresholds(
            candidate["final_state"],
            candidate,
            matching_scale_gev=matching_scale_gev,
            singlet_mass_gev=singlet_mass_gev,
        )
        projected = dict(candidate)
        projected["final_state"] = corrected
        input_text, mapping = w15_state_to_smdr_input(
            corrected,
            scale_gev=matching_scale_gev,
            candidate=projected,
        )
        backend = run_smdr_calc_all(smdr_root, input_text=input_text, timeout_seconds=timeout_seconds)
    except (SMDRBackendError, SMDRMatchingError, BSMThresholdMatchingError) as exc:
        return {
            "case_id": case_id,
            "candidate_id": candidate_id,
            "w15_status": w15_status,
            "status": "BACKEND_FAILURE" if isinstance(exc, SMDRBackendError) else "MATCHING_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "target_blind_input": True,
            "pole_comparison": "NOT_AUTHORIZED",
            "matching": matching if "matching" in locals() else None,
        }
    return {
        "case_id": case_id,
        "candidate_id": candidate_id,
        "w15_status": w15_status,
        "status": "SMDR_COMPLETE",
        "target_blind_input": True,
        "pole_comparison": "NOT_AUTHORIZED",
        "w15_state": list(candidate["final_state"]),
        "matched_state": corrected,
        "matching": matching,
        "mapping": mapping,
        "backend": {
            "bridge_version": SMDR_BRIDGE_VERSION,
            "parsed": backend["parsed"],
            "input_sha256": backend.get("input_sha256"),
            "stderr": backend.get("stderr", ""),
        },
    }


def run_bsm_threshold_matching_campaign(
    precision_report: Mapping[str, Any],
    *,
    smdr_root: str | Path,
    singlet_mass_grid_gev: Sequence[float] = DEFAULT_SINGLET_MASS_GRID_GEV,
    timeout_seconds: int = 120,
    matching_scale_gev: float | None = None,
) -> dict[str, Any]:
    """Run all W15 candidates across the declared singlet-mass grid."""

    candidates = precision_report.get("candidate_results")
    if not isinstance(candidates, list) or not candidates:
        raise BSMThresholdMatchingError("precision report requires candidate_results")
    masses = [_finite(value, f"singlet_mass_grid_gev[{index}]", positive=True) for index, value in enumerate(singlet_mass_grid_gev)]
    if not masses:
        raise BSMThresholdMatchingError("singlet mass grid must not be empty")
    scale = float(matching_scale_gev if matching_scale_gev is not None else precision_report.get("scope", {}).get("ir_scale_gev", 91.1876))
    root = Path(smdr_root).expanduser().resolve()
    results = [
        _run_case(
            candidate,
            smdr_root=root,
            matching_scale_gev=scale,
            singlet_mass_gev=mass,
            timeout_seconds=timeout_seconds,
        )
        for candidate in candidates
        for mass in masses
    ]
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    source_json = json.dumps(precision_report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "campaign_id": "w17-gauge-yukawa-bsm-threshold-matching-2026-11-16",
        "matching_version": BSM_THRESHOLD_MATCHING_VERSION,
        "execution_status": "COMPLETE",
        "source": {
            "w15_pipeline_version": precision_report.get("pipeline_version"),
            "w15_candidate_count": len(candidates),
            "singlet_mass_grid_gev": masses,
            "case_count": len(results),
            "w15_report_sha256_canonical_json": hashlib.sha256(source_json).hexdigest(),
        },
        "backend": {
            "name": "SMDR pure-SM projection after BSM threshold control",
            "official_repository": SMDR_OFFICIAL_REPOSITORY,
            "known_reference_commit": SMDR_KNOWN_COMMIT,
            "resolved_commit": _backend_commit(root),
            "calc_all_sha256": _binary_sha256(root),
            "matching_scale_gev": scale,
            "timeout_seconds": int(timeout_seconds),
        },
        "scope": {
            "gauge_threshold_order": "one-loop logarithmic MSbar decoupling",
            "portal_threshold_order": "one-loop effective-potential logarithmic control",
            "complete_bsm_self_energies": False,
            "pure_smdr_projection_after_thresholds": True,
            "experimental_comparison": "NOT_AUTHORIZED",
        },
        "scan": {"case_count": len(results), "status_counts": counts},
        "controls": {
            "all_w15_candidates_retained": True,
            "all_singlet_mass_hypotheses_retained": True,
            "candidate_order_preserved": True,
            "target_blind_generation": True,
            "one_loop_gauge_decoupling_applied": True,
            "one_loop_portal_quartic_control_applied": True,
            "new_sector_self_energy_completion_claimed": False,
            "no_experimental_comparison": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
        },
        "candidate_results": results,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
        "interpretation": (
            "W17 applies explicit one-loop BSM threshold controls to every W15 IR state and "
            "projects the corrected SM sector through pure-SM SMDR. It is not a complete "
            "BSM pole calculation because new-sector wave-function, vertex and self-energy "
            "terms remain outside the SMDR executable."
        ),
    }


def write_bsm_threshold_matching_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


__all__ = [
    "BSM_THRESHOLD_MATCHING_VERSION",
    "DEFAULT_SINGLET_MASS_GRID_GEV",
    "BSMThresholdMatchingError",
    "apply_one_loop_bsm_thresholds",
    "run_bsm_threshold_matching_campaign",
    "vectorlike_threshold_delta_b",
    "w15_threshold_events",
    "write_bsm_threshold_matching_report",
]
