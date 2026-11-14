"""Action-to-observable pipeline for the classical Newtonian gravity baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.newtonian_gravity_model import (
    NEWTONIAN_ACCELERATION,
    NEWTONIAN_ACCELERATION_RATIO,
    NEWTONIAN_ACTION,
    NEWTONIAN_FIELD_EQUATION,
    NEWTONIAN_PIPELINE_REF,
    NEWTONIAN_POINT_SOURCE_SOLUTION,
    NewtonianGravityModel,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


NEWTONIAN_PIPELINE_VERSION = NEWTONIAN_PIPELINE_REF
NEWTONIAN_CANDIDATE_ID = "newtonian-gravity"
DEFAULT_NEWTONIAN_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_newtonian_gravity.json"
)


class NewtonianGravityPipelineError(RuntimeError):
    """Raised when the Newtonian gravity baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != NEWTONIAN_PIPELINE_REF:
        raise NewtonianGravityPipelineError(
            f"Newtonian gravity pipeline requires pipeline_ref={NEWTONIAN_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise NewtonianGravityPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise NewtonianGravityPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise NewtonianGravityPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise NewtonianGravityPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != NEWTONIAN_ACTION:
        raise NewtonianGravityPipelineError("Candidate action does not match the Newtonian gravity baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise NewtonianGravityPipelineError("The baseline requires a Lagrangian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 3 or spacetime.get("manifold") != "R_t x R^3":
        raise NewtonianGravityPipelineError(
            "The baseline requires absolute time and three-dimensional Euclidean space."
        )


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise NewtonianGravityPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise NewtonianGravityPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise NewtonianGravityPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise NewtonianGravityPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _parameter_record(parameter_id: str, symbol: str, value: float, unit: str) -> dict[str, Any]:
    return {
        "name": symbol,
        "value": value,
        "provenance": "INPUT",
        "unit": unit,
        "dependencies": [],
        "formula": None,
        "used_by": ["potential", "acceleration", "potential-ratio", "acceleration-ratio"],
        "free": True,
        "parameter_id": parameter_id,
    }


def run_newtonian_gravity_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_NEWTONIAN_CANDIDATE_PATH,
) -> dict[str, Any]:
    """Run the static spherical Newtonian point-source baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)

    gravitational_constant = _input_value(record, "gravitational_constant")
    source_mass = _input_value(record, "source_mass")
    radius = _input_value(record, "radius")
    reference_radius = _input_value(record, "reference_radius")
    result = NewtonianGravityModel(
        gravitational_constant=gravitational_constant,
        source_mass=source_mass,
        radius=radius,
        reference_radius=reference_radius,
    ).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise NewtonianGravityPipelineError(
            "Newtonian gravity validation failed: " + ", ".join(failures)
        )

    observables = [
        {
            "name": "gravitational_potential",
            "value": result.potential,
            "provenance": "DERIVED",
            "status": "DERIVED",
            "formula": NEWTONIAN_POINT_SOURCE_SOLUTION,
            "symbolic": None,
            "dependencies": ["gravitational_constant", "source_mass", "radius"],
            "free_dependencies": ["gravitational_constant", "source_mass", "radius"],
            "state_label": "point-source potential",
        },
        {
            "name": "acceleration_magnitude",
            "value": result.acceleration_magnitude,
            "provenance": "DERIVED",
            "status": "DERIVED",
            "formula": NEWTONIAN_ACCELERATION,
            "symbolic": None,
            "dependencies": ["gravitational_constant", "source_mass", "radius"],
            "free_dependencies": ["gravitational_constant", "source_mass", "radius"],
            "state_label": "radial attractive acceleration",
        },
        {
            "name": "potential_ratio",
            "value": result.potential_ratio,
            "provenance": "DERIVED",
            "status": "PREDICTION (DERIVED, no free parameters)",
            "formula": "phi(r)/phi(r_ref) = r_ref/r",
            "symbolic": None,
            "dependencies": ["radius", "reference_radius"],
            "free_dependencies": [],
            "state_label": "normalized potential",
        },
        {
            "name": "acceleration_ratio",
            "value": result.acceleration_ratio,
            "provenance": "DERIVED",
            "status": "PREDICTION (DERIVED, no free parameters)",
            "formula": NEWTONIAN_ACCELERATION_RATIO,
            "symbolic": None,
            "dependencies": ["radius", "reference_radius"],
            "free_dependencies": [],
            "state_label": "inverse-square ratio",
        },
    ]

    return {
        "pipeline_version": NEWTONIAN_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_REPRODUCTION",
            "model_scope": "CLASSICAL_STATIC_NEWTONIAN_POINT_SOURCE_FIELD",
            "n_body_dynamics": "OUT_OF_SCOPE",
            "general_relativity": "OUT_OF_SCOPE",
            "cosmology": "OUT_OF_SCOPE",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "field_equation": NEWTONIAN_FIELD_EQUATION,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "field_equation": NEWTONIAN_FIELD_EQUATION,
            "point_source_density": "rho(x) = M*delta^3(x)",
            "point_source_solution": NEWTONIAN_POINT_SOURCE_SOLUTION,
            "acceleration": NEWTONIAN_ACCELERATION,
            "boundary_condition": "phi(r) -> 0 as r -> infinity",
            "normalized_acceleration_ratio": NEWTONIAN_ACCELERATION_RATIO,
        },
        "parameters": [
            _parameter_record("gravitational_constant", "G", gravitational_constant, "length^3/(mass*time^2)"),
            _parameter_record("source_mass", "M", source_mass, "mass"),
            _parameter_record("radius", "r", radius, "length"),
            _parameter_record("reference_radius", "r_ref", reference_radius, "length"),
        ],
        "observables": observables,
        "vacuum": {
            "selected_state": None,
            "selection_principle": "NOT_APPLICABLE: this is a classical static field sector, not a quantum vacuum selection",
        },
        "quantization": {
            "scope": "NOT_APPLICABLE",
            "method": "Classical field theory; quantization is outside this K3 baseline.",
            "field_quantization": "NOT_APPLICABLE",
        },
        "checks": result.checks,
        "validation": {
            "newtonian_check_count": len(result.checks),
            "newtonian_failures": failures,
            "parameter_free_observable_count": sum(
                1 for item in observables if item["free_dependencies"] == []
            ),
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "poisson_equation_verified": result.checks["action_to_poisson_equation_verified"],
            "point_source_solution_verified": result.checks["spherical_point_source_solution_verified"],
            "inverse_square_acceleration_verified": result.checks["inverse_square_acceleration_verified"],
            "parameter_free_observable_generated": True,
            "no_experimental_parameters": True,
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_newtonian_gravity_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic Newtonian gravity pipeline report."""
    output_path = Path(path)
    payload = report or run_newtonian_gravity_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_NEWTONIAN_CANDIDATE_PATH",
    "NEWTONIAN_CANDIDATE_ID",
    "NEWTONIAN_PIPELINE_REF",
    "NEWTONIAN_PIPELINE_VERSION",
    "NewtonianGravityPipelineError",
    "run_newtonian_gravity_pipeline",
    "write_newtonian_gravity_report",
]
