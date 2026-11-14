"""Action-to-observable pipeline for the classical Einstein-Hilbert vacuum baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.einstein_hilbert_vacuum_model import (
    EINSTEIN_FIELD_EQUATION,
    EINSTEIN_HILBERT_ACTION,
    EINSTEIN_HILBERT_PIPELINE_REF,
    EINSTEIN_VACUUM_REDUCTION,
    KRETSCHMANN_INVARIANT,
    KRETSCHMANN_RATIO,
    SCHWARZSCHILD_METRIC,
    EinsteinHilbertVacuumModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


EINSTEIN_HILBERT_PIPELINE_VERSION = EINSTEIN_HILBERT_PIPELINE_REF
EINSTEIN_HILBERT_CANDIDATE_ID = "einstein-hilbert-vacuum"
DEFAULT_EINSTEIN_HILBERT_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_einstein_hilbert_vacuum.json"
)


class EinsteinHilbertVacuumPipelineError(RuntimeError):
    """Raised when the Einstein-Hilbert vacuum baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != EINSTEIN_HILBERT_PIPELINE_REF:
        raise EinsteinHilbertVacuumPipelineError(
            f"Einstein-Hilbert pipeline requires pipeline_ref={EINSTEIN_HILBERT_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise EinsteinHilbertVacuumPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise EinsteinHilbertVacuumPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise EinsteinHilbertVacuumPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise EinsteinHilbertVacuumPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != EINSTEIN_HILBERT_ACTION:
        raise EinsteinHilbertVacuumPipelineError(
            "Candidate action does not match the Einstein-Hilbert vacuum baseline."
        )
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise EinsteinHilbertVacuumPipelineError("The baseline requires a Lagrangian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "Schwarzschild exterior r>2GM":
        raise EinsteinHilbertVacuumPipelineError(
            "The baseline requires a four-dimensional Schwarzschild exterior."
        )


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise EinsteinHilbertVacuumPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise EinsteinHilbertVacuumPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise EinsteinHilbertVacuumPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise EinsteinHilbertVacuumPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _parameter_record(parameter_id: str, symbol: str, value: float, unit: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "value": value,
        "provenance": "INPUT",
        "unit": unit,
        "dependencies": [],
        "formula": None,
        "used_by": ["schwarzschild-metric", "kretschmann-invariant", "curvature-ratio"],
        "free": True,
        "parameter_id": parameter_id,
    }


def run_einstein_hilbert_vacuum_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_EINSTEIN_HILBERT_CANDIDATE_PATH,
) -> dict[str, Any]:
    """Run the classical Ricci-flat Schwarzschild exterior baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)

    gravitational_constant = _input_value(record, "gravitational_constant")
    mass_parameter = _input_value(record, "mass_parameter")
    radius = _input_value(record, "radius")
    reference_radius = _input_value(record, "reference_radius")
    result = EinsteinHilbertVacuumModel(
        gravitational_constant=gravitational_constant,
        mass_parameter=mass_parameter,
        radius=radius,
        reference_radius=reference_radius,
    ).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise EinsteinHilbertVacuumPipelineError(
            "Einstein-Hilbert vacuum validation failed: " + ", ".join(failures)
        )

    observables = [
        {
            "name": "schwarzschild_compactness",
            "value": result.compactness,
            "provenance": "DERIVED",
            "status": "DERIVED",
            "formula": "2*G*M/r",
            "symbolic": None,
            "dependencies": ["gravitational_constant", "mass_parameter", "radius"],
            "free_dependencies": ["gravitational_constant", "mass_parameter", "radius"],
            "state_label": "dimensionless compactness",
        },
        {
            "name": "kretschmann_invariant",
            "value": result.kretschmann,
            "provenance": "DERIVED",
            "status": "DERIVED",
            "formula": KRETSCHMANN_INVARIANT,
            "symbolic": None,
            "dependencies": ["gravitational_constant", "mass_parameter", "radius"],
            "free_dependencies": ["gravitational_constant", "mass_parameter", "radius"],
            "state_label": "Schwarzschild exterior curvature",
        },
        {
            "name": "kretschmann_ratio",
            "value": result.kretschmann_ratio,
            "provenance": "DERIVED",
            "status": "PREDICTION (DERIVED, no free parameters)",
            "formula": KRETSCHMANN_RATIO,
            "symbolic": None,
            "dependencies": ["radius", "reference_radius"],
            "free_dependencies": [],
            "state_label": "normalized curvature ratio",
        },
    ]

    return {
        "pipeline_version": EINSTEIN_HILBERT_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "model_scope": "CLASSICAL_EINSTEIN_HILBERT_RICCI_FLAT_SCHWARZSCHILD_EXTERIOR",
            "cosmological_constant": "OUT_OF_SCOPE_AND_SET_TO_ZERO",
            "matter_sources": "OUT_OF_SCOPE",
            "quantization": "OUT_OF_SCOPE",
            "cosmology": "OUT_OF_SCOPE",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "field_equation": EINSTEIN_FIELD_EQUATION,
            "vacuum_reduction": EINSTEIN_VACUUM_REDUCTION,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "metric": SCHWARZSCHILD_METRIC,
            "field_equation": EINSTEIN_FIELD_EQUATION,
            "vacuum_reduction": EINSTEIN_VACUUM_REDUCTION,
            "bianchi_identity": "nabla_mu G^(mu nu) = 0",
            "domain": "r > 2*G*M",
            "boundary_condition": "asymptotically flat as r -> infinity",
            "curvature_invariant": KRETSCHMANN_INVARIANT,
            "curvature_ratio": KRETSCHMANN_RATIO,
        },
        "parameters": [
            _parameter_record("gravitational_constant", "G", gravitational_constant, "length^3/(mass*time^2)"),
            _parameter_record("mass_parameter", "M", mass_parameter, "mass"),
            _parameter_record("radius", "r", radius, "length"),
            _parameter_record("reference_radius", "r_ref", reference_radius, "length"),
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": None,
            "selection_principle": "NOT_APPLICABLE: this is a classical Ricci-flat solution sector, not a quantum vacuum selection",
        },
        "quantization": {
            "scope": "NOT_APPLICABLE",
            "method": "Classical general relativity; quantum gravity is outside this K3 baseline.",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "einstein_hilbert_check_count": len(result.checks),
            "einstein_hilbert_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "vacuum_einstein_equation_verified": result.checks["vacuum_equation_reduction_verified"],
            "schwarzschild_exterior_verified": result.checks["exterior_domain_verified"],
            "ricci_flat_exterior_verified": result.checks["ricci_flat_exterior_verified"],
            "curvature_invariant_verified": result.checks["kretschmann_invariant_verified"],
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_einstein_hilbert_vacuum_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic Einstein-Hilbert vacuum pipeline report."""
    output_path = Path(path)
    payload = report or run_einstein_hilbert_vacuum_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_EINSTEIN_HILBERT_CANDIDATE_PATH",
    "EINSTEIN_HILBERT_CANDIDATE_ID",
    "EINSTEIN_HILBERT_PIPELINE_REF",
    "EINSTEIN_HILBERT_PIPELINE_VERSION",
    "EinsteinHilbertVacuumPipelineError",
    "run_einstein_hilbert_vacuum_pipeline",
    "write_einstein_hilbert_vacuum_report",
]
