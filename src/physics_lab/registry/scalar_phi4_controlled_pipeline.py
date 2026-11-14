"""Pipeline for the controlled finite-lattice classical scalar phi-four model."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.scalar_phi4_controlled_model import PHI4_ACTION, PHI4_EQUATION, PHI4_FORCE_RATIO, PHI4_PIPELINE_REF, ScalarPhi4ControlledModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


PHI4_PIPELINE_VERSION = PHI4_PIPELINE_REF
PHI4_CANDIDATE_ID = "scalar-phi4-controlled"
DEFAULT_PHI4_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_scalar_phi4_controlled.json"


class ScalarPhi4PipelineError(RuntimeError):
    """Raised when the controlled scalar phi-four baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != PHI4_PIPELINE_REF:
        raise ScalarPhi4PipelineError(f"phi-four pipeline requires pipeline_ref={PHI4_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise ScalarPhi4PipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise ScalarPhi4PipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise ScalarPhi4PipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != PHI4_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise ScalarPhi4PipelineError("The baseline requires the controlled phi-four Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 1 or spacetime.get("manifold") != "R_t x Z_N":
        raise ScalarPhi4PipelineError("The phi-four baseline requires a finite one-dimensional periodic lattice.")
    if not any(field.get("id") == "scalar-phi4-field" for field in candidate["fields"]):
        raise ScalarPhi4PipelineError("The interacting scalar field must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str, *, integer: bool = False) -> float | int:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise ScalarPhi4PipelineError(f"Parameter {parameter_id!r} must remain an explicit FREE INPUT.")
    value = parameter.get("value")
    if integer:
        if isinstance(value, bool) or not isinstance(value, int) or value < 2:
            raise ScalarPhi4PipelineError(f"Parameter {parameter_id!r} must be an integer at least 2.")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ScalarPhi4PipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_scalar_phi4_controlled_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_PHI4_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    mass = float(_input_value(record, "mass"))
    coupling = float(_input_value(record, "coupling"))
    amplitude = float(_input_value(record, "field_amplitude"))
    spacing = float(_input_value(record, "lattice_spacing"))
    sites = int(_input_value(record, "site_count", integer=True))
    result = ScalarPhi4ControlledModel(mass, coupling, amplitude, spacing, sites).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise ScalarPhi4PipelineError("Scalar phi-four validation failed: " + ", ".join(failures))
    observables = [
        {"name": "potential_energy_density", "value": result.potential_density, "provenance": "DERIVED", "status": "DERIVED", "formula": "m^2*phi^2/2+lambda*phi^4/24", "dependencies": ["mass", "coupling", "field_amplitude"], "free_dependencies": ["mass", "coupling", "field_amplitude"], "state_label": "uniform finite-lattice configuration"},
        {"name": "quartic_to_quadratic_force_ratio", "value": result.quartic_to_quadratic_force_ratio, "provenance": "DERIVED", "status": "DERIVED", "formula": PHI4_FORCE_RATIO, "dependencies": ["mass", "coupling", "field_amplitude"], "free_dependencies": ["mass", "coupling", "field_amplitude"], "state_label": "interaction strength"},
        {"name": "finite_lattice_site_count", "value": sites, "provenance": "INPUT", "status": "INPUT", "formula": None, "dependencies": [], "free_dependencies": ["site_count"], "state_label": "declared control size"},
    ]
    return {
        "pipeline_version": PHI4_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_CONTROLLED_PHI4_REPRODUCTION", "model_scope": "CLASSICAL_FINITE_PERIODIC_ONE_DIMENSIONAL_PHI4_LATTICE", "continuum_limit": "NOT_CLAIMED", "renormalization": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "field_equation": PHI4_EQUATION, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"field_equation": PHI4_EQUATION, "periodic_boundary": "phi_(j+N)=phi_j", "quartic_potential": "V(phi)=m^2*phi^2/2+lambda*phi^4/24", "finite_lattice": True, "continuum_limit_claimed": False, "parameter_free_observable": "NONE_REQUIRED: controlled interaction observable retains explicit inputs"},
        "parameters": [{"id": "mass", "name": "m", "value": mass, "provenance": "INPUT", "unit": "mass", "dependencies": [], "free": True}, {"id": "coupling", "name": "lambda", "value": coupling, "provenance": "INPUT", "unit": "dimensionless_lattice_coupling", "dependencies": [], "free": True}, {"id": "field_amplitude", "name": "phi_0", "value": amplitude, "provenance": "INPUT", "unit": "field", "dependencies": [], "free": True}, {"id": "lattice_spacing", "name": "a", "value": spacing, "provenance": "INPUT", "unit": "length", "dependencies": [], "free": True}, {"id": "site_count", "name": "N", "value": sites, "provenance": "INPUT", "unit": "count", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: finite classical interaction control, not a quantum vacuum selection"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical finite-lattice control; quantization and continuum renormalization are outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"phi4_check_count": len(result.checks), "phi4_failures": failures, "parameter_free_observable_count": 0, "continuum_limit": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "finite_lattice_explicit": result.checks["finite_periodic_lattice_verified"], "quartic_interaction_present": result.checks["quartic_interaction_present"], "bounded_potential_verified": result.checks["potential_bounded_below_verified"], "continuum_limit_not_claimed": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_scalar_phi4_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_scalar_phi4_controlled_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_PHI4_CANDIDATE_PATH", "PHI4_CANDIDATE_ID", "PHI4_PIPELINE_REF", "PHI4_PIPELINE_VERSION", "ScalarPhi4PipelineError", "run_scalar_phi4_controlled_pipeline", "write_scalar_phi4_report"]
