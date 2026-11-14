"""Action-to-observable pipeline for the known-physics free scalar field."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.free_scalar_field_model import (
    SCALAR_FIELD_ACTION,
    SCALAR_FIELD_DISPERSION,
    SCALAR_FIELD_HAMILTONIAN_DENSITY,
    SCALAR_FIELD_MODE_HAMILTONIAN,
    SCALAR_FIELD_PIPELINE_REF,
    SCALAR_FIELD_RATIO,
    build_free_scalar_field_model,
)
from physics_lab.registry.theory_candidate import (
    SCHEMA_VERSION,
    load_theory_candidate,
    validate_theory_candidate,
)


SCALAR_FIELD_PIPELINE_VERSION = SCALAR_FIELD_PIPELINE_REF
SCALAR_FIELD_CANDIDATE_ID = "known-physics-free-real-scalar-field"
DEFAULT_SCALAR_FIELD_CANDIDATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "examples"
    / "theory_candidate_free_scalar_field.json"
)


class FreeScalarFieldPipelineError(RuntimeError):
    """Raised when the free scalar field baseline cannot close its pipeline."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != SCALAR_FIELD_PIPELINE_REF:
        raise FreeScalarFieldPipelineError(
            f"Free scalar pipeline requires pipeline_ref={SCALAR_FIELD_PIPELINE_REF!r}."
        )
    if candidate["registration"]["selected"]:
        raise FreeScalarFieldPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(
        authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"}
        for key in ("search_status", "finite_bounds", "empirical_comparison")
    ):
        raise FreeScalarFieldPipelineError(
            "Search, finite bounds and empirical comparison must remain closed."
        )
    if authorization["external_data_used"]:
        raise FreeScalarFieldPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise FreeScalarFieldPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != SCALAR_FIELD_ACTION:
        raise FreeScalarFieldPipelineError("Candidate action does not match the free scalar baseline.")
    if candidate["action"]["formulation"] != "LAGRANGIAN":
        raise FreeScalarFieldPipelineError("The free scalar baseline requires a Lagrangian formulation.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 2 or spacetime.get("signature") != "(-,+)":
        raise FreeScalarFieldPipelineError("Free scalar baseline requires 1+1 Minkowski spacetime.")
    if spacetime.get("manifold") != "R_t x S1_L":
        raise FreeScalarFieldPipelineError("Free scalar baseline requires the periodic cylinder R_t x S1_L.")
    if not any(field.get("id") == "scalar-field" for field in candidate["fields"]):
        raise FreeScalarFieldPipelineError("The real scalar field must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next(
        (item for item in candidate["parameters"] if item["id"] == parameter_id),
        None,
    )
    if parameter is None:
        raise FreeScalarFieldPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise FreeScalarFieldPipelineError(
            f"Parameter {parameter_id!r} must remain an explicit FREE INPUT."
        )
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise FreeScalarFieldPipelineError(f"Parameter {parameter_id!r} must be finite and numeric.")
    if float(value) <= 0:
        raise FreeScalarFieldPipelineError(f"Parameter {parameter_id!r} must be positive.")
    return float(value)


def _quantity_record(quantity: Any) -> dict[str, Any]:
    return {
        "name": quantity.name,
        "value": float(quantity.numeric()),
        "provenance": quantity.provenance.value,
        "status": quantity.status(),
        "formula": quantity.formula,
        "symbolic": None if quantity.symbolic is None else str(quantity.symbolic),
        "dependencies": list(quantity.dependencies),
        "free_dependencies": list(quantity.free_dependencies),
        "assumption": quantity.assumption,
        "state_label": quantity.state_label,
        "notes": list(quantity.notes),
    }


def _parameter_record(parameter: Any) -> dict[str, Any]:
    return {
        "name": parameter.name,
        "value": parameter.value,
        "provenance": parameter.provenance.value,
        "unit": parameter.unit,
        "dependencies": list(parameter.dependencies),
        "formula": parameter.formula,
        "used_by": list(parameter.used_by),
        "free": parameter.is_free(),
    }


def run_free_scalar_field_pipeline(
    candidate: Mapping[str, Any] | None = None,
    *,
    candidate_path: str | Path = DEFAULT_SCALAR_FIELD_CANDIDATE_PATH,
    n_max: int = 4,
) -> dict[str, Any]:
    """Run the complete known-physics free scalar field baseline."""
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    if n_max < 1:
        raise ValueError("n_max must be at least 1")

    mass = _input_value(record, "mass")
    length = _input_value(record, "length")
    hbar = _input_value(record, "hbar")
    model = build_free_scalar_field_model(
        mass=mass,
        length=length,
        hbar=hbar,
        n_max=n_max,
    )
    result = model.solve()
    checks = result.metadata["checks"]
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise FreeScalarFieldPipelineError(
            "Free scalar field validation failed: " + ", ".join(failures)
        )

    ratio_quantities = [
        quantity for quantity in result.quantities
        if quantity.name.startswith("dispersion_ratio[")
        and quantity.provenance.value == "DERIVED"
        and not quantity.free_dependencies
    ]
    if not ratio_quantities:
        raise FreeScalarFieldPipelineError(
            "No parameter-free dispersion-ratio observable was generated."
        )

    return {
        "pipeline_version": SCALAR_FIELD_PIPELINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "candidate_id": record["candidate_id"],
        "pipeline_status": "COMPLETE",
        "scope": {
            "candidate_selected": False,
            "claim_scope": "KNOWN_PHYSICS_FREE_SCALAR_FIELD_REPRODUCTION",
            "spacetime": "1+1 Minkowski cylinder R_t x S1_L",
            "search_status": record["authorization"]["search_status"],
            "finite_bounds": record["authorization"]["finite_bounds"],
            "empirical_comparison": record["authorization"]["empirical_comparison"],
            "external_data_used": False,
        },
        "action": {
            "formulation": record["action"]["formulation"],
            "expression": record["action"]["expression"],
            "hamiltonian_density": SCALAR_FIELD_HAMILTONIAN_DENSITY,
            "mode_hamiltonian": SCALAR_FIELD_MODE_HAMILTONIAN,
            "instantiated": True,
            "provenance": "KNOWN_PHYSICS_REFERENCE",
        },
        "derivation": {
            "euler_lagrange_equation": "(d_t^2 - d_x^2 + mu^2) phi = 0",
            "canonical_momentum": "pi = d_t phi",
            "canonical_commutator": "[phi(t,x), pi(t,y)] = i*hbar*delta(x-y)",
            "mode_expansion": "k_n = 2*pi*n/L, n in Z",
            "dispersion": SCALAR_FIELD_DISPERSION,
            "fock_hamiltonian": SCALAR_FIELD_MODE_HAMILTONIAN,
            "parameter_free_ratio": SCALAR_FIELD_RATIO,
            "normal_ordering": "E_vacuum^normal_ordered = 0; absolute zero-point sum not assigned",
            "n_max": n_max,
            "display_window_is_not_a_search_bound": True,
        },
        "parameters": [_parameter_record(parameter) for parameter in result.parameters],
        "spectrum": [
            {
                "label": state.label,
                "quantum_numbers": dict(state.quantum_numbers),
                "eigenvalue": _quantity_record(state.eigenvalue),
            }
            for state in result.spectrum.states
        ],
        "observables": [_quantity_record(quantity) for quantity in result.quantities],
        "vacuum": result.metadata["vacuum"],
        "quantization": result.metadata["quantization"],
        "checks": checks,
        "validation": {
            "free_scalar_field_check_count": len(checks),
            "free_scalar_field_failures": failures,
            "parameter_free_observable_count": len(ratio_quantities),
            "absolute_zero_point_energy": "NOT_ASSIGNED_FINITE_VALUE",
            "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE",
        },
        "controls": {
            "action_instantiated": True,
            "known_physics_scope_explicit": True,
            "periodic_boundary_condition_explicit": True,
            "canonical_field_quantization_in_scope": checks["canonical_field_commutator_declared"],
            "fock_vacuum_selected": checks["fock_vacuum_is_ground_state"],
            "normal_ordered_vacuum_energy_explicit": checks["normal_ordered_vacuum_energy_verified"],
            "absolute_zero_point_energy_not_claimed_finite": True,
            "parameter_free_observable_generated": bool(ratio_quantities),
            "no_experimental_parameters": not any(
                parameter.provenance.value == "EXPERIMENTAL" for parameter in result.parameters
            ),
            "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED",
        },
    }


def write_free_scalar_field_report(
    path: str | Path,
    report: Mapping[str, Any] | None = None,
    **pipeline_kwargs: Any,
) -> Path:
    """Write a deterministic free scalar field pipeline report."""
    output_path = Path(path)
    payload = report or run_free_scalar_field_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DEFAULT_SCALAR_FIELD_CANDIDATE_PATH",
    "FreeScalarFieldPipelineError",
    "SCALAR_FIELD_CANDIDATE_ID",
    "SCALAR_FIELD_PIPELINE_REF",
    "SCALAR_FIELD_PIPELINE_VERSION",
    "run_free_scalar_field_pipeline",
    "write_free_scalar_field_report",
]
