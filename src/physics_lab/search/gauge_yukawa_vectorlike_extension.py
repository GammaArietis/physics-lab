"""A bounded, target-blind SM gauge--Yukawa IR/EFT extension.

This module is deliberately more modest than a full two-loop precision
calculation.  It makes one concrete action explicit, derives the one-loop
gauge coefficients from representation data, integrates a reduced
gauge--Yukawa--scalar system, and exposes the resulting IR observables.

The new matter is vector-like, so gauge anomalies cancel representation by
representation.  The scalar is a real Z2-even singlet and couples to one
vector-like Dirac multiplet through a Yukawa interaction and to the Higgs
through a portal.  Exact zero gauge couplings remain invariant under this
perturbative flow; the extension therefore tests a physical EFT branch but
does not pretend to repair the degenerate W11 states by hand.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.integrate import solve_ivp


GAUGE_YUKAWA_EXTENSION_VERSION = "gauge-yukawa-vectorlike-extension-v1"
LOOP_FACTOR = 16.0 * math.pi**2
PERTURBATIVE_BOUND = 4.0 * math.pi
ZERO_TOLERANCE = 1.0e-14
DEFAULT_UV_SCALE_GEV = 1.0e16
DEFAULT_IR_SCALE_GEV = 91.1876
REFERENCE_ALPHA_ZERO = 1.0 / 137.035999177

# GUT-normalised SM convention: beta_g = b*g^3/(16*pi^2).
SM_GAUGE_B = {"g1": 41.0 / 10.0, "g2": -19.0 / 6.0, "g3": -7.0}


class GaugeYukawaExtensionError(ValueError):
    """Raised for malformed or non-finite extension inputs."""


@dataclass(frozen=True)
class VectorlikeMultiplet:
    """One Dirac multiplet, represented as a vector-like pair."""

    name: str
    color_dim: int
    weak_dim: int
    hypercharge: float
    su3_index: float
    su2_index: float
    casimir_su3: float
    casimir_su2: float
    casimir_u1: float

    def gauge_b_delta(self, multiplicity: int = 1) -> dict[str, float]:
        """Return the Dirac-pair contribution to the one-loop b_i."""

        if multiplicity < 0:
            raise GaugeYukawaExtensionError("multiplicity must be non-negative")
        return {
            "g1": (4.0 / 3.0) * (3.0 / 5.0) * self.hypercharge**2 * self.color_dim * self.weak_dim * multiplicity,
            "g2": (4.0 / 3.0) * self.su2_index * self.color_dim * multiplicity,
            "g3": (4.0 / 3.0) * self.su3_index * self.weak_dim * multiplicity,
        }


MULTIPLETS: dict[str, VectorlikeMultiplet] = {
    "Q": VectorlikeMultiplet("Q", 3, 2, 1.0 / 6.0, 0.5, 0.5, 4.0 / 3.0, 3.0 / 4.0, 1.0 / 60.0),
    "U": VectorlikeMultiplet("U", 3, 1, 2.0 / 3.0, 0.5, 0.0, 4.0 / 3.0, 0.0, 4.0 / 15.0),
    "D": VectorlikeMultiplet("D", 3, 1, -1.0 / 3.0, 0.5, 0.0, 4.0 / 3.0, 0.0, 1.0 / 15.0),
    "L": VectorlikeMultiplet("L", 1, 2, -1.0 / 2.0, 0.0, 0.5, 0.0, 3.0 / 4.0, 3.0 / 20.0),
    "E": VectorlikeMultiplet("E", 1, 1, -1.0, 0.0, 0.0, 0.0, 0.0, 3.0 / 5.0),
}


def _finite(value: Any, name: str, *, lower: float = -100.0, upper: float = 100.0) -> float:
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper:
        raise GaugeYukawaExtensionError(f"{name} must be finite and in [{lower}, {upper}]")
    return result


def _multiplicity_map(values: Mapping[str, Any]) -> dict[str, int]:
    result = {name: 0 for name in MULTIPLETS}
    for name, value in values.items():
        if name not in MULTIPLETS:
            raise GaugeYukawaExtensionError(f"unknown vector-like multiplet: {name}")
        integer = int(value)
        if integer != value or integer < 0 or integer > 8:
            raise GaugeYukawaExtensionError(f"invalid multiplicity for {name}")
        result[name] = integer
    return result


def gauge_coefficients(multiplicities: Mapping[str, Any]) -> dict[str, float]:
    """Derive b_i from SM fields plus explicit vector-like representations."""

    counts = _multiplicity_map(multiplicities)
    result = dict(SM_GAUGE_B)
    for name, count in counts.items():
        delta = MULTIPLETS[name].gauge_b_delta(count)
        for coupling in result:
            result[coupling] += delta[coupling]
    return result


def action_record(multiplicities: Mapping[str, Any], yukawa_multiplet: str) -> dict[str, Any]:
    counts = _multiplicity_map(multiplicities)
    if yukawa_multiplet not in MULTIPLETS:
        raise GaugeYukawaExtensionError("yukawa_multiplet must name a registered multiplet")
    if counts[yukawa_multiplet] < 1:
        raise GaugeYukawaExtensionError("the Yukawa multiplet must be present")
    return {
        "gauge_group": "SU(3)c x SU(2)L x U(1)Y",
        "new_fields": [
            {"field": "S", "spin": 0, "representation": "(1,1)_0", "reality": "real", "symmetry": "Z2-even"},
            *[
                {
                    "field": f"{name}_VL",
                    "spin": "1/2",
                    "representation": f"({MULTIPLETS[name].color_dim},{MULTIPLETS[name].weak_dim})_{MULTIPLETS[name].hypercharge:g}",
                    "multiplicity": count,
                    "vectorlike_pair": True,
                    "gauge_anomaly_cancelled_pairwise": True,
                }
                for name, count in counts.items()
                if count
            ],
        ],
        "lagrangian_terms": [
            "-1/4 F^a_mu_nu F^a_mu_nu",
            "i bar(Psi) slash(D) Psi - M_Psi bar(Psi) Psi",
            "1/2 (partial S)^2 - m_S^2 S^2/2 - lambda_S S^4/4",
            "- y_S S bar(Psi) Psi - lambda_HS S^2 H^dagger H",
        ],
        "z2_condition": "S -> -S, cubic S term omitted",
        "yukawa_multiplet": yukawa_multiplet,
        "normalisation": {"hypercharge": "GUT-normalised g1; gY=sqrt(3/5)*g1", "potential": "lambda_S*S^4/4"},
    }


def beta_state(
    log_scale: float,
    state: Sequence[float],
    *,
    multiplicities: Mapping[str, Any],
    yukawa_multiplet: str,
    top_yukawa: float = 0.0,
) -> tuple[float, ...]:
    """Reduced one-loop beta vector for (g1,g2,g3,yt,yS,lambdaH,lambdaS,lambdaHS).

    The gauge coefficients are derived exactly at one loop from the listed
    representations.  The scalar/Yukawa block is a declared reduced control,
    not a substitute for a two-loop MSbar matching calculation.
    """

    del log_scale
    if len(state) != 8:
        raise GaugeYukawaExtensionError("state must contain eight couplings")
    g1, g2, g3, yt, ys, lam_h, lam_s, lam_hs = tuple(float(value) for value in state)
    values = (g1, g2, g3, yt, ys, lam_h, lam_s, lam_hs)
    if not all(math.isfinite(value) for value in values):
        raise GaugeYukawaExtensionError("state contains a non-finite coupling")
    counts = _multiplicity_map(multiplicities)
    if counts.get(yukawa_multiplet, 0) < 1:
        raise GaugeYukawaExtensionError("Yukawa multiplet is absent")
    multiplet = MULTIPLETS[yukawa_multiplet]
    coefficients = gauge_coefficients(counts)
    gauge = tuple(coefficients[name] * coupling**3 / LOOP_FACTOR for name, coupling in (("g1", g1), ("g2", g2), ("g3", g3)))
    gauge_penalty = 6.0 * (multiplet.casimir_u1 * g1**2 + multiplet.casimir_su2 * g2**2 + multiplet.casimir_su3 * g3**2)
    beta_ys = ys * (3.0 * ys**2 - gauge_penalty) / LOOP_FACTOR
    beta_yt = yt * (
        9.0 / 2.0 * yt**2
        + 3.0 / 2.0 * float(top_yukawa) ** 2
        - 17.0 / 20.0 * g1**2
        - 9.0 / 4.0 * g2**2
        - 8.0 * g3**2
    ) / LOOP_FACTOR
    beta_lam_h = (
        24.0 * lam_h**2
        - 6.0 * yt**4
        + 12.0 * lam_h * yt**2
        - 9.0 * lam_h * g2**2
        - 9.0 / 5.0 * lam_h * g1**2
        + 3.0 / 8.0 * (2.0 * g2**4 + (g2**2 + 3.0 / 5.0 * g1**2) ** 2)
        + 0.5 * lam_hs**2
    ) / LOOP_FACTOR
    beta_lam_s = (18.0 * lam_s**2 + 2.0 * lam_hs**2 + 8.0 * lam_s * ys**2 - 8.0 * ys**4) / LOOP_FACTOR
    beta_lam_hs = lam_hs * (
        12.0 * lam_h + 6.0 * lam_s + 4.0 * ys**2 + 6.0 * yt**2 - 9.0 / 5.0 * g1**2 - 9.0 * g2**2
    ) / LOOP_FACTOR + 4.0 * lam_hs**2 / LOOP_FACTOR
    return (*gauge, beta_yt, beta_ys, beta_lam_h, beta_lam_s, beta_lam_hs)


def _observable_record(state: Sequence[float], scale_gev: float) -> dict[str, Any]:
    g1, g2, g3, yt, ys, lam_h, lam_s, lam_hs = (float(value) for value in state)
    gy = math.sqrt(3.0 / 5.0) * g1
    denominator = math.sqrt(gy**2 + g2**2)
    e = abs(gy * g2) / denominator if denominator else 0.0
    return {
        "scale_gev": float(scale_gev),
        "g1_gut": g1,
        "g2": g2,
        "g3": g3,
        "e": e,
        "alpha_em": e**2 / (4.0 * math.pi),
        "alpha_s": g3**2 / (4.0 * math.pi),
        "y_top_control": yt,
        "y_new_scalar": ys,
        "lambda_h": lam_h,
        "lambda_s": lam_s,
        "lambda_hs": lam_hs,
    }


def run_candidate(candidate: Mapping[str, Any], *, uv_scale_gev: float, ir_scale_gev: float) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id", "unnamed"))
    multiplicities = _multiplicity_map(candidate.get("multiplicities", {}))
    yukawa_multiplet = str(candidate.get("yukawa_multiplet", ""))
    action = action_record(multiplicities, yukawa_multiplet)
    initial = tuple(_finite(value, f"initial_state[{index}]", lower=-PERTURBATIVE_BOUND, upper=PERTURBATIVE_BOUND) for index, value in enumerate(candidate.get("initial_state", [])))
    if len(initial) != 8:
        raise GaugeYukawaExtensionError("initial_state must have eight entries")
    uv_scale = _finite(uv_scale_gev, "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir_scale = _finite(ir_scale_gev, "ir_scale_gev", lower=1.0, upper=1.0e100)
    if uv_scale <= ir_scale:
        raise GaugeYukawaExtensionError("uv_scale_gev must exceed ir_scale_gev")
    coefficients = gauge_coefficients(multiplicities)
    solution = solve_ivp(
        lambda t, y: beta_state(t, y, multiplicities=multiplicities, yukawa_multiplet=yukawa_multiplet),
        (math.log(uv_scale), math.log(ir_scale)),
        np.asarray(initial, dtype=float),
        rtol=1.0e-8,
        atol=1.0e-10,
        max_step=0.25,
    )
    if not solution.success or solution.y.size == 0:
        return {
            "candidate_id": candidate_id,
            "status": "INTEGRATION_FAILURE",
            "action": action,
            "gauge_coefficients": coefficients,
            "message": str(solution.message),
            "target_blind": True,
        }
    final_state = tuple(float(value) for value in solution.y[:, -1])
    max_abs = max(abs(value) for value in solution.y.flat)
    zero_protected = all(abs(value) <= ZERO_TOLERANCE for value in initial[:3]) and all(abs(value) <= ZERO_TOLERANCE for value in final_state[:3])
    status = "ZERO_PROTECTED" if zero_protected else ("NONPERTURBATIVE" if max_abs >= PERTURBATIVE_BOUND else "COMPLETE")
    return {
        "candidate_id": candidate_id,
        "status": status,
        "action": action,
        "gauge_coefficients": coefficients,
        "initial_state": list(initial),
        "final_state": list(final_state),
        "uv_observables": _observable_record(initial, uv_scale),
        "ir_observables": _observable_record(final_state, ir_scale),
        "integration": {
            "success": bool(solution.success),
            "steps": int(solution.t.size),
            "message": str(solution.message),
            "max_abs_coupling": max_abs,
        },
        "controls": {
            "vectorlike_anomaly_cancellation_explicit": True,
            "gauge_coefficients_derived_from_representations": True,
            "exact_zero_gauge_seed_inserted": False,
            "ir_boundary_condition_inserted": False,
            "target_blind_generation": True,
            "two_loop_precision_matching_claimed": False,
            "interacting_fixed_point_claimed": False,
        },
        "target_blind": True,
    }


def _late_comparison(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    complete = [item for item in results if item.get("status") in {"COMPLETE", "ZERO_PROTECTED"}]
    return {
        "performed_after_generation": True,
        "reference_alpha_zero": REFERENCE_ALPHA_ZERO,
        "used_for_fit": False,
        "used_for_selection": False,
        "automatic_ranking": False,
        "candidate_count": len(complete),
        "alpha_em_ir_values": [item.get("ir_observables", {}).get("alpha_em") for item in complete],
        "interpretation": "Descriptive late comparison only; no candidate is promoted and no parameter is adjusted.",
    }


def run_gauge_yukawa_campaign(activation: Mapping[str, Any]) -> dict[str, Any]:
    uv_scale = _finite(activation.get("uv_scale_gev", DEFAULT_UV_SCALE_GEV), "uv_scale_gev", lower=1.0, upper=1.0e100)
    ir_scale = _finite(activation.get("ir_scale_gev", DEFAULT_IR_SCALE_GEV), "ir_scale_gev", lower=1.0, upper=1.0e100)
    candidates = activation.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GaugeYukawaExtensionError("activation must contain a non-empty candidates list")
    results = [run_candidate(candidate, uv_scale_gev=uv_scale, ir_scale_gev=ir_scale) for candidate in candidates]
    status_counts: dict[str, int] = {}
    for result in results:
        status = str(result["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "campaign_id": str(activation.get("campaign_id", "gauge-yukawa-vectorlike-extension")),
        "extension_version": GAUGE_YUKAWA_EXTENSION_VERSION,
        "execution_status": "COMPLETE",
        "scope": {
            "uv_scale_gev": uv_scale,
            "ir_scale_gev": ir_scale,
            "model": "SM + real singlet S + anomaly-free vector-like Dirac multiplets",
            "loop_order": "one-loop reduced gauge-Yukawa-scalar control",
        },
        "scan": {"candidate_count": len(results), "status_counts": status_counts},
        "controls": {
            "all_candidates_retained": True,
            "target_blind_generation": True,
            "no_fitting": True,
            "no_automatic_selection": True,
            "no_automatic_ranking": True,
            "no_exact_zero_gauge_rescue_claimed": True,
            "no_two_loop_precision_matching_claimed": True,
            "no_interacting_fixed_point_claimed": True,
        },
        "literature_position": {
            "vectorlike_gauge_yukawa_asymptotic_safety": "known research direction",
            "this_campaign": "finite reduced EFT control and IR observable generator; not a publication-level full SM matching result",
        },
        "candidate_results": results,
        "late_comparison": _late_comparison(results),
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
    }


def write_campaign_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination

