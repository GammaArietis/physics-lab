"""Action-to-observable pipeline for the free quantized Dirac field."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.free_dirac_field_model import (
    DIRAC_ACTION,
    DIRAC_DISPERSION,
    DIRAC_EQUATION,
    DIRAC_MASS_SHELL_RATIO,
    DIRAC_PIPELINE_REF,
    FreeDiracFieldModel,
)
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


DIRAC_PIPELINE_VERSION = DIRAC_PIPELINE_REF
DIRAC_CANDIDATE_ID = "free-dirac-field"
DEFAULT_DIRAC_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_free_dirac_field.json"


class FreeDiracFieldPipelineError(RuntimeError):
    """Raised when the free Dirac baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != DIRAC_PIPELINE_REF:
        raise FreeDiracFieldPipelineError(f"Dirac pipeline requires pipeline_ref={DIRAC_PIPELINE_REF!r}.")
    if candidate["registration"]["selected"]:
        raise FreeDiracFieldPipelineError("The baseline candidate must remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")):
        raise FreeDiracFieldPipelineError("Search, finite bounds and empirical comparison must remain closed.")
    if authorization["external_data_used"]:
        raise FreeDiracFieldPipelineError("External data cannot enter baseline derivation.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise FreeDiracFieldPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != DIRAC_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise FreeDiracFieldPipelineError("The baseline requires the free Dirac Lagrangian.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "R^1,3":
        raise FreeDiracFieldPipelineError("The Dirac baseline requires four-dimensional Minkowski spacetime.")
    if not any(field.get("id") == "dirac-spinor" for field in candidate["fields"]):
        raise FreeDiracFieldPipelineError("The Dirac spinor must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None:
        raise FreeDiracFieldPipelineError(f"Missing parameter {parameter_id!r}.")
    if parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise FreeDiracFieldPipelineError(f"Parameter {parameter_id!r} must remain an explicit FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise FreeDiracFieldPipelineError(f"Parameter {parameter_id!r} must be positive and finite.")
    return float(value)


def run_free_dirac_field_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_DIRAC_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    mass = _input_value(record, "mass")
    momentum = _input_value(record, "momentum")
    result = FreeDiracFieldModel(mass=mass, momentum=momentum).solve()
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise FreeDiracFieldPipelineError("Free Dirac validation failed: " + ", ".join(failures))
    observables = [
        {"name": "positive_energy", "value": result.energy, "provenance": "DERIVED", "status": "DERIVED", "formula": "sqrt(|p|^2+m^2)", "dependencies": ["mass", "momentum"], "free_dependencies": ["mass", "momentum"], "state_label": "particle/antiparticle mode"},
        {"name": "mass_shell_ratio", "value": result.mass_shell_ratio, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": DIRAC_MASS_SHELL_RATIO, "dependencies": ["mass", "momentum"], "free_dependencies": [], "state_label": "Dirac on-shell relation"},
        {"name": "spinor_component_count", "value": 4, "provenance": "DERIVED", "status": "PREDICTION (DERIVED, no free parameters)", "formula": "four-component Dirac spinor", "dependencies": [], "free_dependencies": [], "state_label": "Dirac field"},
    ]
    return {
        "pipeline_version": DIRAC_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_FREE_DIRAC_FIELD_REPRODUCTION", "model_scope": "QUANTIZED_FREE_DIRAC_FIELD_IN_3_PLUS_1_MINKOWSKI_SPACE", "interactions": "OUT_OF_SCOPE", "gauge_fields": "OUT_OF_SCOPE", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "field_equation": DIRAC_EQUATION, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"clifford_algebra": "{gamma^mu,gamma^nu}=2*eta^(mu nu)", "field_equation": DIRAC_EQUATION, "canonical_anticommutator": "{psi_alpha(t,x),psi_beta^dagger(t,y)}=delta_alpha_beta*delta^3(x-y)", "dispersion": DIRAC_DISPERSION, "fock_quantization": "fermionic creation and annihilation operators for particles and antiparticles", "vacuum": "Fock vacuum annihilated by all particle and antiparticle annihilation operators"},
        "parameters": [{"id": "mass", "name": "m", "value": mass, "provenance": "INPUT", "unit": "mass", "dependencies": [], "free": True}, {"id": "momentum", "name": "|p|", "value": momentum, "provenance": "INPUT", "unit": "inverse_length", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": "Fock vacuum", "selection_principle": "annihilation by all fermionic annihilation operators; normal-ordered free Hamiltonian"},
        "quantization": {"scope": "QUANTUM_FIELD", "method": "canonical equal-time anticommutation relations and fermionic Fock expansion", "field_quantization": "VERIFIED"},
        "checks": result.checks,
        "validation": {"dirac_check_count": len(result.checks), "dirac_failures": failures, "parameter_free_observable_count": sum(1 for item in observables if not item["free_dependencies"]), "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "canonical_field_quantization_in_scope": result.checks["canonical_anticommutator_declared"], "fock_vacuum_selected": True, "particle_antiparticle_sector_verified": result.checks["particle_antiparticle_sector_verified"], "dispersion_relation_verified": result.checks["dispersion_relation_verified"], "parameter_free_observable_generated": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_free_dirac_field_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_free_dirac_field_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["DEFAULT_DIRAC_CANDIDATE_PATH", "DIRAC_CANDIDATE_ID", "DIRAC_PIPELINE_REF", "DIRAC_PIPELINE_VERSION", "FreeDiracFieldPipelineError", "run_free_dirac_field_pipeline", "write_free_dirac_field_report"]
