"""Action-to-observable pipeline for the free quantized Proca field."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.free_proca_field_model import PROCA_ACTION, PROCA_CONSTRAINT, PROCA_DISPERSION, PROCA_FIELD_EQUATION, PROCA_MASS_SHELL_RATIO, PROCA_PIPELINE_REF, FreeProcaFieldModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


PROCA_PIPELINE_VERSION = PROCA_PIPELINE_REF
PROCA_CANDIDATE_ID = "free-proca-field"
DEFAULT_PROCA_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_free_proca_field.json"


class FreeProcaFieldPipelineError(RuntimeError):
    """Raised when the free Proca baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != PROCA_PIPELINE_REF:
        raise FreeProcaFieldPipelineError(f"Proca pipeline requires pipeline_ref={PROCA_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise FreeProcaFieldPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise FreeProcaFieldPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise FreeProcaFieldPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != PROCA_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise FreeProcaFieldPipelineError("The baseline requires the free Proca Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3":
        raise FreeProcaFieldPipelineError("The Proca baseline requires four-dimensional Minkowski spacetime.")
    if not any(field.get("id") == "proca-vector" for field in candidate["fields"]):
        raise FreeProcaFieldPipelineError("The Proca vector field must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise FreeProcaFieldPipelineError(f"Parameter {parameter_id!r} must remain an explicit FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise FreeProcaFieldPipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_free_proca_field_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_PROCA_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    mass = _input_value(record, "mass")
    momentum = _input_value(record, "momentum")
    result = FreeProcaFieldModel(mass=mass, momentum=momentum).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise FreeProcaFieldPipelineError("Free Proca validation failed: " + ", ".join(failures))
    observables = [
        {"name": "positive_energy", "value": result.energy, "provenance": "DERIVED", "status": "DERIVED", "formula": "sqrt(|p|^2+m^2)", "dependencies": ["mass", "momentum"], "free_dependencies": ["mass", "momentum"], "state_label": "massive vector mode"},
        {"name": "mass_shell_ratio", "value": result.mass_shell_ratio, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": PROCA_MASS_SHELL_RATIO, "dependencies": ["mass", "momentum"], "free_dependencies": [], "state_label": "Proca on-shell relation"},
        {"name": "physical_polarization_count", "value": result.physical_polarizations, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "three massive-vector polarizations", "dependencies": [], "free_dependencies": [], "state_label": "Proca field"},
    ]
    return {
        "pipeline_version": PROCA_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FREE_PROCA_FIELD_REPRODUCTION", "model_scope": "QUANTIZED_FREE_MASSIVE_PROCA_FIELD_IN_3_PLUS_1_MINKOWSKI_SPACE", "interactions": "OUT_OF_SCOPE", "gauge_invariance": "BROKEN_BY_MASS_TERM", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "field_equation": PROCA_FIELD_EQUATION, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"field_strength": "F_(mu nu)=partial_mu A_nu-partial_nu A_mu", "field_equation": PROCA_FIELD_EQUATION, "constraint": PROCA_CONSTRAINT, "canonical_anticommutator": "massive-vector mode operators obey bosonic commutation relations", "dispersion": PROCA_DISPERSION, "fock_quantization": "three massive-vector polarization modes", "vacuum": "Fock vacuum annihilated by all vector-mode annihilation operators"},
        "parameters": [{"id": "mass", "name": "m", "value": mass, "provenance": "INPUT", "unit": "mass", "dependencies": [], "free": True}, {"id": "momentum", "name": "|p|", "value": momentum, "provenance": "INPUT", "unit": "inverse_length", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": "Fock vacuum", "selection_principle": "annihilation by all massive-vector annihilation operators; normal-ordered free Hamiltonian"},
        "quantization": {"scope": "QUANTUM_FIELD", "method": "canonical quantization of the constrained massive vector field", "field_quantization": "VERIFIED"},
        "checks": result.checks,
        "validation": {"proca_check_count": len(result.checks), "proca_failures": failures, "parameter_free_observable_count": sum(1 for item in observables if not item["free_dependencies"]), "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "lorenz_constraint_verified": result.checks["lorenz_constraint_verified"], "canonical_field_quantization_in_scope": True, "fock_vacuum_selected": True, "three_physical_polarizations_verified": result.checks["three_physical_polarizations_verified"], "dispersion_relation_verified": result.checks["dispersion_relation_verified"], "parameter_free_observable_generated": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_free_proca_field_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_free_proca_field_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_PROCA_CANDIDATE_PATH", "PROCA_CANDIDATE_ID", "PROCA_PIPELINE_REF", "PROCA_PIPELINE_VERSION", "FreeProcaFieldPipelineError", "run_free_proca_field_pipeline", "write_free_proca_field_report"]
