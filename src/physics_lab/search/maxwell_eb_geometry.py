"""Target-blind Maxwell E/B geometry audit.

The module turns the user's geometric intuition into Lorentz/gauge-aware
quantities.  Field lines are visualisation aids; the invariant objects used
here are the two electromagnetic scalars and the Poynting direction.  A
separate late comparison checks whether any generated dimensionless ratio is
near the CODATA fine-structure constant, without ranking or promoting a
geometry.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


MAXWELL_EB_GEOMETRY_VERSION = "maxwell-eb-geometry-v1"
SPEED_OF_LIGHT = 299_792_458.0
CODATA_ALPHA_ZERO = 7.2973525643e-3


class MaxwellGeometryError(ValueError):
    """Raised for malformed geometry inputs."""


def _vector(values: Sequence[float], name: str) -> tuple[float, float, float]:
    if len(values) != 3:
        raise MaxwellGeometryError(f"{name} must contain three components")
    result = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in result):
        raise MaxwellGeometryError(f"{name} contains a non-finite component")
    return result  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Sequence[float]) -> float:
    return math.sqrt(_dot(a, a))


def evaluate_geometry(
    *,
    electric: Sequence[float],
    magnetic: Sequence[float],
    propagation: Sequence[float],
    support_length_m: float = 1.0,
) -> dict[str, Any]:
    """Evaluate invariant and wave-geometry diagnostics.

    The magnetic vector is expressed in SI tesla and the electric vector in
    SI volt/metre.  The combinations below are dimensionless and insensitive
    to a common amplitude rescaling.
    """

    e = _vector(electric, "electric")
    b = _vector(magnetic, "magnetic")
    k = _vector(propagation, "propagation")
    length = float(support_length_m)
    if not math.isfinite(length) or length <= 0.0:
        raise MaxwellGeometryError("support_length_m must be positive")
    e2 = _dot(e, e)
    c2b2 = SPEED_OF_LIGHT**2 * _dot(b, b)
    denominator = e2 + c2b2
    if denominator <= 0.0:
        raise MaxwellGeometryError("E and B cannot both vanish")
    ecb = SPEED_OF_LIGHT * _dot(e, b)
    poynting = _cross(e, b)
    k_norm = _norm(k)
    p_norm = _norm(poynting)
    e_norm = math.sqrt(e2)
    cb_norm = math.sqrt(c2b2)
    return {
        "electric": list(e),
        "magnetic": list(b),
        "propagation": list(k),
        "maxwell_action_invariants": {
            "I1_normalized": (c2b2 - e2) / denominator,
            "I2_normalized": ecb / denominator,
            "F_squared_zero_for_null_wave": abs(c2b2 - e2) <= 1.0e-12 * denominator,
            "F_dual_F_zero_for_orthogonal_wave": abs(ecb) <= 1.0e-12 * denominator,
        },
        "geometry": {
            "E_dot_cB_over_energy": ecb / denominator,
            "E_B_cosine": _dot(e, b) / (e_norm * _norm(b)) if e_norm and _norm(b) else None,
            "poynting_vector": list(poynting),
            "poynting_parallel_to_propagation": abs(_dot(poynting, k)) / (p_norm * k_norm) if p_norm and k_norm else None,
            "electric_to_magnetic_energy_ratio": e2 / c2b2 if c2b2 else None,
            "electric_action_fraction": e2 / denominator,
            "magnetic_action_fraction": c2b2 / denominator,
            "B_divergence_constraint": "zero away from magnetic monopoles; closed field lines are a topology constraint",
            "field_lines_are_physical_tubes": False,
        },
        "support": {
            "length_m": length,
            "electric_area_scaling": length**2,
            "magnetic_area_scaling": length**2,
            "volume_scaling": length**3,
            "area_or_volume_ratio_is_lorentz_invariant": False,
        },
    }


def _plane_wave(*, amplitude: float, magnetic_ratio: float, angle_degrees: float) -> dict[str, Any]:
    angle = math.radians(float(angle_degrees))
    electric = (amplitude, 0.0, 0.0)
    magnetic = (magnetic_ratio * amplitude * math.sin(angle) / SPEED_OF_LIGHT, magnetic_ratio * amplitude * math.cos(angle) / SPEED_OF_LIGHT, 0.0)
    return evaluate_geometry(electric=electric, magnetic=magnetic, propagation=(0.0, 0.0, 1.0))


def run_maxwell_geometry_campaign(activation: Mapping[str, Any]) -> dict[str, Any]:
    amplitudes = activation.get("amplitudes", [1.0])
    magnetic_ratios = activation.get("magnetic_ratios", [0.25, 0.5, 1.0, 2.0, 4.0])
    angles = activation.get("angles_degrees", [0.0, 30.0, 60.0, 90.0])
    records: list[dict[str, Any]] = []
    for amplitude in amplitudes:
        for ratio in magnetic_ratios:
            for angle in angles:
                value = _plane_wave(amplitude=float(amplitude), magnetic_ratio=float(ratio), angle_degrees=float(angle))
                records.append({"amplitude": float(amplitude), "magnetic_ratio": float(ratio), "angle_degrees": float(angle), **value})
    alpha_ratios = [record["geometry"]["electric_to_magnetic_energy_ratio"] for record in records]
    return {
        "campaign_id": str(activation.get("campaign_id", "maxwell-eb-geometry")),
        "geometry_version": MAXWELL_EB_GEOMETRY_VERSION,
        "execution_status": "COMPLETE",
        "scope": {
            "action": "-1/4 F_mu_nu F^mu_nu",
            "invariants": ["F_squared", "F_dual_F", "E x H Poynting direction"],
            "field_lines": "topological visualisation only",
            "generation": "target-blind",
        },
        "scan": {"candidate_count": len(records), "amplitudes": list(amplitudes), "magnetic_ratios": list(magnetic_ratios), "angles_degrees": list(angles)},
        "controls": {
            "all_geometries_retained": True,
            "alpha_not_used_during_generation": True,
            "no_fitting": True,
            "no_automatic_ranking": True,
            "no_automatic_selection": True,
            "lorentz_invariant_quantities_used": True,
            "area_volume_ratio_treated_as_non_invariant": True,
        },
        "late_comparison": {
            "performed_after_generation": True,
            "reference_alpha_zero": CODATA_ALPHA_ZERO,
            "electric_to_magnetic_energy_ratios": alpha_ratios,
            "contains_ratio_within_1e-6_of_alpha": any(abs(float(value) - CODATA_ALPHA_ZERO) < 1.0e-6 for value in alpha_ratios),
            "interpretation": "The ratio is continuously adjustable through the amplitude ratio; a numerical coincidence is not a derivation of alpha.",
            "used_for_selection": False,
        },
        "records": records,
        "selection": {"performed": False, "ranking_performed": False, "human_review_required": True},
    }


def write_geometry_report(path: str | Path, report: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination

