"""Pipeline for a controlled linear scalar cosmological perturbation mode."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from physics_lab.models.examples.cosmological_scalar_perturbation_model import COSMO_PERTURBATION_ACTION, COSMO_PERTURBATION_BACKGROUND, COSMO_PERTURBATION_EQUATION, COSMO_PERTURBATION_PIPELINE_REF, CosmologicalScalarPerturbationModel
from physics_lab.registry.theory_candidate import SCHEMA_VERSION, load_theory_candidate, validate_theory_candidate


COSMO_PERTURBATION_PIPELINE_VERSION = COSMO_PERTURBATION_PIPELINE_REF
COSMO_PERTURBATION_CANDIDATE_ID = "cosmological-perturbations"
DEFAULT_COSMO_PERTURBATION_CANDIDATE_PATH = Path(__file__).resolve().parents[3] / "schemas" / "examples" / "theory_candidate_cosmological_perturbations.json"


class CosmologicalPerturbationPipelineError(RuntimeError):
    """Raised when the controlled perturbation baseline cannot close."""


def _require_scope(candidate: Mapping[str, Any]) -> None:
    if candidate["registration"].get("pipeline_ref") != COSMO_PERTURBATION_PIPELINE_REF or candidate["registration"]["selected"]:
        raise CosmologicalPerturbationPipelineError("The perturbation baseline must use its pipeline and remain unselected.")
    authorization = candidate["authorization"]
    if any(authorization[key] not in {"NOT_AUTHORIZED", "NOT_ACTIVATED", "NOT_APPLICABLE"} for key in ("search_status", "finite_bounds", "empirical_comparison")) or authorization["external_data_used"]:
        raise CosmologicalPerturbationPipelineError("Search, bounds, empirical comparison and external data must remain closed.")
    if any(source["kind"] == "EXPERIMENTAL_DATA" for source in candidate["provenance"]["sources"]):
        raise CosmologicalPerturbationPipelineError("Experimental sources are comparison-only.")
    if candidate["action"]["expression"] != COSMO_PERTURBATION_ACTION or candidate["action"]["formulation"] != "LAGRANGIAN":
        raise CosmologicalPerturbationPipelineError("The quadratic scalar perturbation action is required.")
    spacetime = candidate["geometry"]["spacetime"]
    if spacetime.get("dimension") != 4 or spacetime.get("manifold") != "FRW_power_law_perturbation_background":
        raise CosmologicalPerturbationPipelineError("The perturbation baseline requires the declared power-law FRW background.")
    if not any(field.get("id") == "gauge-invariant-scalar-mode" for field in candidate["fields"]):
        raise CosmologicalPerturbationPipelineError("The gauge-invariant scalar mode must be explicitly registered.")


def _input_value(candidate: Mapping[str, Any], parameter_id: str) -> float:
    parameter = next((item for item in candidate["parameters"] if item["id"] == parameter_id), None)
    if parameter is None or parameter["provenance"] != "INPUT" or parameter["status"] != "FREE":
        raise CosmologicalPerturbationPipelineError(f"Parameter {parameter_id!r} must remain a FREE INPUT.")
    value = parameter.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise CosmologicalPerturbationPipelineError(f"Parameter {parameter_id!r} must be finite.")
    return float(value)


def run_cosmological_perturbations_pipeline(candidate: Mapping[str, Any] | None = None, *, candidate_path: str | Path = DEFAULT_COSMO_PERTURBATION_CANDIDATE_PATH) -> dict[str, Any]:
    record = load_theory_candidate(candidate_path) if candidate is None else validate_theory_candidate(candidate)
    _require_scope(record)
    sound_speed = _input_value(record, "sound_speed")
    wave_number = _input_value(record, "wave_number")
    conformal_time = _input_value(record, "conformal_time")
    power_exponent = _input_value(record, "power_exponent")
    try:
        result = CosmologicalScalarPerturbationModel(sound_speed, wave_number, conformal_time, power_exponent).solve()
    except ValueError as exc:
        raise CosmologicalPerturbationPipelineError(str(exc)) from exc
    failures = [name for name, passed in result.checks.items() if not passed]
    if failures:
        raise CosmologicalPerturbationPipelineError("Cosmological perturbation validation failed: " + ", ".join(failures))
    observables = [
        {"name": "effective_background_potential", "value": result.effective_potential, "provenance": "DERIVED", "status": "DERIVED", "formula": "p*(p-1)/eta^2", "dependencies": ["conformal_time", "power_exponent"], "free_dependencies": ["conformal_time", "power_exponent"], "state_label": "power-law FRW background"},
        {"name": "mode_frequency_squared", "value": result.mode_frequency_squared, "provenance": "DERIVED", "status": "DERIVED", "formula": "c_s^2*k^2-z''/z", "dependencies": ["sound_speed", "wave_number", "conformal_time", "power_exponent"], "free_dependencies": ["sound_speed", "wave_number", "conformal_time", "power_exponent"], "state_label": "linear scalar perturbation mode"},
        {"name": "horizon_crossing_ratio", "value": result.horizon_ratio, "provenance": "DERIVED", "status": "DERIVED", "formula": "k*eta/p", "dependencies": ["wave_number", "conformal_time", "power_exponent"], "free_dependencies": ["wave_number", "conformal_time", "power_exponent"], "state_label": "mode versus Hubble scale"},
    ]
    return {
        "pipeline_version": COSMO_PERTURBATION_PIPELINE_VERSION, "schema_version": SCHEMA_VERSION, "candidate_id": record["candidate_id"], "pipeline_status": "COMPLETE",
        "scope": {"candidate_selected": False, "claim_scope": "KNOWN_PHYSICS_LINEAR_SCALAR_COSMOLOGICAL_PERTURBATION", "model_scope": "LINEAR_SINGLE_MODE_ON_POWER_LAW_FLAT_FRW_BACKGROUND", "mode_solution": "LOCAL_COEFFICIENTS_ONLY", "vacuum_and_power_spectrum": "NOT_CLAIMED", "search_status": record["authorization"]["search_status"], "finite_bounds": record["authorization"]["finite_bounds"], "empirical_comparison": record["authorization"]["empirical_comparison"], "external_data_used": False},
        "action": {"formulation": record["action"]["formulation"], "expression": record["action"]["expression"], "background": COSMO_PERTURBATION_BACKGROUND, "mode_equation": COSMO_PERTURBATION_EQUATION, "instantiated": True, "provenance": "KNOWN_PHYSICS_REFERENCE"},
        "derivation": {"background": COSMO_PERTURBATION_BACKGROUND, "mode_equation": COSMO_PERTURBATION_EQUATION, "gauge_invariant_variable": "v_k", "linear_order": True, "vacuum_selection_claimed": False, "power_spectrum_claimed": False},
        "parameters": [{"id": "sound_speed", "name": "c_s", "value": sound_speed, "provenance": "INPUT", "unit": "dimensionless", "dependencies": [], "free": True}, {"id": "wave_number", "name": "k", "value": wave_number, "provenance": "INPUT", "unit": "inverse_length", "dependencies": [], "free": True}, {"id": "conformal_time", "name": "eta", "value": conformal_time, "provenance": "INPUT", "unit": "time", "dependencies": [], "free": True}, {"id": "power_exponent", "name": "p", "value": power_exponent, "provenance": "INPUT", "unit": "dimensionless", "dependencies": [], "free": True}],
        "observables": observables,
        "vacuum": {"selected_state": None, "selection_principle": "NOT_APPLICABLE: classical linear perturbation coefficients only"},
        "quantization": {"scope": "NOT_APPLICABLE", "method": "Classical linear perturbation equation; perturbation quantization, vacuum choice and power spectrum are outside this baseline.", "field_quantization": "NOT_APPLICABLE"},
        "checks": result.checks,
        "validation": {"cosmological_perturbation_check_count": len(result.checks), "cosmological_perturbation_failures": failures, "parameter_free_observable_count": 0, "vacuum_and_power_spectrum": "NOT_CLAIMED", "legacy_validator": "NOT_APPLICABLE_MODEL_SPECIFIC_BASELINE"},
        "controls": {"action_instantiated": True, "known_physics_scope_explicit": True, "quadratic_mode_equation_verified": result.checks["mukhanov_sasaki_mode_equation_verified"], "power_law_background_explicit": True, "linear_scope_explicit": True, "no_vacuum_or_power_spectrum_claim": True, "no_experimental_parameters": True, "external_comparison_not_authorized": record["authorization"]["empirical_comparison"] == "NOT_AUTHORIZED"},
    }


def write_cosmological_perturbations_report(path: str | Path, report: Mapping[str, Any] | None = None, **pipeline_kwargs: Any) -> Path:
    output_path = Path(path)
    payload = report or run_cosmological_perturbations_pipeline(**pipeline_kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


__all__ = ["COSMO_PERTURBATION_CANDIDATE_ID", "COSMO_PERTURBATION_PIPELINE_REF", "COSMO_PERTURBATION_PIPELINE_VERSION", "DEFAULT_COSMO_PERTURBATION_CANDIDATE_PATH", "CosmologicalPerturbationPipelineError", "run_cosmological_perturbations_pipeline", "write_cosmological_perturbations_report"]
